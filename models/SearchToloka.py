import requests
from bs4 import BeautifulSoup
import logging

from models.SearchBase import SearchBase

# logging.basicConfig( format = '[%(asctime)s] [%(levelname)s]: %(name)s %(message)s',
#                      level = logging.getLevelName("INFO"))

class SearchToloka(SearchBase):
    TRACKER_NAME = 'toloka'
    TRACKER_URL = "https://toloka.to"
    TRACKER_SEARCH_URL_TPL = "https://toloka.to/tracker.php?nm="
    TRACKER_LOGIN_URL = "https://toloka.to/login.php"
    

    def __init__(self, username, password) -> None:
        self.username = username
        self.password = password

    def login(self):
        self.log.info("Loggin in")
        payload = {
            "username": self.username,
            "password": self.password,
            'redirect':'index.php?', 
            'sid':'', 
            'login':'Login'
        }
        self.SESSION.post(self.TRACKER_LOGIN_URL, data=payload)
        self.LOGGED_IN = True

    def search(self, search_string: str) -> bool:
        self.log.info("Searching for something")
        if not self.LOGGED_IN:
            self.login()
        raw_data = self.SESSION.get(f"{self.TRACKER_SEARCH_URL_TPL}{search_string}")
        _data=BeautifulSoup(raw_data.content, 'lxml').select('table.forumline')
        
        if len(_data) != 2:
            return False
        rows = _data[1].select('tr')
        
        """Search data on the web"""
        self.log.debug(_data)
        for row in rows:
            _cols = row.select('td')
            if not len(_cols) == 13:
                continue
            TITLE=_cols[2].text.replace(r'<', '')
            INFO=_cols[2].select('a')[0].get('href')
            DL=_cols[5].select('a')[0].get('href')
            SIZE=_cols[6].text
            DATE=_cols[12].text
            self.log.debug(f"COL T: {TITLE} L:{str(INFO)} DL:{str(DL)} S:{str(SIZE)} D:{str(DATE)}")

            # if SIZE[-2:].upper() in self.UNITS.keys():
            #     SIZE = int(float(SIZE[:-2])) * self.UNITS[SIZE[-2:].upper()]
            SEEDS = _cols[9].text
            LEACH = _cols[10].text
            self.log.debug(f"COL T: {TITLE} L:{str(INFO)} DL:{str(DL)} S:{str(SIZE)} D:{str(DATE)}")
            self.POSTS.append({'tracker': self.TRACKER_NAME,
                               'title': TITLE,
                                'info': f"{self.TRACKER_URL}/{INFO}",
                                'dl': f"{self.TRACKER_URL}/{DL}",
                                'size' :SIZE,
                                'date': DATE,
                                'seed': SEEDS,
                                'leach': LEACH})
        return True
