from __future__ import annotations

import difflib
import html
import io
import json
import logging
import os
import re
from typing import Any
from urllib.parse import urlparse

import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)


TYPE, QUERY = range(2)
CATALOG_URL = os.getenv(
    "CATALOG_URL",
    "https://raw.githubusercontent.com/belka-developer/belka-modules/"
    "refs/heads/main/bot_market/asset.json",
)
MAX_RESULTS = 10

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def platform_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Hikka", callback_data="type:hikka"),
                InlineKeyboardButton("ExteriaGram", callback_data="type:exteriagram"),
            ]
        ]
    )


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


def github_file_url(entry: dict[str, Any]) -> str:
    file_url = str(entry.get("file", "")).strip()
    if file_url.startswith(("http://", "https://")):
        return file_url

    listing_url = str(entry.get("ls", "")).strip()
    parsed = urlparse(listing_url)
    parts = parsed.path.strip("/").split("/")
    if parsed.netloc == "github.com" and len(parts) >= 5 and parts[2] == "tree":
        owner, repository, branch = parts[0], parts[1], parts[3]
        directory = "/".join(parts[4:])
        return (
            f"https://raw.githubusercontent.com/{owner}/{repository}/"
            f"{branch}/{directory}/{file_url}"
        )
    return file_url


def parse_catalog(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        entries = payload.get("items", payload.get("modules", []))
    else:
        entries = payload
    if not isinstance(entries, list):
        raise ValueError("Каталог должен содержать массив items")

    result: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("name") and entry.get("file"):
            result.append(entry)
    return result


async def load_catalog() -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(CATALOG_URL)
        response.raise_for_status()
        return parse_catalog(response.json())


def search_catalog(
    entries: list[dict[str, Any]], platform: str, query: str
) -> list[dict[str, Any]]:
    query_text = normalize(query)
    query_words = set(query_text.split())
    scored: list[tuple[float, dict[str, Any]]] = []

    for entry in entries:
        entry_type = normalize(str(entry.get("type", "")))
        if entry_type not in {normalize(platform), "plugin" if platform == "exteriagram" else "module"}:
            continue
        haystack = normalize(
            " ".join(
                str(entry.get(field, ""))
                for field in ("name", "description", "keywords", "type")
            )
        )
        words = set(haystack.split())
        overlap = len(query_words & words)
        similarity = difflib.SequenceMatcher(None, query_text, haystack).ratio()
        if overlap or query_text in haystack:
            scored.append((overlap * 2 + similarity, entry))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [entry for _, entry in scored[:MAX_RESULTS]]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Выберите платформу, для которой ищете модуль или плагин:",
        reply_markup=platform_keyboard(),
    )
    return TYPE


async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    platform = query.data.removeprefix("type:")
    context.user_data["platform"] = platform
    await query.edit_message_text(
        f"Платформа: {platform}\n\nВведите название или примерное описание:"
    )
    return QUERY


async def find_items(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    search_text = update.message.text.strip()
    platform = str(context.user_data.get("platform", ""))
    if not search_text:
        await update.message.reply_text("Введите непустое название или описание.")
        return QUERY

    try:
        entries = await load_catalog()
        results = search_catalog(entries, platform, search_text)
    except (httpx.HTTPError, json.JSONDecodeError, ValueError) as error:
        logger.warning("Не удалось загрузить каталог: %s", error)
        await update.message.reply_text(
            "Не удалось загрузить каталог. Попробуйте повторить поиск позже."
        )
        return ConversationHandler.END

    if not results:
        await update.message.reply_text(
            "Ничего не найдено. Попробуйте изменить запрос или выбрать другое слово."
        )
        return ConversationHandler.END

    context.user_data["results"] = results
    keyboard = [
        [
            InlineKeyboardButton(
                str(item["name"])[:64],
                callback_data=f"get:{index}",
            )
        ]
        for index, item in enumerate(results)
    ]
    await update.message.reply_text(
        f"Найдено: {len(results)}\nВыберите нужный файл:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return ConversationHandler.END


async def send_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        index = int(query.data.removeprefix("get:"))
        item = context.user_data["results"][index]
        file_url = github_file_url(item)
        if not file_url.startswith(("http://", "https://")):
            raise ValueError("У элемента каталога отсутствует корректная ссылка на файл")
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(file_url)
            response.raise_for_status()
        filename = os.path.basename(urlparse(file_url).path) or f"{item['name']}.plugin"
        await query.message.reply_document(
            document=InputFile(io.BytesIO(response.content), filename=filename),
            caption=html.escape(str(item.get("name", "Файл"))),
        )
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as error:
        logger.warning("Не удалось отправить элемент каталога: %s", error)
        await query.message.reply_text(
            "Не удалось скачать файл. Проверьте ссылку в каталоге или повторите поиск позже."
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Ошибка обработки обновления", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "Произошла ошибка при обработке запроса. Попробуйте еще раз."
        )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Поиск отменен.")
    return ConversationHandler.END


def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Укажите токен бота в переменной окружения BOT_TOKEN")

    application = Application.builder().token(token).build()
    conversation = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("search", start)],
        states={
            TYPE: [CallbackQueryHandler(choose_type, pattern=r"^type:")],
            QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, find_items)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conversation)
    application.add_handler(CallbackQueryHandler(send_item, pattern=r"^get:"))
    application.add_error_handler(error_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
