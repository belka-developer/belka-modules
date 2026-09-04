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
#                                © Copyright 2024
#
#                             https://t.me/belka_mod
#
#                               ── 𝙱ᥱ᧘κᥲ | 𝙼𝙾𝙳𝚂 ──
#                          meta developer: @psycho_belka
import json
import re
import time
from collections import deque
from types import SimpleNamespace
from typing import Any, List, Optional, Tuple

import requests
try:
    from java import jclass
except ImportError:
    jclass = None

from base_plugin import BasePlugin, HookResult, HookStrategy
from ui.settings import Header, Input, Text
from client_utils import send_text, run_on_queue
try:
    from hook_utils import get_private_field
except ImportError:
    get_private_field = None

# Selector и BulletinHelper используются только для пресета моделей —
# делаем импорт "мягким". Если на какой-то версии клиента их нет, плагин
# всё равно должен загрузиться и показать кнопку настроек, просто без
# части preset-функциональности, а не упасть целиком на импорте.
try:
    from ui.settings import Selector
except Exception:
    Selector = None

try:
    from ui.bulletin import BulletinHelper
except Exception:
    BulletinHelper = None


def _notify(kind: str, message: str):
    if BulletinHelper is None:
        return
    try:
        getattr(BulletinHelper, f"show_{kind}")(message)
    except Exception:
        pass

__id__ = "ai-model-belka"
__name__ = "Ai-model-belka"
__description__ = (
    "Команды .он / .оф включают и выключают автоответы нейросети Hugging Face "
    "в текущем чате (с КД между ответами)"
)
__author__ = "belka • @belka_spot"
__version__ = "1.6.3"
__icon__ = "icon_belka_prod/0"
__app_version__ = ">=12.5.1"
__sdk_version__ = ">=1.4.3.3"

DEFAULT_MODEL = ""
DEFAULT_COOLDOWN = 15  # секунд
DEFAULT_MEMORY_SIZE = 10  # сколько последних сообщений юзера помнить в чате
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"

# Готовый пресет моделей: обновляемый автором список "[Название] (org/model)"
# на каждой строке. Парсим его и даём выбрать модель из Selector в настройках,
# не мешая ручному вводу в поле "Модель" выше.
MODEL_PRESET_URL = (
    "https://raw.githubusercontent.com/"
    "belka-developer/belka-modules/"
    "refs/heads/main/"
    "plugin_extra/Ai-model-belka/model-preset.txt"
)
PRESET_LINE_RE = re.compile(r"^\s*\[(?P<name>.+?)\]\s*\((?P<model>.+?)\)\s*$")
PRESET_CACHE_KEY = "model_presets_cache_json"
PRESET_MANUAL_LABEL = "✏️ Своя модель (см. поле «Модель» выше)"

# Готовый пресет "личностей" (системных промптов): JSON-массив
# [{"persona": "Название", "prompt": "текст системного промпта"}, ...]
# по той же схеме, что и пресет моделей — с кэшем и фоновым обновлением.
PERSONA_PRESET_URL = (
    "https://raw.githubusercontent.com/"
    "belka-developer/belka-modules/"
    "refs/heads/main/"
    "plugin_extra/Ai-model-belka/face.json"
)
PERSONA_CACHE_KEY = "persona_presets_cache_json"
PERSONA_MANUAL_LABEL = "✏️ Свой промпт (см. поле «Системный промпт» выше)"

SYSTEM_PROMPT = ""
DEFAULT_LOG_AGGREGATOR_URL = ""

CMD_ON = ".он"
CMD_OFF = ".оф"
CMD_PING = ".ping"
CMD_STATUS = ".status"
CMD_TEST = ".t"
CMD_GPT = ".гпт"
CMD_MEMCLEAR = ".память"
CMD_MODELS = ".модели"
CMD_PERSONAS = ".личности"

# Описание каждой настраиваемой команды для подстраницы "Управление из чата":
# (ключ настройки, слово по умолчанию, заголовок, подсказка).
# Стили оформления ответа нейросети. Значение (первый элемент кортежа) —
# то, что реально хранится в настройке; используется в _apply_style().
# Markdown-синтаксис — тот, что понимает парсер клиента (НЕ обычный
# CommonMark): *bold*, _italic_, __underline__, ~strike~, `mono`,
# ```code```, > quote, **> quote (свёрнутая/expandable).
REPLY_STYLES: List[Tuple[str, str]] = [
    ("none", "Обычный текст (без форматирования)"),
    ("italic", "Курсив"),
    ("bold", "Жирный"),
    ("underline", "Подчёркнутый"),
    ("strike", "Зачёркнутый"),
    ("mono", "Моно (инлайн-код)"),
    ("code", "Блок кода"),
    ("quote", "Цитата"),
    ("quote_collapsed", "Цитата (свёрнутая)"),
    ("spoiler", "Спойлер"),
]

# Куда именно применяется стиль: (ключ настройки, подпись в UI).
# Ключ настройки хранит id стиля (значение из REPLY_STYLES), а Selector
# в UI работает поверх отдельного "*_index"-ключа — та же схема, что и
# у пресетов моделей/личностей выше по файлу.
STYLE_TARGETS: List[Tuple[str, str]] = [
    ("style_autoreply", "Автоответ в чате (.он/.оф)"),
    ("style_test", "Ответ на .t (тестовый запрос)"),
    ("style_gpt", "Ответ на .гпт (чистый запрос)"),
    ("style_custom_trigger", "Ответ на своё триггер-слово"),
]

COMMAND_DEFS = [
    ("cmd_on", CMD_ON, "Включить автоответ", "Слово для включения автоответов нейросети в этом чате"),
    ("cmd_off", CMD_OFF, "Выключить автоответ", "Слово для выключения автоответов нейросети в этом чате"),
    ("cmd_ping", CMD_PING, "Проверка связи", "Слово для диагностики соединения с Hugging Face"),
    ("cmd_status", CMD_STATUS, "Статус / диагностика", "Слово для подробного отчёта о работе плагина"),
    ("cmd_test", CMD_TEST, "Тестовый запрос", "Слово + текст — реальный ответ нейросети без памяти чата. Доступно тебе и разрешённым ID (настройка выше), в любом чате"),
    ("cmd_gpt", CMD_GPT, "Чистый запрос", "Слово + текст — запрос без системного промпта и без памяти чата, ответ чистым сообщением. Доступно тебе и разрешённым ID"),
    ("cmd_memclear", CMD_MEMCLEAR, "Очистить память чата", "Слово для очистки мини-памяти текущего чата"),
    ("cmd_models", CMD_MODELS, "Список моделей", "Слово для показа списка моделей из пресета"),
    ("cmd_personas", CMD_PERSONAS, "Список личностей", "Слово для показа списка личностей из пресета"),
]


class HFAutoResponderPlugin(BasePlugin):
    def on_plugin_load(self):
        # Хук на исходящие сообщения — ловим команды .он / .оф / .ping / .status / .t
        self.add_on_send_message_hook()
        # Хук на входящие апдейты — реагируем на новые сообщения в активных чатах.
        # TL_updateNewMessage — сообщения с медиа/групповые чаты.
        # TL_updateShortMessage — обычные текстовые сообщения в личке (компактная форма).
        # SDK может передавать полное Java-имя TL-класса, поэтому нужен
        # substring-match, а не точное совпадение имени события.
        self.add_hook("TL_update", match_substring=True)
        self.add_hook("TL_updates", match_substring=True)

        # Загружаем список активных чатов из настроек в память
        self._active_chats = self._load_active_chats()
        # peer_id -> unix timestamp последнего ответа
        self._last_reply_at = {}

        # peer_id -> deque последних сообщений юзера (мини-память чата).
        # Новое сообщение добавляется в конец, старое при переполнении
        # само вытесняется (maxlen), т.е. 1,2,3 -> после нового 2,3,4.
        self._chat_history: dict = {}

        # Пресеты моделей: сперва читаем то, что закэшировано локально (чтобы
        # список в настройках был доступен сразу, без сети), затем в фоне
        # пробуем подтянуть свежую версию с MODEL_PRESET_URL. Обёрнуто в
        # try/except, чтобы сбой здесь не ронял загрузку всего плагина
        # (и, как следствие, кнопку настроек).
        try:
            self._model_presets: List[Tuple[str, str]] = self._load_cached_presets()
            self._preset_ui_error: Optional[str] = None
        except Exception as e:
            self._model_presets = []
            self._dlog(f"presets: сбой при чтении кэша на старте: {e}")
        try:
            run_on_queue(lambda: self._refresh_presets(notify=False))
        except Exception as e:
            self._dlog(f"presets: не удалось запланировать обновление: {e}")

        # Пресеты личностей (системных промптов) — та же схема, что и у
        # моделей: кэш сразу, свежая версия в фоне, никакие сбои здесь не
        # должны блокировать загрузку плагина.
        try:
            self._persona_presets: List[Tuple[str, str]] = self._load_cached_personas()
            self._persona_ui_error: Optional[str] = None
        except Exception as e:
            self._persona_presets = []
            self._dlog(f"personas: сбой при чтении кэша на старте: {e}")
        try:
            run_on_queue(lambda: self._refresh_personas(notify=False))
        except Exception as e:
            self._dlog(f"personas: не удалось запланировать обновление: {e}")

        # Диагностика для .status — считаем, что происходит с апдейтами
        self._debug = {
            "hook_calls_total": 0,
            "updates_total": 0,
            "updates_no_text": 0,
            "updates_out_skipped": 0,
            "updates_no_peer": 0,
            "updates_inactive_chat": 0,
            "updates_cooldown_skipped": 0,
            "updates_no_token": 0,
            "updates_dispatched": 0,
            "last_incoming_peer": None,
            "last_incoming_text": None,
            "last_error": None,
            "last_reply_sent": None,
        }

        self._dlog(f"HF Auto-Responder loaded, active chats: {self._active_chats}")

    # ---------- логирование ----------

    def _dlog(self, msg: str):
        try:
            self.log(msg)
        except Exception:
            pass

    # ---------- настраиваемые триггер-слова команд ----------

    def _cmd(self, key: str, default: str) -> str:
        # Возвращает актуальное (настроенное пользователем) слово-команду.
        # Если поле очищено или сбой чтения настройки — тихо откатываемся
        # на слово по умолчанию, чтобы команда не переставала работать.
        try:
            value = self.get_setting(key, default).strip().lower()
        except Exception:
            value = ""
        return value or default.lower()

    def _create_commands_subpage(self) -> List[Any]:
        # Подстраница настроек, открывается по тапу на "Управление из чата".
        # Здесь пользователь может переназначить слово для любой команды —
        # например, сделать .он -> "старт" и т.п.
        items: List[Any] = [
            Header(text="Триггер-слова команд"),
            Text(
                text="Слово для каждой команды можно изменить на своё. Регистр не важен — при сравнении всё приводится к нижнему регистру",
                icon="msg_info",
            ),
        ]
        for key, default, label, subtext in COMMAND_DEFS:
            items.append(
                Input(
                    key=key,
                    text=label,
                    default=default,
                    subtext=f"{subtext}. По умолчанию: {default}",
                    icon="msg_bot",
                )
            )
        items.append(
            Text(
                text="↺ Сбросить к значениям по умолчанию",
                subtext="Вернёт все слова выше к исходным (.он, .оф, .ping и т.д.)",
                icon="msg_retry",
                on_click=self._on_reset_commands_click,
            )
        )
        return items

    def _on_reset_commands_click(self, view):
        try:
            for key, default, _label, _subtext in COMMAND_DEFS:
                self.set_setting(key, default)
            self.set_setting("commands_reset_tick", str(time.time()), reload_settings=True)
            _notify("success", "Слова-команды сброшены к значениям по умолчанию")
        except Exception as e:
            self._dlog(f"commands: сброс не удался: {e}")
            _notify("error", f"Не удалось сбросить: {e}")

    def _preset_settings_items(self) -> List[Any]:
        # Отдельная сборка блока пресетов: если что-то здесь пойдёт не так
        # (Selector недоступен на этой версии клиента, битый кэш и т.п.),
        # весь остальной экран настроек не должен пострадать. Причина
        # отсутствия блока запоминается в self._preset_ui_error, чтобы её
        # можно было посмотреть через .status, не разбирая логи.
        self._preset_ui_error = None

        if Selector is None:
            self._preset_ui_error = (
                "класс Selector недоступен в ui.settings на этой сборке клиента"
            )
            self._dlog(f"presets: блок настроек скрыт — {self._preset_ui_error}")
            return []
        try:
            model_presets = getattr(self, "_model_presets", []) or []
            return [
                Selector(
                    key="preset_model_index",
                    text="Модель из пресета",
                    default=self._current_preset_index(),
                    items=self._preset_selector_items(),
                    icon="msg_folders",
                    on_change=self._on_preset_selected,
                ),
                Text(
                    text="🔄 Обновить список моделей",
                    subtext=f"Загружено моделей: {len(model_presets)}. Список подтягивается с GitHub автора плагина",
                    icon="msg_retry",
                    on_click=self._on_refresh_presets_click,
                ),
            ]
        except Exception as e:
            self._preset_ui_error = f"{type(e).__name__}: {e}"
            self._dlog(f"presets: сбой при построении блока настроек: {e}")
            return []

    def _persona_settings_items(self) -> List[Any]:
        # Та же защитная схема, что и у пресета моделей.
        self._persona_ui_error = None

        if Selector is None:
            self._persona_ui_error = (
                "класс Selector недоступен в ui.settings на этой сборке клиента"
            )
            self._dlog(f"personas: блок настроек скрыт — {self._persona_ui_error}")
            return []
        try:
            personas = getattr(self, "_persona_presets", []) or []
            return [
                Selector(
                    key="persona_preset_index",
                    text="Личность из пресета",
                    default=self._current_persona_index(),
                    items=self._persona_selector_items(),
                    icon="msg_folders",
                    on_change=self._on_persona_selected,
                ),
                Text(
                    text="🔄 Обновить список личностей",
                    subtext=f"Загружено личностей: {len(personas)}. Список подтягивается с GitHub автора плагина",
                    icon="msg_retry",
                    on_click=self._on_refresh_personas_click,
                ),
            ]
        except Exception as e:
            self._persona_ui_error = f"{type(e).__name__}: {e}"
            self._dlog(f"personas: сбой при построении блока настроек: {e}")
            return []

    # ---------- стиль оформления ответов нейросети ----------

    def _style_options_labels(self) -> List[str]:
        return [label for _style_id, label in REPLY_STYLES]

    def _style_id_by_index(self, index: int) -> str:
        if 0 <= index < len(REPLY_STYLES):
            return REPLY_STYLES[index][0]
        return REPLY_STYLES[0][0]

    def _style_index_by_id(self, style_id: str) -> int:
        for i, (sid, _label) in enumerate(REPLY_STYLES):
            if sid == style_id:
                return i
        return 0

    def _get_style(self, target_key: str) -> str:
        # target_key — один из ключей из STYLE_TARGETS, например "style_test".
        try:
            value = self.get_setting(target_key, "none").strip()
        except Exception:
            value = ""
        return value or "none"

    def _current_style_index(self, target_key: str) -> int:
        return self._style_index_by_id(self._get_style(target_key))

    def _make_style_on_change(self, target_key: str, label: str):
        def _on_change(new_index: int):
            style_id = self._style_id_by_index(new_index)
            try:
                self.set_setting(target_key, style_id)
            except Exception as e:
                self._dlog(f"style: не удалось сохранить {target_key}: {e}")
                return
            style_label = REPLY_STYLES[new_index][1] if 0 <= new_index < len(REPLY_STYLES) else style_id
            _notify("success", f"{label}: {style_label}")
        return _on_change

    def _create_cosmetics_subpage(self) -> List[Any]:
        # Подстраница "Косметика", открывается по тапу на одноимённый пункт
        # в главных настройках — та же схема, что и у "Управление из чата".
        items: List[Any] = [
            Header(text="Стиль ответа нейросети"),
            Text(
                text="Как оформить текст ответа перед отправкой в чат — отдельно для каждого триггер-слова",
                icon="msg_info",
            ),
        ]

        if Selector is None:
            items.append(
                Text(
                    text="Недоступно на этой сборке клиента",
                    subtext="Класс Selector отсутствует в ui.settings — выбор стиля показать нельзя",
                    icon="msg_info",
                )
            )
            return items

        try:
            for target_key, label in STYLE_TARGETS:
                items.append(
                    Selector(
                        key=f"{target_key}_index",
                        text=label,
                        default=self._current_style_index(target_key),
                        items=self._style_options_labels(),
                        icon="msg_edit",
                        on_change=self._make_style_on_change(target_key, label),
                    )
                )
        except Exception as e:
            self._dlog(f"style: сбой при построении подстраницы «Косметика»: {e}")
            items.append(
                Text(
                    text="Не удалось построить список стилей",
                    subtext=f"{type(e).__name__}: {e}",
                    icon="msg_info",
                )
            )
        return items

    def _apply_style(self, text: str, style_id: str) -> str:
        # Оборачивает text в markdown-синтаксис клиента под выбранный стиль.
        # "none" (или что-то незнакомое) — текст возвращается как есть,
        # без изменений и без markdown-парсинга при отправке.
        if not text:
            return text

        if style_id == "italic":
            return f"_{text}_"
        if style_id == "bold":
            return f"*{text}*"
        if style_id == "underline":
            return f"__{text}__"
        if style_id == "strike":
            return f"~{text}~"
        if style_id == "spoiler":
            return f"||{text}||"
        if style_id == "mono":
            return f"`{text}`"
        if style_id == "code":
            return f"```\n{text}\n```"
        if style_id == "quote":
            lines = text.split("\n")
            return "\n".join((f"> {line}" if line else ">") for line in lines)
        if style_id == "quote_collapsed":
            return text

        return text

    def _style_send_kwargs(self, style_id: str, text: str = "") -> dict:
        # parse_mode передаём только если реально что-то меняли — иначе
        # ответ модели уходит как раньше, plain-текстом, без риска, что
        # случайные *звёздочки* в ответе нейросети сломают форматирование.
        if style_id == "quote_collapsed" and jclass is not None:
            entity_class = jclass("org.telegram.tgnet.TLRPC$TL_messageEntityBlockquote")
            entity = entity_class()
            entity.offset = 0
            entity.length = len(text.encode("utf-16-le")) // 2
            entity.collapsed = True
            return {"entities": [entity]}
        if style_id and style_id != "none":
            return {"parse_mode": "Markdown"}
        return {}

    def create_settings(self) -> List[Any]:
        items: List[Any] = [
            Header(text="Hugging Face"),
            Input(
                key="hf_token",
                text="API токен",
                default="",
                subtext="Токен доступа Hugging Face (Settings -> Access Tokens)",
                icon="msg_pin_code",
            ),
            Input(
                key="hf_model",
                text="Модель",
                default=DEFAULT_MODEL,
                subtext="Например: meta-llama/Llama-3.1-8B-Instruct:fastest. Можно ввести вручную или выбрать ниже из пресета",
                icon="msg_bot",
            ),
        ]
        items.extend(self._preset_settings_items())
        items.extend([
            Header(text="Поведение"),
            Input(
                key="system_prompt",
                text="Системный промпт",
                default=SYSTEM_PROMPT,
                subtext="Задаёт характер и стиль ответов модели. Можно ввести вручную или выбрать ниже готовую личность из пресета",
                icon="msg_bot",
            ),
        ])
        items.extend(self._persona_settings_items())
        items.extend([
            Input(
                key="cooldown",
                text="КД между ответами (сек)",
                default=str(DEFAULT_COOLDOWN),
                subtext="Минимальное время между ответами в одном чате. 0 — без задержки",
                icon="msg_recent",
            ),
            Input(
                key="memory_size",
                text="Память (сообщений юзера)",
                default=str(DEFAULT_MEMORY_SIZE),
                subtext="Сколько последних сообщений юзера в чате помнит нейросеть. 0 — без памяти",
                icon="msg_saved",
            ),
            Input(
                key="allowed_test_users",
                text="Разрешённые ID для .t",
                default="",
                subtext="Telegram ID через запятую — этим пользователям разрешено вызывать .t где угодно (лично и в группах), не только тебе",
                icon="msg_contacts",
            ),
            Input(
                key="custom_trigger",
                text="Своё триггер-слово",
                default="",
                subtext="Например: !ai — сообщения с этим словом уйдут в нейросеть, а ответ придёт одним чистым сообщением, без эмодзи/времени/модели. Пусто — выключено",
                icon="msg_bot",
            ),
            Input(
                key="log_aggregator_url",
                text="URL агрегатора логов",
                default=DEFAULT_LOG_AGGREGATOR_URL,
                subtext="Например: http://192.168.1.10:8765/log. Оставь пустым, чтобы отключить отправку логов",
                icon="msg_log",
            ),
            Text(
                text="Управление из чата",
                subtext=(
                    f"{self._cmd('cmd_on', CMD_ON)} / {self._cmd('cmd_off', CMD_OFF)} — вкл/выкл автоответ. "
                    f"{self._cmd('cmd_test', CMD_TEST)} / {self._cmd('cmd_gpt', CMD_GPT)} <текст> — прямой запрос нейросети. "
                    "Нажми, чтобы посмотреть все команды и настроить свои слова"
                ),
                icon="msg_info",
                create_sub_fragment=self._create_commands_subpage,
            ),
            Text(
                text="🎨 Косметика",
                subtext="Оформление ответа нейросети (курсив, жирный, цитата и т.д.) — отдельно для каждого триггер-слова",
                icon="menu_feature_stories",
                create_sub_fragment=self._create_cosmetics_subpage,
            ),
        ])
        return items

    # ---------- пресеты моделей ----------

    def _load_cached_presets(self) -> List[Tuple[str, str]]:
        raw = self.get_setting(PRESET_CACHE_KEY, "").strip()
        if not raw:
            return []
        try:
            data = json.loads(raw)
            return [(str(name), str(model)) for name, model in data]
        except Exception as e:
            self._dlog(f"presets: не удалось прочитать кэш: {e}")
            return []

    def _save_cached_presets(self, presets: List[Tuple[str, str]]):
        try:
            self.set_setting(PRESET_CACHE_KEY, json.dumps(presets, ensure_ascii=False))
        except Exception as e:
            self._dlog(f"presets: не удалось сохранить кэш: {e}")

    def _parse_presets(self, text: str) -> List[Tuple[str, str]]:
        presets = []
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = PRESET_LINE_RE.match(line)
            if not match:
                continue
            name = match.group("name").strip()
            model = match.group("model").strip()
            if name and model:
                presets.append((name, model))
        return presets

    def _fetch_presets(self) -> List[Tuple[str, str]]:
        response = requests.get(MODEL_PRESET_URL, timeout=15)
        response.raise_for_status()
        return self._parse_presets(response.text)

    def _refresh_presets(self, notify: bool):
        try:
            fresh = self._fetch_presets()
        except Exception as e:
            self._dlog(f"presets: обновление списка не удалось: {e}")
            if notify:
                _notify("error", f"Не удалось обновить список моделей: {e}")
            return

        if not fresh:
            self._dlog("presets: список по ссылке пуст или не распознан")
            if notify:
                _notify("error", "Список моделей пуст или имеет неверный формат")
            return

        changed = fresh != self._model_presets
        self._model_presets = fresh
        self._save_cached_presets(fresh)

        if notify:
            _notify("success", f"Список моделей обновлён: {len(fresh)} шт.")

        if changed or notify:
            # Пересобираем экран настроек, чтобы Selector показал новый список.
            try:
                self.set_setting(
                    "preset_last_refresh", str(time.time()), reload_settings=True
                )
            except Exception as e:
                self._dlog(f"presets: reload_settings не удалось: {e}")

    def _preset_selector_items(self) -> List[str]:
        return [PRESET_MANUAL_LABEL] + [name for name, _ in self._model_presets]

    def _current_preset_index(self) -> int:
        current_model = self.get_setting("hf_model", DEFAULT_MODEL).strip()
        for i, (_, model) in enumerate(self._model_presets):
            if model == current_model:
                return i + 1
        return 0

    def _on_preset_selected(self, new_index: int):
        if new_index == 0:
            # Пользователь явно выбрал "своя модель" — очищаем поле
            # ручного ввода, чтобы не оставалась модель из предыдущего
            # выбора пресета.
            self.set_setting("hf_model", "", reload_settings=True)
            _notify("info", "Поле «Модель» очищено — введите модель вручную")
            return

        if new_index < 0 or new_index > len(self._model_presets):
            return

        name, model = self._model_presets[new_index - 1]
        self.set_setting("hf_model", model, reload_settings=True)
        _notify("success", f"Модель установлена: {name}")

    def _build_models_report(self) -> str:
        current_model = self.get_setting("hf_model", DEFAULT_MODEL).strip() or DEFAULT_MODEL

        if not self._model_presets:
            return (
                "📋 .модели\n"
                "Пресет ещё не загружен. Открой настройки плагина и нажми "
                "«🔄 Обновить список моделей», либо подожди — плагин пробует "
                "подтянуть его в фоне при запуске."
            )

        lines = [f"📋 .модели — доступно {len(self._model_presets)} из пресета:", ""]
        for name, model in self._model_presets:
            marker = "✅" if model == current_model else "•"
            lines.append(f"{marker} {name} — `{model}`")
        lines.append("")
        lines.append(f"Текущая модель: {current_model}")
        lines.append("Выбрать другую — в настройках плагина, пункт «Модель из пресета».")
        return "\n".join(lines)

    def _on_refresh_presets_click(self, view):
        _notify("info", "Обновляю список моделей...")
        run_on_queue(lambda: self._refresh_presets(notify=True))

    # ---------- пресеты личностей (системных промптов) ----------

    def _load_cached_personas(self) -> List[Tuple[str, str]]:
        raw = self.get_setting(PERSONA_CACHE_KEY, "").strip()
        if not raw:
            return []
        try:
            data = json.loads(raw)
            return [(str(name), str(prompt)) for name, prompt in data]
        except Exception as e:
            self._dlog(f"personas: не удалось прочитать кэш: {e}")
            return []

    def _save_cached_personas(self, personas: List[Tuple[str, str]]):
        try:
            self.set_setting(PERSONA_CACHE_KEY, json.dumps(personas, ensure_ascii=False))
        except Exception as e:
            self._dlog(f"personas: не удалось сохранить кэш: {e}")

    def _parse_personas(self, text: str) -> List[Tuple[str, str]]:
        # Ожидаемый формат: [{"persona": "Название", "prompt": "текст"}, ...]
        data = json.loads(text)
        personas = []
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("persona", "")).strip()
                prompt = str(item.get("prompt", "")).strip()
                if name and prompt:
                    personas.append((name, prompt))
        return personas

    def _fetch_personas(self) -> List[Tuple[str, str]]:
        response = requests.get(PERSONA_PRESET_URL, timeout=15)
        response.raise_for_status()
        return self._parse_personas(response.text)

    def _refresh_personas(self, notify: bool):
        try:
            fresh = self._fetch_personas()
        except Exception as e:
            self._dlog(f"personas: обновление списка не удалось: {e}")
            if notify:
                _notify("error", f"Не удалось обновить список личностей: {e}")
            return

        if not fresh:
            self._dlog("personas: список по ссылке пуст или не распознан")
            if notify:
                _notify("error", "Список личностей пуст или имеет неверный формат")
            return

        changed = fresh != getattr(self, "_persona_presets", [])
        self._persona_presets = fresh
        self._save_cached_personas(fresh)

        if notify:
            _notify("success", f"Список личностей обновлён: {len(fresh)} шт.")

        if changed or notify:
            try:
                self.set_setting(
                    "persona_last_refresh", str(time.time()), reload_settings=True
                )
            except Exception as e:
                self._dlog(f"personas: reload_settings не удалось: {e}")

    def _persona_selector_items(self) -> List[str]:
        personas = getattr(self, "_persona_presets", []) or []
        return [PERSONA_MANUAL_LABEL] + [name for name, _ in personas]

    def _current_persona_index(self) -> int:
        current_prompt = self.get_setting("system_prompt", SYSTEM_PROMPT).strip()
        personas = getattr(self, "_persona_presets", []) or []
        for i, (_, prompt) in enumerate(personas):
            if prompt.strip() == current_prompt:
                return i + 1
        return 0

    def _on_persona_selected(self, new_index: int):
        personas = getattr(self, "_persona_presets", []) or []

        if new_index == 0:
            # Пользователь явно выбрал "свой промпт" — очищаем поле
            # системного промпта, чтобы не оставался текст от предыдущей
            # выбранной личности.
            self.set_setting("system_prompt", "", reload_settings=True)
            _notify("info", "Поле «Системный промпт» очищено — введите текст вручную")
            return

        if new_index < 0 or new_index > len(personas):
            return

        name, prompt = personas[new_index - 1]
        self.set_setting("system_prompt", prompt, reload_settings=True)
        _notify("success", f"Личность установлена: {name}")

    def _build_personas_report(self) -> str:
        current_prompt = self.get_setting("system_prompt", SYSTEM_PROMPT).strip() or SYSTEM_PROMPT
        personas = getattr(self, "_persona_presets", []) or []

        if not personas:
            return (
                "🎭 .личности\n"
                "Пресет ещё не загружен. Открой настройки плагина и нажми "
                "«🔄 Обновить список личностей», либо подожди — плагин пробует "
                "подтянуть его в фоне при запуске."
            )

        lines = [f"🎭 .личности — доступно {len(personas)} из пресета:", ""]
        for name, prompt in personas:
            marker = "✅" if prompt.strip() == current_prompt else "•"
            lines.append(f"{marker} {name}")
        lines.append("")
        lines.append("Выбрать другую — в настройках плагина, пункт «Личность из пресета».")
        return "\n".join(lines)

    def _on_refresh_personas_click(self, view):
        _notify("info", "Обновляю список личностей...")
        run_on_queue(lambda: self._refresh_personas(notify=True))

    # ---------- команды .он / .оф ----------

    def on_send_message_hook(self, account: int, params: Any) -> HookResult:
        if not isinstance(getattr(params, "message", None), str):
            return HookResult()

        original_text = params.message.strip()
        raw_text = original_text.lower()

        cmd_on = self._cmd("cmd_on", CMD_ON)
        cmd_off = self._cmd("cmd_off", CMD_OFF)
        cmd_ping = self._cmd("cmd_ping", CMD_PING)
        cmd_status = self._cmd("cmd_status", CMD_STATUS)
        cmd_test = self._cmd("cmd_test", CMD_TEST)
        cmd_gpt = self._cmd("cmd_gpt", CMD_GPT)
        cmd_memclear = self._cmd("cmd_memclear", CMD_MEMCLEAR)
        cmd_models = self._cmd("cmd_models", CMD_MODELS)
        cmd_personas = self._cmd("cmd_personas", CMD_PERSONAS)

        is_exact_cmd = raw_text in (cmd_on, cmd_off, cmd_ping, cmd_status, cmd_memclear, cmd_models, cmd_personas)
        is_test_cmd = raw_text == cmd_test or raw_text.startswith(cmd_test + " ")
        is_gpt_cmd = raw_text == cmd_gpt or raw_text.startswith(cmd_gpt + " ")

        custom_trigger = self._get_custom_trigger()
        is_custom_cmd = bool(custom_trigger) and (
            raw_text == custom_trigger or raw_text.startswith(custom_trigger + " ")
        )

        if not is_exact_cmd and not is_test_cmd and not is_gpt_cmd and not is_custom_cmd:
            return HookResult()

        dialog_id = getattr(params, "peer", None)
        if dialog_id is None:
            return HookResult()

        if raw_text == cmd_on:
            self._active_chats.add(dialog_id)
            params.message = "✅ Автоответы включены в этом чате"
            self._save_active_chats()
            return HookResult(strategy=HookStrategy.MODIFY, params=params)

        if raw_text == cmd_off:
            self._active_chats.discard(dialog_id)
            params.message = "🛑 Автоответы выключены в этом чате"
            self._save_active_chats()
            return HookResult(strategy=HookStrategy.MODIFY, params=params)

        if raw_text == cmd_status:
            params.message = self._build_status_report(dialog_id)
            return HookResult(strategy=HookStrategy.MODIFY, params=params)

        if raw_text == cmd_memclear:
            self._chat_history.pop(dialog_id, None)
            params.message = "🧹 Память этого чата очищена"
            return HookResult(strategy=HookStrategy.MODIFY, params=params)

        if raw_text == cmd_models:
            params.message = self._build_models_report()
            return HookResult(strategy=HookStrategy.MODIFY, params=params)

        if raw_text == cmd_personas:
            params.message = self._build_personas_report()
            return HookResult(strategy=HookStrategy.MODIFY, params=params)

        if is_test_cmd:
            prompt = original_text[len(cmd_test):].strip()
            if not prompt:
                prompt = "Привет! Ответь одним коротким предложением."

            params.message = "🔄 Жду ответ от нейросети..."

            token = self.get_setting("hf_token", "").strip()
            model = self.get_setting("hf_model", DEFAULT_MODEL).strip() or DEFAULT_MODEL

            run_on_queue(lambda: self._handle_test(dialog_id, prompt, token, model))

            return HookResult(strategy=HookStrategy.MODIFY, params=params)

        if is_gpt_cmd:
            prompt = original_text[len(cmd_gpt):].strip()
            if not prompt:
                # Без текста после команды запрашивать нечего.
                return HookResult()

            params.message = "🔄 ..."

            token = self.get_setting("hf_token", "").strip()
            model = self.get_setting("hf_model", DEFAULT_MODEL).strip() or DEFAULT_MODEL

            run_on_queue(lambda: self._handle_gpt(dialog_id, prompt, token, model))

            return HookResult(strategy=HookStrategy.MODIFY, params=params)

        if is_custom_cmd:
            prompt = original_text[len(custom_trigger):].strip()
            if not prompt:
                # Без текста после триггера запрашивать нечего — просто
                # молча возвращаем исходное сообщение как есть.
                return HookResult()

            params.message = "🔄 ..."

            token = self.get_setting("hf_token", "").strip()
            model = self.get_setting("hf_model", DEFAULT_MODEL).strip() or DEFAULT_MODEL

            run_on_queue(lambda: self._handle_custom(dialog_id, prompt, token, model))

            return HookResult(strategy=HookStrategy.MODIFY, params=params)

        if raw_text == cmd_ping:
            # Не отправляем это сообщение как есть, а подменяем его на
            # статус "проверяю" и запускаем диагностику в фоне, чтобы не
            # блокировать поток отправки сообщений.
            params.message = "🔄 Проверяю связь с Hugging Face..."

            token = self.get_setting("hf_token", "").strip()
            model = self.get_setting("hf_model", DEFAULT_MODEL).strip() or DEFAULT_MODEL

            run_on_queue(lambda: self._handle_ping(dialog_id, token, model))

            return HookResult(strategy=HookStrategy.MODIFY, params=params)

        # На всякий случай (например, если два триггер-слова случайно
        # совпали) — молча ничего не делаем, вместо угадывания команды.
        return HookResult()

    # ---------- .ping: диагностика соединения с HF ----------

    def _handle_ping(self, dialog_id: int, token: str, model: str):
        report = self._diagnose_hf(token, model)
        try:
            send_text(dialog_id, report)
        except Exception as e:
            self._dlog(f"ping: send_text failed: {e}")

    # ---------- .t: реальный запрос к нейросети ----------

    def _handle_test(self, dialog_id: int, prompt: str, token: str, model: str, reply_to_id=None):
        if not token:
            try:
                send_text(dialog_id, "❌ .t: токен HF не задан в настройках плагина", replyToMsg=reply_to_id)
            except Exception as e:
                self._dlog(f".t: send_text failed: {e}")
            return

        started = time.time()
        try:
            reply = self._query_hf(prompt, token, model)
        except Exception as e:
            self._debug["last_error"] = f".t _query_hf: {e}"
            try:
                send_text(dialog_id, f"❌ .t: ошибка запроса к нейросети: {e}", replyToMsg=reply_to_id)
            except Exception as e2:
                self._dlog(f".t: send_text failed: {e2}")
            return

        elapsed = time.time() - started

        if not reply:
            try:
                send_text(dialog_id, f"⚠️ .t: нейросеть вернула пустой ответ ({elapsed:.1f}с)", replyToMsg=reply_to_id)
            except Exception as e:
                self._dlog(f".t: send_text failed: {e}")
            return

        try:
            style_id = self._get_style("style_test")
            styled_reply = self._apply_style(reply, style_id)
            if style_id in ("quote", "quote_collapsed"):
                message = f"{styled_reply}\n\n({elapsed:.1f}с, модель: {model})"
            else:
                message = f"🤖 {styled_reply}\n\n({elapsed:.1f}с, модель: {model})"
            send_text(
                dialog_id,
                message,
                replyToMsg=reply_to_id,
                **self._style_send_kwargs(style_id, styled_reply),
            )
            self._debug["last_reply_sent"] = reply[:100]
        except Exception as e:
            self._dlog(f".t: send_text failed: {e}")

    # ---------- своё триггер-слово: чистый ответ нейросети без обвязки ----------

    def _handle_custom(self, dialog_id: int, prompt: str, token: str, model: str, reply_to_id=None):
        if not token:
            self._debug["last_error"] = "custom_trigger: токен HF не задан"
            self._dlog("custom_trigger: HF token is not set, skipping")
            return

        # В отличие от .t — своё триггер-слово помнит контекст чата (мини-память).
        history = list(self._get_history(dialog_id))

        try:
            reply = self._query_hf(prompt, token, model, history=history)
        except Exception as e:
            self._debug["last_error"] = f"custom_trigger _query_hf: {e}"
            self._dlog(f"custom_trigger: HF request failed: {e}")
            return

        if not reply:
            self._debug["last_error"] = "custom_trigger: пустой ответ от модели"
            return

        # Запоминаем сообщение только после удачного ответа, как и в автоответе.
        self._remember(dialog_id, prompt)

        # В отличие от .t — только сам ответ модели, без эмодзи/времени/модели.
        try:
            style_id = self._get_style("style_custom_trigger")
            styled_reply = self._apply_style(reply, style_id)
            send_text(dialog_id, styled_reply, replyToMsg=reply_to_id, **self._style_send_kwargs(style_id, styled_reply))
            self._debug["last_reply_sent"] = reply[:100]
        except Exception as e:
            self._debug["last_error"] = f"custom_trigger send_text: {e}"
            self._dlog(f"custom_trigger: send_text failed: {e}")

    # ---------- .гпт: запрос без системного промпта, с памятью, чистый ответ ----------

    def _handle_gpt(self, dialog_id: int, prompt: str, token: str, model: str, reply_to_id=None):
        if not token:
            self._debug["last_error"] = "gpt: токен HF не задан"
            self._dlog("gpt: HF token is not set, skipping")
            return

        # В отличие от своего триггер-слова — .гпт без памяти чата,
        # только запрос без системного/мастер-промпта.
        try:
            reply = self._query_hf(prompt, token, model, use_system_prompt=False)
        except Exception as e:
            self._debug["last_error"] = f"gpt _query_hf: {e}"
            self._dlog(f"gpt: HF request failed: {e}")
            return

        if not reply:
            self._debug["last_error"] = "gpt: пустой ответ от модели"
            return

        # Ответ приходит так же, как и у своего триггер-слова — чистым
        # сообщением, без эмодзи/времени/названия модели.
        try:
            style_id = self._get_style("style_gpt")
            styled_reply = self._apply_style(reply, style_id)
            send_text(dialog_id, styled_reply, replyToMsg=reply_to_id, **self._style_send_kwargs(style_id, styled_reply))
            self._debug["last_reply_sent"] = reply[:100]
        except Exception as e:
            self._debug["last_error"] = f"gpt: send_text failed: {e}"
            self._dlog(f"gpt: send_text failed: {e}")

    def _diagnose_hf(self, token: str, model: str) -> str:
        if not token:
            return "❌ .ping: токен HF не задан в настройках плагина"

        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 8,
        }

        started = time.time()
        try:
            response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=15)
        except requests.exceptions.Timeout:
            return (
                f"❌ .ping: таймаут запроса к модели '{model}' (>15с)\n"
                "Запрос уходит, но ответа от сервера нет вовремя."
            )
        except requests.exceptions.ConnectionError as e:
            return (
                f"❌ .ping: не удалось установить соединение с {HF_API_URL}\n"
                f"Запрос не уходит. Ошибка: {e}"
            )
        except Exception as e:
            return f"❌ .ping: непредвиденная ошибка при отправке запроса: {e}"

        elapsed = time.time() - started

        status = response.status_code

        if status == 401:
            return "❌ .ping: HTTP 401 — токен HF недействителен или отозван"
        if status == 403:
            return "❌ .ping: HTTP 403 — доступ запрещён (проверь права токена)"
        if status == 404:
            return f"❌ .ping: HTTP 404 — модель '{model}' не найдена"
        if status == 400:
            snippet = response.text[:200] if response.text else ""
            return f"❌ .ping: HTTP 400 — модель '{model}' не поддерживается или неверный запрос\n{snippet}"
        if status == 503:
            return (
                f"⏳ .ping: HTTP 503 — модель '{model}' загружается, "
                "попробуй ещё раз через минуту"
            )
        if status == 429:
            return "❌ .ping: HTTP 429 — превышен лимит запросов к HF API"

        if status != 200:
            snippet = response.text[:200] if response.text else ""
            return f"❌ .ping: HTTP {status} за {elapsed:.1f}с\n{snippet}"

        try:
            data = response.json()
        except Exception:
            return (
                f"⚠️ .ping: HTTP 200 за {elapsed:.1f}с, но ответ не в формате JSON\n"
                f"Сырой ответ: {response.text[:200]}"
            )

        if isinstance(data, dict) and "error" in data:
            return f"⚠️ .ping: HTTP 200, но сервер вернул ошибку: {data['error']}"

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            content = None

        if content:
            return f"✅ .ping: связь с моделью '{model}' работает, ответ получен за {elapsed:.1f}с"

        return (
            f"⚠️ .ping: HTTP 200 за {elapsed:.1f}с, но формат ответа неожиданный\n"
            f"Ответ: {str(data)[:200]}"
        )

    def _build_status_report(self, current_dialog_id) -> str:
        d = self._debug
        is_active = current_dialog_id in self._active_chats
        token_set = bool(self.get_setting("hf_token", "").strip())
        mem_size = self._get_memory_size()
        mem_used = len(self._chat_history.get(current_dialog_id, []))

        lines = [
            f"📊 .status",
            f"Этот чат активен: {'да' if is_active else 'нет'}",
            f"Всего активных чатов: {len(self._active_chats)}",
            f"Токен задан: {'да' if token_set else 'нет'}",
            f"Память этого чата: {mem_used}/{mem_size}",
            "",
            f"on_update_hook вызван всего раз: {d.get('hook_calls_total', 0)}",
            f"Апдейтов (short+new) обработано: {d['updates_total']}",
            f"— пропущено (свои сообщения): {d['updates_out_skipped']}",
            f"— пропущено (нет текста): {d['updates_no_text']}",
            f"— пропущено (не определён peer): {d['updates_no_peer']}",
            f"— пропущено (чат не активен): {d['updates_inactive_chat']}",
            f"— пропущено (кулдаун): {d['updates_cooldown_skipped']}",
            f"— пропущено (нет токена): {d['updates_no_token']}",
            f"— отправлено в обработку: {d['updates_dispatched']}",
            "",
            f"Последний входящий peer: {d['last_incoming_peer']}",
            f"Последний входящий текст: {d['last_incoming_text']}",
            f"Последний отправленный ответ: {d['last_reply_sent']}",
            f"Последняя ошибка: {d['last_error']}",
            "",
            f"Пресет: Selector доступен: {'да' if Selector is not None else 'нет'}",
            f"Пресет: моделей загружено: {len(getattr(self, '_model_presets', []) or [])}",
            f"Пресет: ошибка блока настроек: {getattr(self, '_preset_ui_error', None) or 'нет'}",
            "",
            f"Личности: личностей загружено: {len(getattr(self, '_persona_presets', []) or [])}",
            f"Личности: ошибка блока настроек: {getattr(self, '_persona_ui_error', None) or 'нет'}",
        ]
        return "\n".join(lines)

    # ---------- автоответ на новые сообщения ----------

    def on_update_hook(self, update_name: str, account: int, update: Any) -> HookResult:
        result = HookResult()

        # Безусловный лог КАЖДОГО апдейта, чтобы проверить в логах плагина,
        # вызывается ли этот хук вообще на данной версии клиента/SDK.
        self._debug["hook_calls_total"] = self._debug.get("hook_calls_total", 0) + 1
        self._dlog(f"HF Auto-Responder: on_update_hook called, update_name={update_name}")

        try:
            # Приватные текстовые сообщения без медиа в MTProto приходят в
            # компактной форме TL_updateShortMessage — там текст/user_id/out/id
            # лежат прямо на update, а не внутри update.message.
            if "TL_updateShortMessage" in update_name:
                return self._handle_short_message(update)

            if "TL_updateShortChatMessage" in update_name:
                return self._handle_short_chat_message(update)

            # Сообщения с медиа, обычные (не супер-) групповые чаты и т.д.
            # приходят как TL_updateNewMessage, где всё завёрнуто в update.message.
            if "TL_updateNewMessage" in update_name:
                return self._handle_new_message(getattr(update, "message", None))

            # Супергруппы и каналы шлют отдельный тип апдейта — та же структура
            # (update.message), просто другое имя TL-объекта.
            if "TL_updateNewChannelMessage" in update_name:
                return self._handle_new_message(getattr(update, "message", None))

            return result
        except Exception as e:
            self._debug["last_error"] = f"on_update_hook: {e}"
            self._dlog(f"HF Auto-Responder: on_update_hook error: {e}")
            return result

    def on_updates_hook(self, container_name: str, account: int, updates: Any) -> HookResult:
        """
        На части версий клиента/SDK TL_updateShortMessage (и иногда
        TL_updateNewMessage) прилетают не в on_update_hook, а сюда — при этом
        `updates` это сам объект апдейта, а не настоящий контейнер со списком.
        Обрабатываем оба варианта: и "ложный контейнер" (сам апдейт), и
        настоящий TL_updates/TL_updatesCombined со списком вложенных апдейтов.
        """
        result = HookResult()

        self._debug["hook_calls_total"] = self._debug.get("hook_calls_total", 0) + 1
        self._dlog(f"HF Auto-Responder: on_updates_hook called, container_name={container_name}")

        try:
            if "TL_updateShortMessage" in container_name:
                return self._handle_short_message(updates)

            if "TL_updateShortChatMessage" in container_name:
                return self._handle_short_chat_message(updates)

            if "TL_updateNewMessage" in container_name:
                return self._handle_new_message(getattr(updates, "message", None))

            if "TL_updateNewChannelMessage" in container_name:
                return self._handle_new_message(getattr(updates, "message", None))

            inner = self._get_update_field(updates, "updates")
            if inner is None:
                # Some SDK builds pass the collection itself as `updates`
                # instead of wrapping it in TL_updates.updates.
                inner = updates
                self._dlog(
                    f"updates field fallback: type={type(updates).__name__}, "
                    f"repr={str(updates)[:200]}"
                )

            for item in self._iter_updates(inner):
                self._handle_update_object(item)

            return result
        except Exception as e:
            self._debug["last_error"] = f"on_updates_hook: {e}"
            self._dlog(f"HF Auto-Responder: on_updates_hook error: {e}")
            return result

    def _iter_updates(self, updates: Any):
        # SDK versions expose TL_updates.updates either as a Java list or
        # as a regular Python iterable.
        try:
            count = int(updates.size())
        except (AttributeError, TypeError, ValueError):
            count = None

        if count is not None:
            for idx in range(count):
                yield updates.get(idx)
            return

        try:
            yield from updates
        except TypeError:
            return

    def _get_update_field(self, obj: Any, name: str):
        try:
            value = getattr(obj, name, None)
        except Exception:
            value = None
        if value is not None:
            return value
        if get_private_field is not None:
            try:
                return get_private_field(obj, name)
            except Exception:
                pass
        return None

    def _handle_update_object(self, update: Any):
        update_type = type(update).__name__
        if update_type in ("str", "bytes", "int", "NoneType"):
            return
        self._dlog(f"nested update received: type={update_type}")
        if "TL_updateNewChannelMessage" in update_type:
            self._handle_new_message(self._get_update_field(update, "message"))
        elif "TL_updateNewMessage" in update_type:
            self._handle_new_message(self._get_update_field(update, "message"))
        elif "TL_updateShortMessage" in update_type:
            self._handle_short_message(update)
        elif "TL_updateShortChatMessage" in update_type:
            self._handle_short_chat_message(update)

    def _handle_short_chat_message(self, update: Any) -> HookResult:
        # Telegram uses this compact update for ordinary group chats.
        chat_id = self._get_update_field(update, "chat_id")
        text = self._get_update_field(update, "message")
        if chat_id is None or not isinstance(text, str):
            self._dlog(
                f"short chat update missing fields: "
                f"chat_id={chat_id}, text_type={type(text).__name__}"
            )
            return HookResult()

        peer = SimpleNamespace(chat_id=chat_id)
        sender_id = self._get_update_field(update, "from_id")
        if not isinstance(sender_id, int):
            sender_id = getattr(sender_id, "user_id", None)
        message = SimpleNamespace(
            message=text,
            peer_id=peer,
            from_id=SimpleNamespace(user_id=sender_id),
            id=self._get_update_field(update, "id"),
            out=self._get_update_field(update, "out") or False,
        )
        return self._handle_new_message(message)

    def _handle_short_message(self, update: Any) -> HookResult:
        result = HookResult()
        self._debug["updates_total"] += 1

        if getattr(update, "out", False):
            self._debug["updates_out_skipped"] += 1
            return result

        text = getattr(update, "message", None)
        if not isinstance(text, str) or not text.strip():
            self._debug["updates_no_text"] += 1
            return result

        peer_dialog_id = getattr(update, "user_id", None)
        self._debug["last_incoming_peer"] = peer_dialog_id
        self._debug["last_incoming_text"] = text[:100]

        if peer_dialog_id is None:
            self._debug["updates_no_peer"] += 1
            return result

        reply_to_id = getattr(update, "id", None)

        # В личных сообщениях (TL_updateShortMessage) отправитель — это и
        # есть peer_dialog_id (собеседник в этом чате).
        raw_text = text.strip().lower()
        cmd_test = self._cmd("cmd_test", CMD_TEST)
        cmd_gpt = self._cmd("cmd_gpt", CMD_GPT)
        is_test_cmd = raw_text == cmd_test or raw_text.startswith(cmd_test + " ")
        if is_test_cmd and peer_dialog_id in self._get_allowed_test_users():
            prompt = text.strip()[len(cmd_test):].strip()
            if not prompt:
                prompt = "Привет! Ответь одним коротким предложением."

            token = self.get_setting("hf_token", "").strip()
            model = self.get_setting("hf_model", DEFAULT_MODEL).strip() or DEFAULT_MODEL
            run_on_queue(
                lambda: self._handle_test(peer_dialog_id, prompt, token, model, reply_to_id)
            )
            return result

        is_gpt_cmd = raw_text == cmd_gpt or raw_text.startswith(cmd_gpt + " ")
        if is_gpt_cmd and peer_dialog_id in self._get_allowed_test_users():
            prompt = text.strip()[len(cmd_gpt):].strip()
            if prompt:
                token = self.get_setting("hf_token", "").strip()
                model = self.get_setting("hf_model", DEFAULT_MODEL).strip() or DEFAULT_MODEL
                run_on_queue(
                    lambda: self._handle_gpt(peer_dialog_id, prompt, token, model, reply_to_id)
                )
            return result

        custom_trigger = self._get_custom_trigger()
        is_custom_cmd = bool(custom_trigger) and (
            raw_text == custom_trigger or raw_text.startswith(custom_trigger + " ")
        )
        if is_custom_cmd and peer_dialog_id in self._get_allowed_test_users():
            prompt = text.strip()[len(custom_trigger):].strip()
            if prompt:
                token = self.get_setting("hf_token", "").strip()
                model = self.get_setting("hf_model", DEFAULT_MODEL).strip() or DEFAULT_MODEL
                run_on_queue(
                    lambda: self._handle_custom(peer_dialog_id, prompt, token, model, reply_to_id)
                )
            return result

        return self._dispatch_if_active(peer_dialog_id, text, reply_to_id)

    def _handle_new_message(self, message: Any) -> HookResult:
        result = HookResult()

        if message is None:
            self._debug["updates_no_text"] += 1
            return result

        self._debug["updates_total"] += 1

        # Свои же сообщения (в т.ч. подтверждения .он/.оф и ответы плагина) пропускаем
        if getattr(message, "out", False):
            self._debug["updates_out_skipped"] += 1
            return result

        text = getattr(message, "message", None)
        if not isinstance(text, str) or not text.strip():
            self._debug["updates_no_text"] += 1
            return result

        peer = getattr(message, "peer_id", None)
        peer_dialog_id = self._extract_peer_id(peer)
        self._debug["last_incoming_peer"] = peer_dialog_id
        self._debug["last_incoming_text"] = text[:100]

        if peer_dialog_id is None:
            self._debug["updates_no_peer"] += 1
            return result

        reply_to_id = getattr(message, "id", None)

        # .t от разрешённых пользователей (не только от владельца аккаунта,
        # который вызывает .t через on_send_message_hook как своё исходящее
        # сообщение) — работает и в группах, и в личных сообщениях.
        raw_text = text.strip().lower()
        cmd_test = self._cmd("cmd_test", CMD_TEST)
        cmd_gpt = self._cmd("cmd_gpt", CMD_GPT)
        is_test_cmd = raw_text == cmd_test or raw_text.startswith(cmd_test + " ")
        if is_test_cmd:
            from_id = getattr(message, "from_id", None)
            sender_id = self._extract_sender_id(from_id, peer)
            if sender_id is None and not self._is_group_peer(peer):
                # В личных сообщениях from_id иногда отсутствует —
                # тогда отправитель это собеседник, т.е. сам peer.
                sender_id = getattr(peer, "user_id", None)
            allowed = self._get_allowed_test_users()
            if sender_id is not None and sender_id in allowed:
                prompt = text.strip()[len(cmd_test):].strip()
                if not prompt:
                    prompt = "Привет! Ответь одним коротким предложением."

                token = self.get_setting("hf_token", "").strip()
                model = self.get_setting("hf_model", DEFAULT_MODEL).strip() or DEFAULT_MODEL
                run_on_queue(
                    lambda: self._handle_test(peer_dialog_id, prompt, token, model, reply_to_id)
                )
                return result

        is_gpt_cmd = raw_text == cmd_gpt or raw_text.startswith(cmd_gpt + " ")
        if is_gpt_cmd:
            from_id = getattr(message, "from_id", None)
            sender_id = self._extract_sender_id(from_id, peer)
            if sender_id is None and not self._is_group_peer(peer):
                sender_id = getattr(peer, "user_id", None)
            allowed = self._get_allowed_test_users()
            if sender_id is not None and sender_id in allowed:
                prompt = text.strip()[len(cmd_gpt):].strip()
                if prompt:
                    token = self.get_setting("hf_token", "").strip()
                    model = self.get_setting("hf_model", DEFAULT_MODEL).strip() or DEFAULT_MODEL
                    run_on_queue(
                        lambda: self._handle_gpt(peer_dialog_id, prompt, token, model, reply_to_id)
                    )
                return result

        custom_trigger = self._get_custom_trigger()
        is_custom_cmd = bool(custom_trigger) and (
            raw_text == custom_trigger or raw_text.startswith(custom_trigger + " ")
        )
        if is_custom_cmd:
            from_id = getattr(message, "from_id", None)
            sender_id = self._extract_sender_id(from_id, peer)
            if sender_id is None and not self._is_group_peer(peer):
                sender_id = getattr(peer, "user_id", None)
            allowed = self._get_allowed_test_users()
            if sender_id is not None and sender_id in allowed:
                prompt = text.strip()[len(custom_trigger):].strip()
                if prompt:
                    token = self.get_setting("hf_token", "").strip()
                    model = self.get_setting("hf_model", DEFAULT_MODEL).strip() or DEFAULT_MODEL
                    run_on_queue(
                        lambda: self._handle_custom(peer_dialog_id, prompt, token, model, reply_to_id)
                    )
                return result

        return self._dispatch_if_active(peer_dialog_id, text, reply_to_id)

    def _dispatch_if_active(self, peer_dialog_id: int, text: str, reply_to_id) -> HookResult:
        result = HookResult()

        if peer_dialog_id not in self._active_chats:
            self._debug["updates_inactive_chat"] += 1
            return result

        if not self._check_cooldown(peer_dialog_id):
            self._debug["updates_cooldown_skipped"] += 1
            return result

        token = self.get_setting("hf_token", "").strip()
        if not token:
            self._debug["updates_no_token"] += 1
            self._dlog("HF token is not set, skipping")
            return result

        model = self.get_setting("hf_model", DEFAULT_MODEL).strip() or DEFAULT_MODEL

        self._debug["updates_dispatched"] += 1

        run_on_queue(
            lambda: self._handle_message(peer_dialog_id, text, token, model, reply_to_id)
        )

        return result

    # ---------- helpers ----------

    def _load_active_chats(self) -> set:
        raw = self.get_setting("active_chats", "").strip()
        chats = set()
        for chunk in raw.split(","):
            chunk = chunk.strip()
            if not chunk:
                continue
            try:
                chats.add(int(chunk))
            except ValueError:
                continue
        return chats

    def _save_active_chats(self):
        self.set_setting("active_chats", ",".join(str(c) for c in self._active_chats))

    def _extract_peer_id(self, peer: Any) -> Optional[int]:
        if peer is None:
            return None
        user_id = getattr(peer, "user_id", None)
        if user_id:
            return user_id
        chat_id = getattr(peer, "chat_id", None)
        if chat_id:
            return -chat_id
        channel_id = getattr(peer, "channel_id", None)
        if channel_id:
            return -(1000000000000 + channel_id)
        return None

    def _is_group_peer(self, peer: Any) -> bool:
        if peer is None:
            return False
        return bool(getattr(peer, "chat_id", None)) or bool(getattr(peer, "channel_id", None))

    def _extract_sender_id(self, from_id: Any, peer: Any) -> Optional[int]:
        # В старом формате Message.from_id может быть самим числовым ID,
        # а в новом — объектом PeerUser с полем user_id.
        if isinstance(from_id, int):
            return from_id
        sender_id = getattr(from_id, "user_id", None) if from_id is not None else None
        if sender_id is not None:
            return sender_id
        if from_id is None and not self._is_group_peer(peer):
            return getattr(peer, "user_id", None)
        return None

    def _get_allowed_test_users(self) -> set:
        raw = self.get_setting("allowed_test_users", "").strip()
        if not raw:
            return set()
        ids = set()
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                ids.add(int(part))
            except ValueError:
                continue
        return ids

    def _get_custom_trigger(self) -> str:
        # Пользовательское триггер-слово из настроек, в нижнем регистре,
        # без пробелов по краям. Пусто — фича выключена.
        return self.get_setting("custom_trigger", "").strip().lower()

    def _get_memory_size(self) -> int:
        try:
            size = int(self.get_setting("memory_size", str(DEFAULT_MEMORY_SIZE)))
        except (TypeError, ValueError):
            size = DEFAULT_MEMORY_SIZE
        return max(0, size)

    def _get_history(self, peer_dialog_id: int) -> deque:
        maxlen = self._get_memory_size() or 1
        history = self._chat_history.get(peer_dialog_id)
        if history is None or history.maxlen != maxlen:
            # Пересоздаём deque, если лимит памяти поменяли в настройках,
            # перенося то, что влезет, в новый лимит.
            history = deque(history or [], maxlen=maxlen)
            self._chat_history[peer_dialog_id] = history
        return history

    def _remember(self, peer_dialog_id: int, text: str):
        if self._get_memory_size() <= 0:
            return
        # deque(maxlen=N) сам вытесняет самый старый элемент при добавлении
        # нового сверх лимита — то самое "1,2,3 -> после нового 2,3,4".
        self._get_history(peer_dialog_id).append(text)

    def _check_cooldown(self, peer_dialog_id: int) -> bool:
        try:
            cooldown = float(self.get_setting("cooldown", str(DEFAULT_COOLDOWN)))
        except (TypeError, ValueError):
            cooldown = DEFAULT_COOLDOWN
        if cooldown < 0:
            cooldown = 0

        now = time.time()
        last = self._last_reply_at.get(peer_dialog_id, 0)

        if now - last < cooldown:
            return False

        self._last_reply_at[peer_dialog_id] = now
        return True

    def _handle_message(self, peer_dialog_id: int, text: str, token: str, model: str, reply_to_id):
        history = list(self._get_history(peer_dialog_id))

        try:
            reply = self._query_hf(text, token, model, history=history)
        except Exception as e:
            self._debug["last_error"] = f"_query_hf: {e}"
            self._dlog(f"HF request failed: {e}")
            return

        if not reply:
            self._debug["last_error"] = "_query_hf: пустой ответ от модели"
            return

        # Запоминаем сообщение юзера только после удачного ответа нейросети —
        # так неудачные/пустые запросы не засоряют память.
        self._remember(peer_dialog_id, text)

        try:
            style_id = self._get_style("style_autoreply")
            styled_reply = self._apply_style(reply, style_id)
            send_text(peer_dialog_id, styled_reply, replyToMsg=reply_to_id, **self._style_send_kwargs(style_id, styled_reply))
            self._debug["last_reply_sent"] = reply[:100]
        except Exception as e:
            self._debug["last_error"] = f"send_text: {e}"
            self._dlog(f"send_text failed: {e}")

    def _query_hf(
        self,
        text: str,
        token: str,
        model: str,
        history: Optional[List[str]] = None,
        use_system_prompt: bool = True,
    ) -> str:
        headers = {"Authorization": f"Bearer {token}"}

        messages = []
        if use_system_prompt:
            system_prompt = self.get_setting("system_prompt", SYSTEM_PROMPT).strip() or SYSTEM_PROMPT
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
        # Мини-память: прошлые сообщения юзера идут перед текущим, все с
        # ролью "user" (ответы бота мы не храним) — модель видит контекст
        # последних N сообщений собеседника перед тем, как ответить на новое.
        for old_text in (history or []):
            messages.append({"role": "user", "content": old_text})
        messages.append({"role": "user", "content": text})

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 256,
        }

        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict) and "error" in data:
            self._dlog(f"HF error: {data['error']}")
            return ""

        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError):
            self._dlog(f"HF: неожиданный формат ответа: {data}")
            return ""