from bs4 import BeautifulSoup
from models.SearchBase import SearchBase
from typing import List

class SearchNonameClub(SearchBase):
    TRACKER_NAME = "nnmclub"
    TRACKER_URL = "https://nnmclub.to"
    TRACKER_SEARCH_URL_TPL = "/forum/tracker.php?nm="
    TRACKER_LOGIN_URL = "https://nnmclub.to/forum/login.php"

    def convert_date(self, date: str) -> str:
        try:
            _date = date.split("-")
            return f"{_date[2]}-{_date[1]}-{_date[0]}"
        except Exception:
            return date

    def search(self, search_string: str) -> List:
        """Search data on the web"""

        _data = self.get_data(search_string).select('table.forumline > tbody > tr')
        self.log.debug(_data)
        self.log.info("Found %s posts", len(_data))

        posts = []
        for row in _data:
            try:
                _cols = row.select('td')
                TITLE = _cols[2].text.replace(r'<', '')
                INFO = _cols[2].select('a')[0].get('href')
                DL = _cols[4].select('a')[0].get('href')
                SIZE = "".join(_cols[5].text.split(' ')[1:])
                DATE = "".join(_cols[9].text.split(' ')[1:])[0:10]
                authorized = False
                for key in self.session.cookies.get_dict().keys():
                    if key.startswith("phpbb2mysql"):
                        authorized = True
                if authorized:
                    SEEDS = _cols[7].text
                    LEACH = _cols[8].text
                else:
                    SEEDS = _cols[6].text
                    LEACH = _cols[7].text
                self.log.info(f"Found seeds: {SEEDS}, leaches: {LEACH}")
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
