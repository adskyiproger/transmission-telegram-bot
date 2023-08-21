import hashlib
import pydash as _
import time
from typing import List, Dict
from models.SearchNonameClub import SearchNonameClub
from models.SearchRUTOR import SearchRUTOR
from models.SearchBase import SearchBase
# TODO: KAT is down, temporary disabled
# from models.SearchKAT import SearchKAT
from models.SearchToloka import SearchToloka
from lib.func import (human_to_bytes,
                      bytes_to_human,
                      get_logger)
from lib.constants import CACHE_TIMEOUT
log = get_logger("SearchTorrents")


class SearchTorrents:
    """
    Search torrent files by provided search string on all torrent
    trackers defined in CLASSES.
    """
    # Key to sort search results
    sort_by = 'size'
    # reverse sort order
    SORT_REVERSE = True
    # CREDENTIALS: {
    # "trakcer_name": {
    #     "user": <user name>,
    #     "password": <password>
    # }}
    # TODO: For 2-factor auth we need to implement authentication with phpbb tokens
    CREDENTIALS = {}
    # List of enabled trackers
    CLASSES = {"nnmclub": SearchNonameClub,
               "rutor": SearchRUTOR,
               # FIXME: Check KAT is alive or dead
               # "kat": SearchKAT,
               "toloka": SearchToloka}
    # Variable for storing search results
    CACHE = {}
    CACHE_TIMER = {}
    def __init__(self, credentials: dict, sort_by: str) -> None:
        self.CREDENTIALS = credentials
        self.sort_by = sort_by
        self._trackers = {}
        self.FAILED_SEARCH = []
        self.FAILED_TRACKERS = []

    @property
    def trackers(self) -> Dict[str, SearchBase]:
        if self.FAILED_TRACKERS:
            self._trackers = None
            self.FAILED_TRACKERS = None
        if self._trackers:
            return self._trackers

        for _class in self.CLASSES:
            try:
                tracker = self.CLASSES[_class](
                    username=_.get(self.CREDENTIALS, [_class, "user"]),
                    password=_.get(self.CREDENTIALS, [_class, "password"]))
                self._trackers[_class] = tracker
                log.info("Initialised tracker %s", _class)
            except Exception as err:
                self.FAILED_TRACKERS.append(_class)
                log.error("Failed initialise tracker %s due to error: %s", _class, err)
        return self._trackers

    def search(self, search_string: str) -> List:
        """Check Cached search results and do search if nothing found in cache"""
        srch_hash = hashlib.md5(str(search_string).encode('utf-8')).hexdigest()

        if _.get(self.CACHE_TIMER, srch_hash, time.time() - CACHE_TIMEOUT * 2) < time.time() - CACHE_TIMEOUT:
            self.CACHE_TIMER[srch_hash] = time.time()
            self.CACHE[srch_hash] = self._search(search_string)
        return self.sort(self.CACHE[srch_hash])

    def _search(self, search_string: str) -> List:
        """Search over trackers"""
        log.info("Searching for: %s", search_string)
        posts = []
        self.FAILED_SEARCH = []
        # Search over enabled trackers
        for tracker_name, tracker in self.trackers.items():
            try:
                posts.extend(tracker.search(search_string))
                log.info("Found %s posts on %s trackers", len(posts), ', '.join(self.trackers.keys()))
            except Exception as err:
                self.FAILED_SEARCH.append(tracker_name)
                log.error("Failed search due to error: %s", err)
        return posts

    def sort(self, posts: List) -> List:
        try:
            posts = self.pre_sort_format(posts)
            sorted_list = sorted(posts,
                                 key=lambda d: int(d[self.sort_by]),
                                 reverse=self.SORT_REVERSE)
            # Store results in cache if sorting went well
            posts = self.post_sort_format(sorted_list)
        except Exception as err:
            log.fatal(err)
            log.fatal(posts)
        return posts

    def pre_sort_format(self, posts):
        if self.sort_by != "size":
            return posts
        for post in posts:
            post["size"] = human_to_bytes(post['size'])
        return posts

    def post_sort_format(self, posts):
        # Convert size B -> human readable (K, M, G)
        if self.sort_by != "size":
            return posts
        for el in posts:
            el['size'] = bytes_to_human(el['size'])
        return posts

    def download(self, url: str, tracker: str) -> str:
        return self.trackers[tracker].download(url)
