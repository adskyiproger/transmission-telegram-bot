from bs4 import BeautifulSoup
from models.SearchBase import SearchBase
from typing import List

class SearchRutracker(SearchBase):
    TRACKER_NAME = "rutracker"
    TRACKER_URL = "https://rutracker.org"
    TRACKER_SEARCH_URL_TPL = "/forum/tracker.php?nm="
    TRACKER_LOGIN_URL = "https://rutracker.org/forum/login.php"
    TRACKER_LOGIN_FIELDS = {
        "username":"login_username", 
        "password":"login_password", 
        "meta":{
            "login":None
            }
        }

    def convert_date(self, date: str) -> str:
        try:
            _date = date.split("-")
            return f"{_date[2]}-{_date[1]}-{_date[0]}"
        except Exception:
            return date

    def search(self, search_string: str) -> List:
        """Search data on the web"""
        self.log.info("Searching for %s on %s", search_string, self.TRACKER_NAME)
        x = self.TRACKER_URL+self.TRACKER_SEARCH_URL_TPL+search_string

        _data = BeautifulSoup(self.session.get(x).content, 'lxml').select('table.forumline > tbody > tr')
        self.log.debug(_data)
        self.log.info("Found %s posts", len(_data))

        posts = []
        for row in _data:
            try:
                _cols = row.select('td')
                INFO = _cols[3].select('a')[0].get('href')
                TITLE = _cols[3].text.replace(r'<', '').strip()
                DL = _cols[5].select('a')[0].get('href')
                SIZE = "".join(_cols[5].text.split(' ')[0])
                DATE = "".join(_cols[9].text.split(' ')[1:])[0:10]
                SEEDS = _cols[6].text.replace(r'\n', '').strip()
                LEACH = _cols[7].text.replace(r'\n', '').strip()
                self.log.debug(f"COL T: {TITLE} L:{str(INFO)} DL:{str(DL)} S:{str(SIZE)} D:{str(DATE)}")

                posts.append({
                    'tracker': self.TRACKER_NAME,
                    'title': TITLE,
                    'info': f"{self.TRACKER_URL}/forum/{INFO}",
                    'dl': f"{self.TRACKER_URL}/forum/{DL}",
                    'size': SIZE,
                    'date': self.convert_date(DATE),
                    'seed': SEEDS,
                    'leach': LEACH})
            except Exception as e:
                # seems that there is some problem with this tr, let's just continue to the next one
                # self.log.warning(_cols)
                self.log.critical(e, exc_info=True)
                pass

        return posts
