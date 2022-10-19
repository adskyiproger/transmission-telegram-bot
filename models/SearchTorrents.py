from models.SearchBase import SearchBase
from models.SearchNonameClub import SearchNonameClub
from models.SearchRUTOR import SearchRUTOR
# TODO: KAT is down, temporary disabled
# from models.SearchKAT import SearchKAT
from models.SearchToloka import SearchToloka
import hashlib, threading, time, logging
import math
import pydash as _


def convert_size(size_bytes):
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

    FAILED_TRACKERS = []
    def __init__(self, credentials, sort_by):
        self.CREDENTIALS = credentials
        self.SORT_BY = sort_by

    def search(self,search_string: str) -> list:
        """Check Cached search results and do search if nothing found in cache"""
        srch_hash = hashlib.md5(str(search_string).encode('utf-8')).hexdigest()
        if srch_hash not in self.CACHE.keys():
            self.CACHE[srch_hash] = self._search(search_string)
        return self.sort(self.CACHE[srch_hash])

    def _search(self, search_string: str) -> list:
        """Search over trackers"""
        posts = []
        log.info("Searching for: %s", search_string)
        # Search over enabled trackers
        for _class in self.CLASSES:
            try:
                TRACKER = self.CLASSES[_class](
                    username=_.get(self.CREDENTIALS, f"{_class}.USERNAME", None),
                    password=_.get(self.CREDENTIALS, f"{_class}.PASSWORD", None))
                TRACKER.search(search_string)
                posts.extend(TRACKER.POSTS)
            except:
                self.FAILED_TRACKERS.append(_class)
        log.info("Found %s posts on %s trackers", len(posts), ', '.join(self.CLASSES.keys()))
        return posts

    def sort(self, posts):
        try:
            posts = self.pre_sort_format(posts)
            sorted_list = sorted(posts, 
                                    key=lambda d: int(d[self.SORT_BY]),
                                    reverse=self.SORT_REVERSE)
            # Store results in cache if sorting went well
            posts = self.post_sort_format(sorted_list)
        except Exception as err:
            log.fatal(err)
            log.fatal(posts)
        return posts

    def pre_sort_format(self, posts):
        if self.SORT_BY != "size":
            return posts
        for post in posts:
            try:
                post["size"] = int(float(post["size"][:-2])) * self.UNITS[post["size"][-2:].upper()]
            except:
                continue
        return posts

    def post_sort_format(self, posts):
        # Convert size B -> human readable (K, M, G)
        if self.SORT_BY != "size":
            return posts
        for el in posts:
            try:
                el['size'] = convert_size(el['size'])
            except Exception as err:
                log.error("Conversion failed: %s", el)
        return posts