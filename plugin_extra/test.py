from base_plugin import HookResult
from android_utils import log


def on_plugin_load():
    log("[Belka] ===========================")
    log("[Belka] on_plugin_load ЗАПУЩЕН")
    log("[Belka] ===========================")


def on_send_message(account, params):
    return HookResult()
