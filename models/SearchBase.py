import logging
import requests

class SearchBase:
    SESSION = requests.Session()
    LOGGED_IN = False
    POSTS = []
    TRACKER_NAME = 'dummy'
    _log_updated = False
    _log = logging.getLogger()

    def __init__(self, username, password) -> None:
        pass

    async def search(self) -> bool:
        pass

    @property
    def log(self):
        if not self._log_updated:
            self._log = logging.getLogger(self.__class__.__name__)
            self._log_updated = True
        return self._log
