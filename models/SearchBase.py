import requests
from typing import List
from bs4 import BeautifulSoup

from lib.func import get_logger, save_torrent_to_tempfile
from models.BotConfigurator import BotConfigurator

bot_config = BotConfigurator()

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

    def get_data(self, search_string: str):
        self.log.info("Searching for %s on %s", search_string, self.TRACKER_NAME)
        search_url = self.TRACKER_URL+self.TRACKER_SEARCH_URL_TPL+search_string
        return BeautifulSoup(self.session.get(search_url, timeout=10).content, 'lxml')

    @property
    def session(self) -> requests.Session:
        if self._session:
            return self._session

        self._session = requests.Session()
        self._session.headers.update(
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.5563.65 Safari/537.36'})

        # this helps debugging
        if bot_config.get('proxy.enabled'):
            proxies = {}
            if bot_config.get('proxy.url'):
                proxies['http'] = bot_config.get('proxy.url')
                proxies['https'] = bot_config.get('proxy.url')
            self._session.proxies.update(proxies)
            self._session.verify = False

        self.log.debug("%s %s", self.username, self.password)
        if self.TRACKER_LOGIN_URL:
            self.log.info("Loggin in %s", self.TRACKER_LOGIN_URL)
            username_field = "username"
            password_field = "password"

            try:
                if self.TRACKER_LOGIN_FIELDS:
                    username_field = self.TRACKER_LOGIN_FIELDS['username']
                    password_field = self.TRACKER_LOGIN_FIELDS['password']
            except Exception as e:
                self.log.warning(e)
                pass
            payload = {
                username_field: self.username,
                password_field: self.password,
                'redirect': 'index.php?',
                'sid': '',
                'login': 'Login'
            }
            self._session.post(self.TRACKER_LOGIN_URL, data=payload, timeout=10)

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