#
#            ███████████  ██████████ █████       █████   ████   █████████  
#            ░███░░░░░███░░███░░░░░█░░███       ░░███   ███░   ███░░░░░███ 
#            ░███    ░███ ░███  █ ░  ░███        ░███  ███    ░███    ░███ 
#            ░██████████  ░██████    ░███        ░███████     ░███████████ 
#            ░███░░░░░███ ░███░░█    ░███        ░███░░███    ░███░░░░░███ 
#            ░███    ░███ ░███ ░   █ ░███      █ ░███ ░░███   ░███    ░███ 
#            ███████████  ██████████ ███████████ █████ ░░████ █████   █████
#            ░░░░░░░░░░░  ░░░░░░░░░░ ░░░░░░░░░░░ ░░░░░   ░░░░ ░░░░░   ░░░░░ 
#                                                                    
#                                                                    
#            ██████   ██████    ███████    ██████████    █████████ 
#            ░██████ ██████   ███░░░░░███  ░███░░░░███  ███░░░░░███
#            ░███░█████░███  ███     ░░███ ░███   ░░███░███    ░░░ 
#            ░███░░███ ░███ ░███      ░███ ░███    ░███░░█████████ 
#            ░███ ░░░  ░███ ░███      ░███ ░███    ░███ ░░░░░░░░███
#            ░███      ░███ ░░███     ███  ░███    ███  ███    ░███
#            █████     █████ ░░░███████░   ██████████  ░░█████████ 
#            ░░░░░     ░░░░░    ░░░░░░░    ░░░░░░░░░░    ░░░░░░░░░  
#       
#                                © Copyright 2026
#
#                             https://t.me/belka_mod
#
#                               ── 𝙱ᥱ᧘κᥲ | 𝙼𝙾𝙳𝚂 ──
#                          meta developer: @psycho_belka
# ---------------------------------------------------------------------------------
# Name: deff
# meta developer: @mqone
# meta нахуй ты код смотришь?
# Commands:
# .deff 
# ---------------------------------------------------------------------------------\

import random
from typing import Dict

from java.util import ArrayList
from base_plugin import BasePlugin, HookResult, HookStrategy
from client_utils import RequestCallback, get_messages_controller, run_on_queue, send_request
from org.telegram.tgnet import TLRPC


__id__ = "deff-men"
__name__ = "Deff Men"
__description__ = "Отправляет голосовые кружки по командам."
__author__ = "@mqone • belka • @belka_spot"
__version__ = "1.0.5"
__icon__ = "icon_belka_prod/0"
__app_version__ = ">=12.5.1"
__sdk_version__ = ">=1.4.3.3"


MEDIA_CHANNEL = "ajskalqpwoe"
COMMANDS: Dict[str, int] = {
    ".deff": 9,
    ".nedox": 10,
    ".mama": 11,
    ".anime": 12,
    ".al": 13,
    ".ros": 14,
    ".miyagi": 15,
    ".lyto": 16,
    ".rep": 17,
    ".anti": 19,
    ".huy": 20,
    ".xaxa": 21,
    ".buster": 22,
}
HELP_COMMAND = ".help"


class DeffMen(BasePlugin):
    def on_plugin_load(self):
        self.add_on_send_message_hook()

    def on_send_message_hook(self, account: int, params) -> HookResult:
        message = getattr(params, "message", None)
        if not isinstance(message, str):
            return HookResult()

        command = message.strip().lower()
        if command == HELP_COMMAND:
            params.message = self._help_text()
            return HookResult(strategy=HookStrategy.MODIFY, params=params)

        message_id = COMMANDS.get(command)
        if message_id is None:
            return HookResult()

        peer = getattr(params, "peer", None)
        if peer is None:
            self.log(f"Deff Men: не найден peer для {command}")
            return HookResult()

        run_on_queue(
            lambda: self._forward_clip(account, peer, message_id, command)
        )
        return HookResult(strategy=HookStrategy.CANCEL)

    @staticmethod
    def _help_text() -> str:
        commands = "\n".join(
            f"{command} — переслать сообщение #{message_id}"
            for command, message_id in COMMANDS.items()
        )
        return f"🎙 Deff Men — доступные команды:\n\n{commands}\n\n.help — показать эту справку"

    def _forward_clip(self, account: int, peer, message_id: int, command: str):
        try:
            resolve = TLRPC.TL_contacts_resolveUsername()
            resolve.username = MEDIA_CHANNEL.lstrip("@")
            send_request(
                resolve,
                RequestCallback(
                    lambda response, error: self._on_channel_resolved(
                        account, peer, message_id, command, response, error
                    )
                ),
                account,
            )
        except Exception as error:
            self.log(f"Deff Men: ошибка поиска канала для {command}: {error}")

    def _on_channel_resolved(
        self, account: int, peer, message_id: int, command: str, response, error
    ):
        if error is not None:
            self.log(f"Deff Men: канал не найден для {command}: {error}")
            return
        try:
            controller = get_messages_controller(account)
            chats = getattr(response, "chats", None)
            if chats is None or chats.size() == 0:
                self.log(f"Deff Men: resolveUsername не вернул канал для {command}")
                return

            chat = chats.get(0)
            chat_id = getattr(chat, "id", None)
            if not isinstance(chat_id, int):
                self.log(f"Deff Men: у канала нет корректного id для {command}")
                return

            request = TLRPC.TL_messages_forwardMessages()
            # getInputPeer expects a dialog id here. Passing response.peer
            # directly produces an invalid/empty InputPeer on some builds.
            request.from_peer = controller.getInputPeer(-chat_id)
            request.to_peer = self._target_input_peer(controller, peer)

            message_ids = ArrayList()
            message_ids.add(message_id)
            request.id = message_ids

            random_ids = ArrayList()
            random_ids.add(random.getrandbits(63))
            request.random_id = random_ids
            request.drop_author = True
            request.flags |= 8
            send_request(
                request,
                RequestCallback(
                    lambda result, send_error: self._forward_result(
                        command, result, send_error
                    )
                ),
                account,
            )
        except Exception as send_error:
            self.log(f"Deff Men: ошибка подготовки пересылки {command}: {send_error}")

    def _forward_result(self, command: str, response, error):
        if error is not None:
            self.log(f"Deff Men: Telegram не переслал {command}: {error}")
        elif response is None:
            self.log(f"Deff Men: Telegram вернул пустой ответ для {command}")

    @staticmethod
    def _target_input_peer(controller, peer):
        if isinstance(peer, int):
            return controller.getInputPeer(peer)
        peer_type = type(peer).__name__
        if peer_type.startswith("TL_inputPeer"):
            return peer
        for name in ("user_id", "chat_id", "channel_id"):
            value = getattr(peer, name, None)
            if isinstance(value, int):
                if name == "channel_id":
                    value = -value
                elif name == "chat_id":
                    value = -value
                return controller.getInputPeer(value)
        raise ValueError(f"неподдерживаемый peer: {peer_type}")
