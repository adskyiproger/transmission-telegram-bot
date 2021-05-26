from models.SearchNonameClub import SearchNonameClub
from models.SearchRUTOR import SearchRUTOR
from models.SearchEZTV import SearchEZTV
from models.SearchKAT import SearchKAT
import hashlib, threading, time, logging

logger = logging.getLogger(__name__)
class SearchTorrents:
     CLASSES={ "nnmclub" : SearchNonameClub,
               "rutor" : SearchRUTOR,
               "EZTV" : SearchEZTV,
               "KAT" : SearchKAT
             }
     CACHE={}
     CACHE_TIMER={}
     def __init__(self, name="rutor", search_string="test"):
         self.PAGES={}
         self.LINKS={}
         self.POSTS={}
         x=search_string
         logger.info("Searching on tracker {0} for: {1}".format(name,search_string))
         srch_hash=hashlib.md5(str(name+search_string).encode('utf-8')).hexdigest()
         if srch_hash in self.CACHE.keys():
             logger.info("Found cached search results for: {0}".format(search_string))
             self.POSTS=self.CACHE[srch_hash]
         else:
             TRACKER=self.CLASSES[name]()
             TRACKER.search(x)
             self.POSTS=TRACKER.POSTS
             self.CACHE[srch_hash]=TRACKER.POSTS

         _message=""
         kk=1
         ii=1
         jj=1
         for post in self.POSTS:
             _message += f"\n<b>{post['title']}</b>: {post['size']}  {post['date']}\n<a href='{post['info']}'>Info</a>     [ ▼ /download_{ii} ]\n"
             self.LINKS[str(ii)]=post['dl']
             ii+=1
             if kk == 5:
                self.PAGES[str(jj)]=_message
                kk=0
                jj+=1
                _message=""
             kk+=1
         if kk>1:
            self.PAGES[str(jj)]=_message
             
         logger.info(f"Found {len(self.LINKS)} posts grouped into {len(self.PAGES)} pages for {search_string} on tracker {name}")

