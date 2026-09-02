from base_plugin import HookResult
from android_utils import log
from client_utils import send_request
from org.telegram.tgnet import TLRPC


def on_plugin_load():
    log("[Belka] on_plugin_load: START")

    try:
        request = TLRPC.TL_contacts_resolveUsername()
        request.username = "belka_spot"

        log("[Belka] Отправляем resolveUsername")

        def on_resolved(result, error):
            log("[Belka] resolveUsername callback")

            if error:
                log(f"[Belka] resolve error: {error}")
                return

            if not result:
                log("[Belka] result == None")
                return

            log(f"[Belka] result: {result}")

            if result.chats is None or result.chats.size() == 0:
                log("[Belka] Канал не найден")
                return

            # Java ArrayList -> берём элемент через get()
            chat = result.chats.get(0)

            log(f"[Belka] Найден канал: id={chat.id}")
            log(f"[Belka] access_hash={chat.access_hash}")

            try:
                input_channel = TLRPC.TL_inputChannel()
                input_channel.channel_id = chat.id
                input_channel.access_hash = chat.access_hash

                log("[Belka] InputChannel создан")

                join_request = TLRPC.TL_channels_joinChannel()
                join_request.channel = input_channel

                log("[Belka] Отправляем joinChannel")

                def on_joined(join_result, join_error):
                    log("[Belka] joinChannel callback")

                    if join_error:
                        log(f"[Belka] join error: {join_error}")
                    else:
                        log("[Belka] УСПЕШНО ВСТУПИЛИ В @belka_spot")

                send_request(
                    join_request,
                    on_joined
                )

            except Exception as e:
                log(f"[Belka] Ошибка создания join request: {e}")

        send_request(
            request,
            on_resolved
        )

    except Exception as e:
        log(f"[Belka] КРИТИЧЕСКАЯ ОШИБКА: {e}")


COMMANDS = {
    ".тест": "тест пройден",
    ".ping": "pong",
}


def on_send_message(account, params):
    if not isinstance(getattr(params, "message", None), str):
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
