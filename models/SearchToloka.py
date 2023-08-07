from bs4 import BeautifulSoup
from models.SearchBase import SearchBase

class SearchToloka(SearchBase):
    TRACKER_NAME = 'toloka'
    TRACKER_URL = "https://toloka.to"
    TRACKER_SEARCH_URL_TPL = "https://toloka.to/tracker.php?nm="
    TRACKER_LOGIN_URL = "https://toloka.to/login.php"

    def login(self):
        self.log.info("Loggin in %s", self.TRACKER_LOGIN_URL)
        payload = {
            "username": self.username,
            "password": self.password,
            'redirect': 'index.php?',
            'sid': '',
            'login': 'Login'
        }
        self.SESSION.post(self.TRACKER_LOGIN_URL, data=payload)
        self.LOGGED_IN = True

    def search(self, search_string: str) -> bool:
        self.log.info("Searching for %s on %s", search_string, self.TRACKER_NAME)
        if not self.LOGGED_IN:
            self.login()
        raw_data = self.SESSION.get(f"{self.TRACKER_SEARCH_URL_TPL}{search_string}")
        _data = BeautifulSoup(raw_data.content, 'lxml').select('table.forumline')

        if len(_data) != 2:
            return False
        rows = _data[1].select('tr')

        """Search data on the web"""
        self.log.debug(_data)
        for row in rows:
            _cols = row.select('td')
            if not len(_cols) == 13:
                continue
            TITLE = _cols[2].text.replace(r'<', '')
            INFO = _cols[2].select('a')[0].get('href')
            DL = _cols[5].select('a')[0].get('href')
            SIZE = _cols[6].text
            DATE = _cols[12].text
            SEEDS = _cols[9].text
            LEACH = _cols[10].text
            self.log.debug(f"COL T: {TITLE} L:{str(INFO)} DL:{str(DL)} S:{str(SIZE)} D:{str(DATE)}")

            self.POSTS.append({'tracker': self.TRACKER_NAME,
                               'title': TITLE,
                               'info': f"{self.TRACKER_URL}/{INFO}",
                               'dl': f"{self.TRACKER_URL}/{DL}",
                               'size': SIZE,
                               'date': DATE,
                               'seed': SEEDS,
                               'leach': LEACH})
        return True
