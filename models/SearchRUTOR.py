from requests import get
from bs4 import BeautifulSoup
import logging



class SearchRUTOR:
    TRACKER_URL="http://rutor.info"
    TRACKER_SEARCH_URL_TPL="/search/0/0/000/0/"

    def search(self,search_string):    
        logger = logging.getLogger(self.__class__.__name__)
        """Search data on the web"""
        self.POSTS=[]
        x=self.TRACKER_URL+self.TRACKER_SEARCH_URL_TPL+search_string
        _data=BeautifulSoup(get(x).content, 'lxml').select('div#index > table > tr')
        for row in _data[1:]:
            _cols=row.select('td')
            TITLE=_cols[1].select('a')[2].text
            INFO=_cols[1].select('a')[2].get('href')
            DL=_cols[1].select('a')[1].get('href')
            SIZE = _cols[3].text if len(_cols) == 5 else _cols[2].text
            UNITS = {'KB': 1024, 'KB': 1024, 'MB': 1048576, 'GB': 1073741824 }
            # try:
                #logger.info(f"Size {SIZE.split('\\xa0')}")
            if SIZE.split('\xa0')[1].upper() in UNITS.keys():
                SIZE = int(float(SIZE.split('\xa0')[0])) * UNITS[SIZE.split('\xa0')[1].upper()]
            # except Exception as e:
            #    logger.error(f"Can not convert {SIZE}")
            #    SIZE = '0'
            DATE=_cols[0].text
                    
            logger.debug("COL Title:"+TITLE+" L:"+str(INFO)+" DL:"+str(DL)+" S:"+str(SIZE)+" D:"+str(DATE))
            self.POSTS.append(
                        {'title': TITLE.replace(r'<',''), 'info':"{0}/{1}".format(self.TRACKER_URL,INFO), 'dl': "{1}".format(self.TRACKER_URL,DL), 'size':SIZE,'date': DATE }
                            )

