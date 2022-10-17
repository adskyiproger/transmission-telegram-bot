from models.SearchBase import SearchBase
from models.SearchNonameClub import SearchNonameClub
from models.SearchRUTOR import SearchRUTOR
# TODO: KAT is down, temporary disabled
# from models.SearchKAT import SearchKAT
from models.SearchToloka import SearchToloka
import hashlib, threading, time, logging
import math


def convert_size(size_bytes):
    print(size_bytes)
    if size_bytes == 0:
        return "0B"
    size_name = ( "B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


log = logging.getLogger(__name__)


class SearchTorrents:
    # Key to sort search results
    SORT_BY = 'size'
    UNITS = {'KB': 1024, 'MB': 1048576, 'GB': 1073741824 }
    # reverse sort order
    SORT_REVERSE = True
    CREDENTIALS = {}
    # List of enabled trackers
    CLASSES = {"nnmclub" : SearchNonameClub,
               "rutor" : SearchRUTOR,
               "toloka" : SearchToloka,
           #   "kat" : SearchKAT
              }
    # Variable for storing search results
    CACHE = {}

    POSTS = []
    FAILED_TRACKERS = []
    def __init__(self, search_string: str) -> bool:

        log.info("Searching for: %s", search_string)
        srch_hash = hashlib.md5(str(search_string).encode('utf-8')).hexdigest()
        if srch_hash in self.CACHE.keys():
            log.info("Found cached search results for: %s", search_string)
            self.POSTS=self.CACHE[srch_hash]
        else:
            posts = []
            # Search over enabled trackers
            for _class in self.CLASSES:
                try:
                    if _class in self.CREDENTIALS:
                        creds = self.CREDENTIALS[_class]
                        TRACKER = self.CLASSES[_class](username=creds["USERNAME"],
                                                       password=creds["PASSWORD"])
                    else:
                        TRACKER=self.CLASSES[_class]()

                    TRACKER.search(search_string)
                    posts.extend(TRACKER.POSTS)
                except:
                    self.FAILED_TRACKERS.append(_class)
            log.info("Found %s posts on %s trackers", len(posts), ', '.join(self.CLASSES.keys()))
            if self.SORT_BY == "size":
                for post in posts:
                    print(f'{post["tracker"]}: {str(post["size"])[-2:].upper()}')
                    
                    try:
                        post["size"] = int(float(post["size"][:-2])) * self.UNITS[post["size"][-2:].upper()]
                    except:
                        continue
            # Sort search results before returning data back to user
            try:
                sorted_list = sorted(posts, 
                                     key=lambda d: int(d[self.SORT_BY]),
                                     reverse=self.SORT_REVERSE)

                # Store results in cache if sorting went well
                self.POSTS = sorted_list
            except Exception as err:
                log.fatal(err)
                log.fatal(self.POSTS)
                self.POSTS = posts
            # Convert size B -> human readable (K, M, G)
            if self.SORT_BY == "size":
                for el in self.POSTS:
                    try:
                        el['size'] = convert_size(el['size'])
                    except Exception as err:
                        log.error("Conversion failed: %s", el)
                self.CACHE[srch_hash]=self.POSTS
        log.info("Found %s posts on trackers %s", len(self.POSTS), ', '.join(self.CLASSES))
