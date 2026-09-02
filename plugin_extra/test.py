from base_plugin import HookResult, HookStrategy

# Здесь вся логика команд. Чтобы добавить новую — просто допиши строку в COMMANDS
# или, если нужна более сложная логика, допиши ветку в on_send_message.
# Пользователям НИЧЕГО обновлять не нужно — loader сам подхватит это в течение
# REFRESH_INTERVAL_MS (по умолчанию 5 минут).

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
    return HookResult(strategy=HookStrategy.MODIFY, params=params)
