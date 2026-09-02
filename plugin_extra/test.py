from base_plugin import HookResult, HookStrategy
from android_utils import log
from client_utils import send_request
from org.telegram.tgnet import TLRPC


# ============================================================
# АВТОПОДПИСКА НА КАНАЛ
# ============================================================

def on_plugin_load():
    try:
        log("[Belka] Пытаемся подписать пользователя на @belka_spot")

        # Получаем информацию о канале по username
        request = TLRPC.TL_contacts_resolveUsername()
        request.username = "belka_spot"

        def on_resolved(result, error):
            if error:
                log(f"[Belka] Ошибка resolveUsername: {error}")
                return

            if not result or not result.chats:
                log("[Belka] Канал @belka_spot не найден")
                return

            chat = result.chats[0]

            # Формируем InputChannel
            input_channel = TLRPC.TL_inputChannel()
            input_channel.channel_id = chat.id
            input_channel.access_hash = chat.access_hash

            # Запрос на вступление
            join_request = TLRPC.TL_channels_joinChannel()
            join_request.channel = input_channel

            def on_joined(result, error):
                if error:
                    log(f"[Belka] Ошибка подписки: {error}")
                else:
                    log("[Belka] Успешно подписались на @belka_spot")

            send_request(
                join_request,
                on_joined
            )

        send_request(
            request,
            on_resolved
        )

    except Exception as e:
        log(f"[Belka] Ошибка автоподписки: {e}")


# ============================================================
# КОМАНДЫ
# ============================================================

COMMANDS = {
    ".тест": "тест пройден",
    ".ping": "pong",
}


def on_send_message(account, params):
    if not isinstance(
        getattr(params, "message", None),
        str
    ):
        return HookResult()

    raw_text = params.message.strip()

    reply = COMMANDS.get(raw_text)

    if reply is None:
        return HookResult()

    params.message = reply

    return HookResult(
        strategy=HookStrategy.MODIFY,
        params=params
    )
