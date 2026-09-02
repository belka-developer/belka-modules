import urllib.request

from android_utils import log
from client_utils import PLUGINS_QUEUE, run_on_queue

MEDAL_LIST_URL = (
    "https://raw.githubusercontent.com/belka-developer/"
    "belka-modules/main/id_medal_user.txt"
)
ID_REFRESH_INTERVAL_MS = 5 * 60 * 1000

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
                log(f"[CommunityMedal] пропущена строка в id_medal_user.txt: {line!r}")

        _medal_ids = ids
        log(f"[CommunityMedal] список ID обновлён, всего: {len(_medal_ids)}")
    except Exception as e:
        log(f"[CommunityMedal] не удалось обновить список ID: {e}")
    finally:
        # Сами себя переставляем в очередь — loader в это не вмешивается.
        run_on_queue(_refresh_ids, PLUGINS_QUEUE, ID_REFRESH_INTERVAL_MS)


def on_load():
    """Вызывается loader'ом один раз при первой успешной загрузке этого файла."""
    run_on_queue(_refresh_ids, PLUGINS_QUEUE, 0)


def on_user_deserialized(user):
    """Вызывается loader'ом на каждый десериализованный TLRPC.User."""
    user_id = getattr(user, "id", None)
    if user_id is not None and user_id in _medal_ids:
        user.verified = True
