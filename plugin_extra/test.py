import urllib.request

from android_utils import log
from client_utils import PLUGINS_QUEUE, run_on_queue
from org.telegram.tgnet import TLRPC

MEDAL_LIST_URL = (
    "https://raw.githubusercontent.com/belka-developer/"
    "belka-modules/main/id_medal_user.txt"
)
ID_REFRESH_INTERVAL_MS = 5 * 60 * 1000

CUSTOM_EMOJI_DOCUMENT_ID = 0  # <-- подставишь реальный ID позже

# --- ДИАГНОСТИКА -----------------------------------------------------------
# Впиши сюда ID аккаунта(ов), у которых видишь галочку exteraGram
# (например, официальный канал/аккаунт разработчиков).
# Как узнать ID: открой профиль, в exteraGram обычно можно скопировать ID
# через долгий тап на аватар/имя, либо через любой @userinfobot-подобный сервис.
DEBUG_LOG_USER_IDS = {
    # 123456789,  # <-- сюда ID аккаунта с их галочкой
}


def _describe_emoji_status(status) -> str:
    if status is None:
        return "None"
    try:
        doc_id = getattr(status, "document_id", None)
        until = getattr(status, "until", None)
        return f"class={type(status).__name__} document_id={doc_id} until={until}"
    except Exception as e:
        return f"<error reading emoji_status: {e}>"


def _dump_user_flags(user):
    """Печатает в лог все поля User, которые потенциально отвечают за бейджи."""
    uid = getattr(user, "id", None)
    fields_to_check = [
        "verified",
        "premium",
        "scam",
        "fake",
        "support",
        "bot",
        "bot_verification_icon",  # если есть у ботов - тоже интересно глянуть
        "emoji_status",
        "color",           # PeerColor - иногда тоже часть кастомизации профиля
        "profile_color",
    ]

    parts = []
    for field_name in fields_to_check:
        if not hasattr(user, field_name):
            continue
        value = getattr(user, field_name)
        if field_name == "emoji_status":
            value = _describe_emoji_status(value)
        parts.append(f"{field_name}={value}")

    log(f"[MedalDebug] user_id={uid} class={type(user).__name__} " + " ".join(parts))
# -----------------------------------------------------------------------------

_medal_ids: set = set()


def _refresh_ids():
    global _medal_ids
    try:
        with urllib.request.urlopen(MEDAL_LIST_URL, timeout=10) as resp:
            raw = resp.read().decode("utf-8")

        ids = set()
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                ids.add(int(line))
            except ValueError:
                log(f"[CommunityMedal] пропущена строка в id_medal_user.txt: {line!r}")

        _medal_ids = ids
        log(f"[CommunityMedal] список ID обновлён, всего: {len(_medal_ids)}")
    except Exception as e:
        log(f"[CommunityMedal] не удалось обновить список ID: {e}")
    finally:
        run_on_queue(_refresh_ids, PLUGINS_QUEUE, ID_REFRESH_INTERVAL_MS)


def on_load():
    run_on_queue(_refresh_ids, PLUGINS_QUEUE, 0)


def _make_emoji_status():
    status = TLRPC.TL_emojiStatus()
    status.document_id = CUSTOM_EMOJI_DOCUMENT_ID
    return status


def on_user_deserialized(user):
    user_id = getattr(user, "id", None)

    # Диагностика: если список DEBUG_LOG_USER_IDS пуст — логируем ВСЕХ подряд
    # (шумно, но удобно, если пока не знаешь точный ID). Если список не пуст —
    # логируем только тех, кого явно указал.
    if not DEBUG_LOG_USER_IDS or user_id in DEBUG_LOG_USER_IDS:
        _dump_user_flags(user)

    if user_id is None or user_id not in _medal_ids:
        return

    if not CUSTOM_EMOJI_DOCUMENT_ID:
        return

    try:
        user.emoji_status = _make_emoji_status()
    except Exception as e:
        log(f"[CommunityMedal] не удалось выставить emoji_status: {e}")
