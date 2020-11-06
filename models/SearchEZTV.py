from requests import get
from bs4 import BeautifulSoup
import logging

class SearchEZTV:
    TRACKER_URL="https://eztv.re"
    TRACKER_SEARCH_URL_TPL="/search/"

    def search(self,search_string):    
        logger = logging.getLogger(self.__class__.__name__)
        """Search data on the web"""
        self.POSTS=[]
        x=self.TRACKER_URL+self.TRACKER_SEARCH_URL_TPL+search_string
        _data=BeautifulSoup(get(x).content, 'lxml').select('table.forum_header_border > tr.forum_header_border')
        logger.debug(_data)
        for row in _data:
            _cols=row.select('td')
            TITLE=_cols[1].text
            INFO=_cols[1].select('a')[0].get('href')
            DL=_cols[2].select('a')[0].get('href')
            SIZE=_cols[3].text
            DATE=_cols[4].text
                    
            logger.info("COL Title:"+TITLE+" L:"+str(INFO)+" DL:"+str(DL)+" S:"+str(SIZE)+" D:"+str(DATE))
            self.POSTS.append(
                        {'title': TITLE.replace(r'<',''), 'info':"{0}/forum/{1}".format(self.TRACKER_URL,INFO), 'dl': "{0}/forum/{1}".format(self.TRACKER_URL,DL), 'size':SIZE,'date': DATE }
                            )

