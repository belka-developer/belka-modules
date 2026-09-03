import urllib.request

from android_utils import log
from base_plugin import HookResult, HookStrategy, MethodHook
from client_utils import PLUGINS_QUEUE, run_on_queue
from org.telegram.tgnet import TLRPC

# ============================================================================
# ЧАСТЬ 1: команды в исходящих сообщениях (.тест, .ping, .галочка)3
# ============================================================================

COMMANDS = {
    ".тест": "тест пройден",
    ".ping": "pong",
}


def on_send_message(account, params):
    if not isinstance(getattr(params, "message", None), str):
        return HookResult()

    raw_text = params.message.strip()

    if raw_text == ".галочка":
        log("[CommunityMedal] .галочка — test.py загружен и работает")
        params.message = "плагин загружен и работает"
        return HookResult(strategy=HookStrategy.MODIFY, params=params)

    reply = COMMANDS.get(raw_text)
    if reply is None:
        return HookResult()

    params.message = reply
    return HookResult(strategy=HookStrategy.MODIFY, params=params)


# ============================================================================
# ЧАСТЬ 2: список ID разработчиков сообщества (бейдж)
# ============================================================================

MEDAL_LIST_URL = (
    "https://raw.githubusercontent.com/belka-developer/"
    "belka-modules/refs/heads/main/id_medal_user.txt"
)
ID_REFRESH_INTERVAL_MS = 5 * 60 * 1000

CUSTOM_EMOJI_DOCUMENT_ID = 5260399854500191689  # взято из рабочего примера другого плагина

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


def _make_emoji_status():
    status = TLRPC.TL_emojiStatus()
    status.document_id = CUSTOM_EMOJI_DOCUMENT_ID
    return status


def _dump_user_flags(user):
    """Диагностика: печатает интересующие поля User. Включай через DEBUG_LOG_USER_IDS."""
    uid = getattr(user, "id", None)
    fields_to_check = [
        "verified", "premium", "scam", "fake", "support", "bot",
        "emoji_status", "color", "profile_color",
    ]
    parts = []
    for field_name in fields_to_check:
        if not hasattr(user, field_name):
            continue
        value = getattr(user, field_name)
        if field_name == "emoji_status" and value is not None:
            value = f"document_id={getattr(value, 'document_id', None)}"
        parts.append(f"{field_name}={value}")
    log(f"[MedalDebug] user_id={uid} " + " ".join(parts))


DEBUG_LOG_USER_IDS: set = set()  # впиши сюда ID для точечной диагностики, иначе логируются все


class _SanityHook(MethodHook):
    """Проверка, что механизм хука вообще работает. Считает вызовы String.length()."""
    _count = 0

    def after_hooked_method(self, param):
        _SanityHook._count += 1
        if _SanityHook._count in (1, 10, 100):
            log(f"[CommunityMedal] SANITY: String.length() перехвачен, вызовов: {_SanityHook._count}")


class _UserDeserializeHook(MethodHook):
    def before_hooked_method(self, param):
        log("[CommunityMedal] before_hooked_method сработал (TLdeserialize вызван)")

    def after_hooked_method(self, param):
        try:
            log("[CommunityMedal] after_hooked_method сработал")
            user = param.getResult()
            if user is None:
                log("[CommunityMedal] getResult() вернул None")
                return

            user_id = getattr(user, "id", None)

            if not DEBUG_LOG_USER_IDS or user_id in DEBUG_LOG_USER_IDS:
                _dump_user_flags(user)

            if user_id is None or user_id not in _medal_ids:
                return
            if not CUSTOM_EMOJI_DOCUMENT_ID:
                return

            user.emoji_status = _make_emoji_status()
        except Exception as e:
            log(f"[CommunityMedal] ошибка в хуке: {e}")


# ============================================================================
# ЧАСТЬ 3: точка входа — вызывается loader'ом один раз при первой загрузке
# ============================================================================

def on_plugin_load(plugin):
    run_on_queue(_refresh_ids, PLUGINS_QUEUE, 0)

    from java.lang import Class

    # --- диагностика перед установкой боевого хука ---
    try:
        StringClass = Class.forName("java.lang.String")
        log(f"[CommunityMedal] DEBUG StringClass type={type(StringClass)}")
        length_method = StringClass.getDeclaredMethod("length")
        log(f"[CommunityMedal] DEBUG String.getDeclaredMethod('length') OK: {length_method}")

        # Санити-чек самого механизма перехвата: length() вызывается в
        # приложении постоянно, поэтому если хук реально работает - лог
        # заспамит счётчиком в первую же секунду.
        sanity_handle = plugin.hook_method(length_method, _SanityHook())
        log(f"[CommunityMedal] DEBUG sanity-хук на String.length() установлен: handle={sanity_handle}")
    except Exception as e:
        log(f"[CommunityMedal] DEBUG sanity-check на String упал: {e}")

    try:
        UserClass = Class.forName("org.telegram.tgnet.TLRPC$User")
        log(f"[CommunityMedal] DEBUG UserClass={UserClass} type={type(UserClass)}")

        # Не угадываем сигнатуру — ищем метод по имени среди ВСЕХ объявленных
        # методов класса и берём его реальные типы параметров.
        target_method = None
        for m in UserClass.getDeclaredMethods():
            if m.getName() == "TLdeserialize":
                target_method = m
                param_types = [str(t) for t in m.getParameterTypes()]
                log(f"[CommunityMedal] DEBUG найден TLdeserialize, параметры: {param_types}")
                break

        if target_method is None:
            log("[CommunityMedal] TLdeserialize не найден среди объявленных методов TLRPC$User")
        else:
            target_method.setAccessible(True)

            handle = plugin.hook_method(target_method, _UserDeserializeHook())
            if handle:
                log("[CommunityMedal] хук на TLdeserialize установлен")
            else:
                log("[CommunityMedal] не удалось установить хук (handle пустой)")
    except Exception as e:
        log(f"[CommunityMedal] ошибка установки хука: {e}")
