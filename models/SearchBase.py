import requests
from typing import List
from lib.func import get_logger, save_torrent_to_tempfile

class SearchBase:
    LOGGED_IN = False
    POSTS = []
    TRACKER_NAME = 'dummy'
    TRACKER_LOGIN_URL = None
    _log = None

    def __init__(self, username, password) -> None:
        self.username = username
        self.password = password
        self.POSTS = []
    
        self._session = None

    def get_status(self):
        pass

    @property
    def session(self) -> requests.Session:
        if self._session:
            return self._session

        self._session = requests.Session()
        self.log.debug("%s %s", self.username, self.password)
        if self.TRACKER_LOGIN_URL:
            self.log.debug("Loggin in %s", self.TRACKER_LOGIN_URL)
            payload = {
                "username": self.username,
                "password": self.password,
                'redirect': 'index.php?',
                'sid': '',
                'login': 'Login'
            }
            self._session.post(self.TRACKER_LOGIN_URL, data=payload)

        return self._session

    def search(self) -> List:
        return []

    @property
    def log(self):
        if not self._log:
            self._log = get_logger(self.__class__.__name__)
        return self._log

    def download(self, file_url: str) -> str:
        content = self.session.get(file_url, allow_redirects=True).content
        self.log.info("Downloading file %s with authorization", file_url)
        return save_torrent_to_tempfile(content)