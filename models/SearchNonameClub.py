from requests import get
from bs4 import BeautifulSoup
import logging
#logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
from models.SearchBase import SearchBase

class SearchNonameClub(SearchBase):
    TRACKER_NAME = "nnmclub"
    TRACKER_URL="https://nnmclub.to"
    TRACKER_SEARCH_URL_TPL="/forum/tracker.php?nm="

    def convert_date(self, date: str):
        _date = date.split("-")
        return f"{_date[2]}-{_date[1]}-{_date[0]}"

    def search(self, search_string: str) -> bool:
        """Search data on the web"""
        self.log.info("Searching for %s on %s", search_string, self.TRACKER_NAME)
        x=self.TRACKER_URL+self.TRACKER_SEARCH_URL_TPL+search_string
        _data=BeautifulSoup(self.SESSION.get(x).content, 'lxml').select('table.forumline > tbody > tr')
        self.log.debug(_data)
        for row in _data:
            _cols=row.select('td')
            TITLE=_cols[2].text.replace(r'<', '')
            INFO=_cols[2].select('a')[0].get('href')
            DL=_cols[4].select('a')[0].get('href')
            SIZE="".join(_cols[5].text.split(' ')[1:])
            DATE="".join(_cols[9].text.split(' ')[1:])[0:10]
            SEEDS = _cols[6].text
            LEACH = _cols[7].text
            self.log.debug(f"COL T: {TITLE} L:{str(INFO)} DL:{str(DL)} S:{str(SIZE)} D:{str(DATE)}")
            
            self.POSTS.append({'tracker': self.TRACKER_NAME,
                               'title': TITLE,
                               'info': f"{self.TRACKER_URL}/forum/{INFO}",
                               'dl': f"{self.TRACKER_URL}/forum/{DL}",
                               'size': SIZE,
                               'date': self.convert_date(DATE),
                               'seed': SEEDS,
                               'leach': LEACH})
        return True
