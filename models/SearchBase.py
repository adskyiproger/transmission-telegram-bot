import requests
from urllib.parse import quote
from typing import List, Any, Dict
from bs4 import BeautifulSoup

from lib.func import get_logger, save_torrent_to_tempfile
from models.BotConfigurator import BotConfigurator

bot_config = BotConfigurator()


class SearchBase:
    LOGGED_IN: bool = False
    LOGIN_NEEDED: bool = False
    TRACKER_LOGIN_FIELDS: Dict[str, Any] = {
        "username": "username",
        "password": "password",
        "meta": {"login": None},
    }
    POSTS: List[Any] = []
    TRACKER_NAME: str = "dummy"
    TRACKER_LOGIN_URL: str | None = None
    TRACKER_URL: str | None = None
    TRACKER_SEARCH_URL_TPL: str | None = None

    _log = None

    def __init__(self, username, password) -> None:
        if all([self.LOGIN_NEEDED, not (username and password)]):
            raise Exception("Please add login credentials to configuration file")
        self.username = username
        self.password = password
        self.POSTS = []
        self._session = None

    def get_status(self):
        pass

    def get_data(self, search_string: str) -> BeautifulSoup:
        self.log.info("Searching for %s on %s", search_string, self.TRACKER_NAME)
        search_url = (
            f"{self.TRACKER_URL}{self.TRACKER_SEARCH_URL_TPL}"
            f"{quote(search_string, safe='')}"
        )
        response = self.session.get(search_url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, "lxml")

    @property
    def session(self) -> requests.Session:
        if self._session:
            return self._session

        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.5563.65 Safari/537.36"
            }
        )

        # this helps debugging
        if bot_config.get("proxy.enabled"):
            proxies = {}
            if bot_config.get("proxy.url"):
                proxies["http"] = bot_config.get("proxy.url")
                proxies["https"] = bot_config.get("proxy.url")
            self._session.proxies.update(proxies)
            self._session.verify = bot_config.get("proxy.verify_tls", True)

        if not self.TRACKER_LOGIN_URL:
            return self._session

        self.log.info("Loggin in %s", self.TRACKER_LOGIN_URL)
        username_field = self.TRACKER_LOGIN_FIELDS["username"]
        password_field = self.TRACKER_LOGIN_FIELDS["password"]

        payload = {
            username_field: self.username,
            password_field: self.password,
            "redirect": "index.php?",
            "sid": "",
            "login": "Login",
        }
        response = self._session.post(self.TRACKER_LOGIN_URL, data=payload, timeout=10)
        response.raise_for_status()

        return self._session

    def search(self, _: str) -> List:
        return []

    @property
    def log(self):
        if not self._log:
            self._log = get_logger(self.__class__.__name__)
        return self._log

    def download(self, file_url: str) -> str:
        self.log.info("Downloading file %s with authorization", file_url)
        response = self.session.get(file_url, allow_redirects=True, timeout=30)
        response.raise_for_status()
        max_size = int(bot_config.get("bot.max_torrent_size", 10 * 1024 * 1024))
        if len(response.content) > max_size:
            raise ValueError("Downloaded torrent exceeds configured size limit")
        return save_torrent_to_tempfile(response.content)
