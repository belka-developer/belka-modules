from __future__ import annotations

import hashlib
import logging
import os
import py_compile
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
BOT_FILE = BASE_DIR / "m.py"
REMOTE_BOT_URL = os.getenv(
    "REMOTE_BOT_URL",
    "https://raw.githubusercontent.com/belka-developer/belka-modules/"
    "refs/heads/main/bot_market/m.py",
)
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", "300"))

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("bot-runner")
bot_process: subprocess.Popen[bytes] | None = None


def download_bot() -> bytes:
    cache_buster = str(int(time.time() // UPDATE_INTERVAL))
    url = f"{REMOTE_BOT_URL}?v={cache_buster}"
    request = Request(url, headers={"Cache-Control": "no-cache"})
    with urlopen(request, timeout=30) as response:
        return response.read()


def update_bot() -> bool:
    try:
        remote_code = download_bot()
    except OSError as error:
        logger.warning("Не удалось проверить обновление: %s", error)
        return False

    if BOT_FILE.exists() and hashlib.sha256(remote_code).digest() == hashlib.sha256(
        BOT_FILE.read_bytes()
    ).digest():
        return False

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=".py",
            prefix="bot-update-",
            dir=BASE_DIR,
            delete=False,
        ) as temporary_file:
            temporary_file.write(remote_code)
            temporary_path = Path(temporary_file.name)
        py_compile.compile(str(temporary_path), doraise=True)
        os.replace(temporary_path, BOT_FILE)
        logger.info("Код бота обновлен с GitHub")
        return True
    except (OSError, py_compile.PyCompileError) as error:
        logger.error("Обновление отклонено: %s", error)
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        return False


def stop_bot() -> None:
    global bot_process
    if bot_process is None or bot_process.poll() is not None:
        return
    bot_process.terminate()
    try:
        bot_process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        bot_process.kill()
        bot_process.wait()
    bot_process = None


def start_bot() -> None:
    global bot_process
    bot_process = subprocess.Popen(
        [sys.executable, str(BOT_FILE)],
        cwd=BASE_DIR,
        env=os.environ.copy(),
    )
    logger.info("Бот запущен, PID: %s", bot_process.pid)


def shutdown(_signum: int, _frame: object) -> None:
    del _signum, _frame
    stop_bot()
    raise SystemExit(0)


def main() -> None:
    if not BOT_FILE.exists():
        logger.info("Локальный m.py не найден, загружаю первую версию с GitHub")
        if not update_bot():
            raise FileNotFoundError(
                f"Не найден локальный файл бота и не удалось скачать его с GitHub: {BOT_FILE}"
            )

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    start_bot()
    while True:
        time.sleep(UPDATE_INTERVAL)
        if update_bot():
            stop_bot()
            start_bot()
        elif bot_process is None or bot_process.poll() is not None:
            logger.warning("Бот завершился, перезапускаю")
            start_bot()


if __name__ == "__main__":
    main()
