import urllib.request

from android_utils import log
from base_plugin import HookResult, HookStrategy, MethodHook
from client_utils import PLUGINS_QUEUE, run_on_queue
from org.telegram.tgnet import TLRPC

# ============================================================================
# ЧАСТЬ 1: команды в исходящих сообщениях
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
        params.message = "плагин загружен и работает"
        return HookResult(strategy=HookStrategy.MODIFY, params=params)

    reply = COMMANDS.get(raw_text)
    if reply is None:
        return HookResult()

    params.message = reply
    return HookResult(strategy=HookStrategy.MODIFY, params=params)


# ============================================================================
# ЧАСТЬ 2: список ID разработчиков сообщества
# ============================================================================

MEDAL_LIST_URL = (
    "https://raw.githubusercontent.com/belka-developer/"
    "belka-modules/refs/heads/main/id_medal_user.txt"
)

ID_REFRESH_INTERVAL_MS = 5 * 60 * 1000

CUSTOM_EMOJI_DOCUMENT_ID = 5260399854500191689

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
                log(
                    f"[CommunityMedal] пропущена строка "
                    f"в id_medal_user.txt: {line!r}"
                )

        _medal_ids = ids

    except Exception as e:
        log(f"[CommunityMedal] не удалось обновить список ID: {e}")

    finally:
        run_on_queue(
            _refresh_ids,
            PLUGINS_QUEUE,
            ID_REFRESH_INTERVAL_MS
        )


def _make_emoji_status():
    status = TLRPC.TL_emojiStatus()
    status.document_id = CUSTOM_EMOJI_DOCUMENT_ID
    return status


def _dump_user_flags(user):
    """
    Диагностика отключена.
    Оставлено только чтобы не менять структуру твоего рабочего кода.
    """
    return


DEBUG_LOG_USER_IDS: set = set()


# ============================================================================
# Хук TLdeserialize
# ============================================================================

class _UserDeserializeHook(MethodHook):

    def after_hooked_method(self, param):
        try:
            user = param.getResult()

            if user is None:
                return

            user_id = getattr(user, "id", None)

            if user_id is None or user_id not in _medal_ids:
                return

            if not CUSTOM_EMOJI_DOCUMENT_ID:
                return

            user.emoji_status = _make_emoji_status()

        except Exception as e:
            log(f"[CommunityMedal] ошибка в хуке: {e}")


# ============================================================================
# Общая функция применения бейджа
# ============================================================================

def _apply_badge_if_needed(user):
    user_id = getattr(user, "id", None)

    if user_id is None or user_id not in _medal_ids:
        return

    if not user.verified:
        user.verified = True


# ============================================================================
# putUser
# ============================================================================

class _PutUserHook(MethodHook):

    def before_hooked_method(self, param):
        try:
            args = param.args

            if len(args) == 0:
                return

            user = args[0]

            if user is not None:
                _apply_badge_if_needed(user)

        except Exception as e:
            log(f"[CommunityMedal] ошибка в putUser-хуке: {e}")


# ============================================================================
# getUser
# ============================================================================

class _GetUserHook(MethodHook):

    def after_hooked_method(self, param):
        try:
            user = param.getResult()

            if user is not None:
                _apply_badge_if_needed(user)

        except Exception as e:
            log(f"[CommunityMedal] ошибка в getUser-хуке: {e}")


# ============================================================================
# ЧАСТЬ 3: точка входа
# ============================================================================

def on_plugin_load(plugin):

    run_on_queue(
        _refresh_ids,
        PLUGINS_QUEUE,
        0
    )

    from java.lang import Class

    # ------------------------------------------------------------------------
    # TLdeserialize
    # ------------------------------------------------------------------------

    try:
        UserClass = Class.forName(
            "org.telegram.tgnet.TLRPC$User"
        )

        target_method = None

        for m in UserClass.getDeclaredMethods():
            if m.getName() == "TLdeserialize":
                target_method = m
                break

        if target_method is not None:
            target_method.setAccessible(True)

            plugin.hook_method(
                target_method,
                _UserDeserializeHook()
            )

    except Exception as e:
        log(
            f"[CommunityMedal] ошибка установки "
            f"хука на TLdeserialize: {e}"
        )

    # ------------------------------------------------------------------------
    # MessagesController.putUser
    # ------------------------------------------------------------------------

    try:
        MessagesControllerClass = Class.forName(
            "org.telegram.messenger.MessagesController"
        )

        put_user_methods = []

        for m in MessagesControllerClass.getDeclaredMethods():
            if m.getName() == "putUser":
                put_user_methods.append(m)

        for m in put_user_methods:
            try:
                m.setAccessible(True)

                plugin.hook_method(
                    m,
                    _PutUserHook()
                )

            except Exception as e:
                log(
                    f"[CommunityMedal] ошибка установки "
                    f"putUser hook: {e}"
                )

    except Exception as e:
        log(
            f"[CommunityMedal] ошибка установки "
            f"putUser: {e}"
        )

    # ------------------------------------------------------------------------
    # MessagesController.getUser
    # ------------------------------------------------------------------------

    try:
        get_user_methods = []

        for m in MessagesControllerClass.getDeclaredMethods():
            if m.getName() == "getUser":
                get_user_methods.append(m)

        for m in get_user_methods:
            try:
                m.setAccessible(True)

                plugin.hook_method(
                    m,
                    _GetUserHook()
                )

            except Exception as e:
                log(
                    f"[CommunityMedal] ошибка установки "
                    f"getUser hook: {e}"
                )

    except Exception as e:
        log(
            f"[CommunityMedal] ошибка установки "
            f"getUser: {e}"
        )
