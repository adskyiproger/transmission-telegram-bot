import hashlib
import logging
import pydash as _

from typing import List
from models.SearchNonameClub import SearchNonameClub
from models.SearchRUTOR import SearchRUTOR
# TODO: KAT is down, temporary disabled
# from models.SearchKAT import SearchKAT
from models.SearchToloka import SearchToloka
from lib.func import human_to_bytes, bytes_to_human

log = logging.getLogger(__name__)


class SearchTorrents:
    """
    Search torrent files by provided search string on all torrent
    trackers defined in CLASSES.
    """
    # Key to sort search results
    SORT_BY = 'size'
    # reverse sort order
    SORT_REVERSE = True
    CREDENTIALS = {}
    # List of enabled trackers
    CLASSES = {"nnmclub": SearchNonameClub,
               "rutor": SearchRUTOR,
               # FIXME: Check KAT is alive or dead
               # "kat": SearchKAT,
               "toloka": SearchToloka}
    # Variable for storing search results
    CACHE = {}

    FAILED_TRACKERS = []

    def __init__(self, credentials: dict, sort_by: str) -> None:
        self.CREDENTIALS = credentials
        self.SORT_BY = sort_by

    def search(self, search_string: str) -> List:
        """Check Cached search results and do search if nothing found in cache"""
        srch_hash = hashlib.md5(str(search_string).encode('utf-8')).hexdigest()
        if srch_hash not in self.CACHE.keys():
            self.CACHE[srch_hash] = self._search(search_string)
        return self.sort(self.CACHE[srch_hash])

    def _search(self, search_string: str) -> List:
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
            except Exception as err:
                self.FAILED_TRACKERS.append(_class)
                log.error("Failed search on tracker %s: %s", _class, err)
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
            post["size"] = human_to_bytes(post['size'])
        return posts

    def post_sort_format(self, posts):
        # Convert size B -> human readable (K, M, G)
        if self.SORT_BY != "size":
            return posts
        for el in posts:
            el['size'] = bytes_to_human(el['size'])
        return posts
