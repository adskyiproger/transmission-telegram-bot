import logging
import requests

class SearchBase:
    SESSION = requests.Session()
    LOGGED_IN = False
    POSTS = []
    # UNITS = {'KB': 1024, 'MB': 1048576, 'GB': 1073741824 }
    TRACKER_NAME = 'dummy'
    _log_updated = False
    _log = logging.getLogger()

    def __init__(self) -> None:
        pass

    def search(self):
        pass

    @property
    def log(self):
        if not self._log_updated:
            self._log = logging.getLogger(self.__class__.__name__)
            self._log_updated = True
        return self._log
