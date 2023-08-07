from bs4 import BeautifulSoup
from models.SearchBase import SearchBase
from typing import List


class SearchToloka(SearchBase):
    TRACKER_NAME = 'toloka'
    TRACKER_URL = "https://toloka.to"
    TRACKER_SEARCH_URL_TPL = "https://toloka.to/tracker.php?nm="
    TRACKER_LOGIN_URL = "https://toloka.to/login.php"

    def search(self, search_string: str) -> List:
        self.log.info("Searching for %s on %s", search_string, self.TRACKER_NAME)

        raw_data = self.session.get(f"{self.TRACKER_SEARCH_URL_TPL}{search_string}")
        _data = BeautifulSoup(raw_data.content, 'lxml').select('table.forumline')

        if len(_data) != 2:
            return False
        rows = _data[1].select('tr')
        self.log.debug(rows)
        """Search data on the web"""
        self.log.info("Found %s posts", len(rows))

        posts = []
        for row in rows[1:]:
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

            posts.append({
                'tracker': self.TRACKER_NAME,
                'title': TITLE,
                'info': f"{self.TRACKER_URL}/{INFO}",
                'dl': f"{self.TRACKER_URL}/{DL}",
                'size': SIZE,
                'date': DATE,
                'seed': SEEDS,
                'leach': LEACH})
        return posts
