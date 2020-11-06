from requests import get
from bs4 import BeautifulSoup
import logging
#logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class SearchKAT:
    TRACKER_URL="https://kat.sx"
    TRACKER_SEARCH_URL_TPL="/search.php?q="

    def search(self,search_string):    
        logger = logging.getLogger(self.__class__.__name__)
        """Search data on the web"""
        self.POSTS=[]
        x=self.TRACKER_URL+self.TRACKER_SEARCH_URL_TPL+search_string
        _data=BeautifulSoup(get(x).content, 'lxml').select('table.data > tr.odd')
        logger.debug(_data)
        for row in _data:
            _cols=row.select('td')
            #print(_cols)
            TITLE=_cols[0].select('div.torrentname > div.markeredBlock > a.cellMainLink')[0].text
            INFO=_cols[0].select('div.torrentname > div.markeredBlock > a.cellMainLink')[0].get('href')
            DL=_cols[0].select('div.iaconbox > a')[3].get('href')
            SIZE=_cols[1].text
            DATE=_cols[2].text
                    
            logger.info("COL Title:"+TITLE+" L:"+str(INFO)+" DL:"+str(DL)+" S:"+str(SIZE)+" D:"+str(DATE))
            self.POSTS.append(
                        {'title': TITLE.replace(r'<',''), 'info':"{0}/forum/{1}".format(self.TRACKER_URL,INFO), 'dl': "{0}/forum/{1}".format(self.TRACKER_URL,DL), 'size':SIZE,'date': DATE }
                            )

