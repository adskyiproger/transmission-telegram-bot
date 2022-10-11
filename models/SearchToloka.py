import requests
from bs4 import BeautifulSoup
import logging

from models.SearchBase import SearchBase


class SearchToloka(SearchBase):
    SESSION = None

    def __init__(self, username, password) -> None:
        self.TRACKER_NAME = 'toloka'
        self.TRACKER_URL = "https://toloka.to"
        self.TRACKER_SEARCH_URL_TPL = self.TRACKER_URL + "/tracker.php?nm="
        self.TRACKER_LOGIN_URL = self.TRACKER_URL + "/login.php"
        self.username = username
        self.password = password
        self.SESSION = None
        self.POSTS=[]

    def login(self):
        headers = {'User-Agent': 'Mozilla/5.0'}
        payload = {
            "username": self.username,
            "password": self.password,
            'redirect':'index.php?', 
            'sid':'', 
            'login':'Login'
        }
        self.SESSION = requests.Session()
        self.SESSION.post(self.TRACKER_LOGIN_URL, data=payload)

    def search(self, search_string):
        if not self.SESSION:
            self.login()
        raw_data = self.SESSION.get(self.TRACKER_SEARCH_URL_TPL + search_string)
        _data=BeautifulSoup(raw_data.content, 'lxml').select('table.forumline')
        
        if len(_data) != 2:
            return self.POSTS
        rows = _data[1].select('tr')
        logger = logging.getLogger(self.__class__.__name__)
        """Search data on the web"""
        logger.debug(_data)
        for row in rows:
            _cols = row.select('td')
            if not len(_cols) == 13:
                continue
            TITLE=_cols[2].text.replace(r'<', '')
            INFO=_cols[2].select('a')[0].get('href')
            DL=_cols[5].select('a')[0].get('href')
            SIZE=_cols[6].text
            DATE=_cols[12].text
            UNITS = {'KB': 1024, 'MB': 1048576, 'GB': 1073741824 }
            logger.debug(f"COL T: {TITLE} L:{str(INFO)} DL:{str(DL)} S:{str(SIZE)} D:{str(DATE)}")

            if SIZE[-2:].upper() in UNITS.keys():
                SIZE = int(float(SIZE[:-2])) * UNITS[SIZE[-2:].upper()]

            SEEDS = _cols[9].text
            LEACH = _cols[10].text
            logger.debug(f"COL T: {TITLE} L:{str(INFO)} DL:{str(DL)} S:{str(SIZE)} D:{str(DATE)}")
            self.POSTS.append({'tracker': self.TRACKER_NAME,
                               'title': TITLE,
                                'info': f"{self.TRACKER_URL}/{INFO}",
                                'dl': f"{self.TRACKER_URL}/{DL}",
                                'size' :SIZE,
                                'date': DATE,
                                'seed': SEEDS,
                                'leach': LEACH})
