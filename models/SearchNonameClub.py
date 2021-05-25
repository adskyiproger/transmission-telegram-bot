from requests import get
from bs4 import BeautifulSoup
import logging
#logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class SearchNonameClub:
    TRACKER_URL="https://nnmclub.to"
    TRACKER_SEARCH_URL_TPL="/forum/tracker.php?nm="

    def search(self,search_string):    
        logger = logging.getLogger(self.__class__.__name__)
        """Search data on the web"""
        self.POSTS=[]
        x=self.TRACKER_URL+self.TRACKER_SEARCH_URL_TPL+search_string
        _data=BeautifulSoup(get(x).content, 'lxml').select('table.forumline > tbody > tr')
        logger.debug(_data)
        for row in _data:
            _cols=row.select('td')
            TITLE=_cols[2].text
            INFO=_cols[2].select('a')[0].get('href')
            DL=_cols[4].select('a')[0].get('href')
            SIZE="".join(_cols[5].text.split(' ')[1:])
            DATE="".join(_cols[9].text.split(' ')[1:])[0:10]
                    
            logger.info("COL Title:"+TITLE+" L:"+str(INFO)+" DL:"+str(DL)+" S:"+str(SIZE)+" D:"+str(DATE))
            self.POSTS.append(
                        {'title': TITLE.replace(r'<',''), 'info':"{0}/forum/{1}".format(self.TRACKER_URL,INFO), 'dl': "{0}/forum/{1}".format(self.TRACKER_URL,DL), 'size':SIZE,'date': DATE }
                            )

