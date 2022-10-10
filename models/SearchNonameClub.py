from requests import get
from bs4 import BeautifulSoup
import logging
#logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
from models.SearchBase import SearchBase

class SearchNonameClub(SearchBase):
    TRACKER_NAME = "nnmclub"
    TRACKER_URL="https://nnmclub.to"
    TRACKER_SEARCH_URL_TPL="/forum/tracker.php?nm="

    def __init__(self, username=None, password=None) -> None:
        pass

    def search(self,search_string):    
        logger = logging.getLogger(self.__class__.__name__)
        """Search data on the web"""
        self.POSTS=[]
        x=self.TRACKER_URL+self.TRACKER_SEARCH_URL_TPL+search_string
        _data=BeautifulSoup(get(x).content, 'lxml').select('table.forumline > tbody > tr')
        logger.debug(_data)
        for row in _data:
            _cols=row.select('td')
            TITLE=_cols[2].text.replace(r'<', '')
            INFO=_cols[2].select('a')[0].get('href')
            DL=_cols[4].select('a')[0].get('href')
            SIZE="".join(_cols[5].text.split(' ')[1:])
            DATE="".join(_cols[9].text.split(' ')[1:])[0:10]
            UNITS = {'KB': 1024, 'MB': 1048576, 'GB': 1073741824 }
            if SIZE[-2:].upper() in UNITS.keys():
                SIZE = int(float(SIZE[:-2])) * UNITS[SIZE[-2:].upper()]

            logger.debug(f"COL T: {TITLE} L:{str(INFO)} DL:{str(DL)} S:{str(SIZE)} D:{str(DATE)}")
            self.POSTS.append({'tracker': self.TRACKER_NAME,
                               'title': TITLE,
                               'info': f"{self.TRACKER_URL}/forum/{INFO}",
                               'dl': f"{self.TRACKER_URL}/forum/{DL}",
                               'size':SIZE,
                               'date': DATE })
