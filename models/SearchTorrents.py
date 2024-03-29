import hashlib
import pydash as _
import time
from typing import List, Dict
from models.SearchNonameClub import SearchNonameClub
from models.SearchRutracker import SearchRutracker
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
    # List of available trackers
    TRACKER_CLASSES = {
        "nnmclub": SearchNonameClub,
        "rutracker": SearchRutracker,
        "rutor": SearchRUTOR,
        # FIXME: Check KAT is alive or dead
        # "kat": SearchKAT,
        "toloka": SearchToloka
    }

    # Variable for storing search results
    CACHE = {}
    CACHE_TIMER = {}

    def __init__(self, credentials: dict, sort_by: str) -> None:
        self.CREDENTIALS = credentials
        self.sort_by = sort_by
        self._trackers = dict()
        self.FAILED_SEARCH = []
        self.FAILED_TRACKERS = []

    @property
    def trackers(self) -> Dict[str, SearchBase]:
        """Initialize trackers"""
        if self._trackers:
            log.info("Trackers initialized: %s", ", ".join(self._trackers.keys()))
            return self._trackers
        log.info("Initialising search trackers from available classes: %s",
                 ", ".join(self.TRACKER_CLASSES.keys()))
        for _class in self.TRACKER_CLASSES:
            # Conditionally disable tracker if not working
            if not _.get(self.CREDENTIALS, [_class, 'enabled'], True):
                log.info("Tracker %s is disabled in configuration file. Skipped initialisation", _class)
                continue
            try:
                tracker = self.TRACKER_CLASSES[_class](
                    username=_.get(self.CREDENTIALS, [_class, "user"]),
                    password=_.get(self.CREDENTIALS, [_class, "password"]))
                self._trackers[_class] = tracker
                log.debug("Initialised tracker %s", _class)
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
        # Search over enabled trackers
        for tracker_name, tracker in self.trackers.items():
            try:
                posts.extend(tracker.search(search_string))
                log.info("Found %s posts on trackers: %s", len(posts), ', '.join(self.trackers.keys()))
            except Exception as err:
                self.FAILED_SEARCH.append(tracker_name)
                log.error("Failed search on tracker %s due to error: %s", err, tracker_name)
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
