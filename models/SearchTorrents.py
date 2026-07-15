import hashlib
import pydash as _
import time
from copy import deepcopy

from typing import List, Dict, Any
from models.SearchNonameClub import SearchNonameClub
from models.SearchRutracker import SearchRutracker
from models.SearchRUTOR import SearchRUTOR
from models.SearchBase import SearchBase

# TODO: KAT is down, temporary disabled
# from models.SearchKAT import SearchKAT
from models.SearchToloka import SearchToloka
from lib.func import human_to_bytes, bytes_to_human, get_logger
from lib.constants import CACHE_TIMEOUT

log = get_logger("SearchTorrents")


class SearchTorrents:
    """
    Search torrent files by provided search string on all torrent
    trackers defined in CLASSES.
    """

    # Key to sort search results
    sort_by: str = "size"
    # reverse sort order
    SORT_REVERSE: bool = True
    # CREDENTIALS: {
    # "trakcer_name": {
    #     "user": <user name>,
    #     "password": <password>
    # }}
    # TODO: For 2-factor auth we need to implement authentication with phpbb tokens
    CREDENTIALS: Dict[str, Any] = {}
    # List of available trackers
    TRACKER_CLASSES: Dict[str, Any] = {
        "nnmclub": SearchNonameClub,
        "rutracker": SearchRutracker,
        "rutor": SearchRUTOR,
        # FIXME: Check KAT is alive or dead
        # "kat": SearchKAT,
        "toloka": SearchToloka,
    }

    # Variable for storing search results in cache
    # Cached items
    CACHE: Dict[str, Any] = {}
    # Time of adding search results to cache
    CACHE_TIMER: Dict[str, Any] = {}
    MAX_CACHE_ITEMS = 128

    def __init__(self, credentials: dict, sort_by: str) -> None:
        self.CREDENTIALS = credentials
        self.sort_by = sort_by
        self._trackers: Dict[str, Any] = {}
        self.FAILED_SEARCH: List[str] = []
        self.FAILED_TRACKERS: List[str] = []

    @property
    def trackers(self) -> Dict[str, SearchBase]:
        """Initialize trackers"""
        if self._trackers:
            log.info("Trackers initialized: %s", ", ".join(self._trackers.keys()))
            return self._trackers
        log.info(
            "Initialising search trackers from available classes: %s",
            ", ".join(self.TRACKER_CLASSES.keys()),
        )
        for _class in self.TRACKER_CLASSES:
            # Conditionally disable tracker if not working
            if not _.get(self.CREDENTIALS, [_class, "enabled"], True):
                log.info(
                    "Tracker %s is disabled in configuration file. Skipped initialisation",
                    _class,
                )
                continue
            try:
                tracker = self.TRACKER_CLASSES[_class](
                    username=_.get(self.CREDENTIALS, [_class, "user"]),
                    password=_.get(self.CREDENTIALS, [_class, "password"]),
                )
                self._trackers[_class] = tracker
                log.debug("Initialised tracker %s", _class)
            except Exception as err:
                self.FAILED_TRACKERS.append(_class)
                log.error("Failed initialise tracker %s due to error: %s", _class, err)
        return self._trackers

    def search(self, search_string: str) -> List:
        """Check Cached search results and do search if nothing found in cache"""
        enabled_trackers = sorted(
            name
            for name in self.TRACKER_CLASSES
            if _.get(self.CREDENTIALS, [name, "enabled"], True)
        )
        cache_key = f"{search_string}\0{self.sort_by}\0{','.join(enabled_trackers)}"
        srch_hash = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()
        # Get time of adding search results to cache
        cache_added_time = _.get(
            self.CACHE_TIMER, srch_hash, time.time() - CACHE_TIMEOUT * 2
        )
        if cache_added_time < time.time() - CACHE_TIMEOUT:
            self.CACHE_TIMER[srch_hash] = time.time()
            self.CACHE[srch_hash] = self._search(search_string)
        self._prune_cache()
        return self.sort(deepcopy(self.CACHE[srch_hash]))

    def _prune_cache(self) -> None:
        expired_before = time.time() - CACHE_TIMEOUT
        expired = [
            key for key, added in self.CACHE_TIMER.items() if added < expired_before
        ]
        for key in expired:
            self.CACHE.pop(key, None)
            self.CACHE_TIMER.pop(key, None)
        while len(self.CACHE_TIMER) > self.MAX_CACHE_ITEMS:
            oldest = min(self.CACHE_TIMER, key=self.CACHE_TIMER.get)
            self.CACHE.pop(oldest, None)
            self.CACHE_TIMER.pop(oldest, None)

    def _search(self, search_string: str) -> List:
        """Search over trackers"""
        log.info("Searching for: %s", search_string)
        posts = []
        # Search over enabled trackers
        for tracker_name, tracker in self.trackers.items():
            try:
                posts.extend(tracker.search(search_string))
                log.info(
                    "Found %s posts on trackers: %s",
                    len(posts),
                    ", ".join(self.trackers.keys()),
                )
            except Exception as err:
                self.FAILED_SEARCH.append(tracker_name)
                log.error(
                    "Failed search on tracker %s due to error: %s", tracker_name, err
                )
        return posts

    def sort(self, posts: List) -> List:
        try:
            posts = self.pre_sort_format(posts)
            sorted_list = sorted(
                posts, key=lambda d: int(d[self.sort_by]), reverse=self.SORT_REVERSE
            )
            # Store results in cache if sorting went well
            posts = self.post_sort_format(sorted_list)
        except Exception as err:
            log.exception("Failed to sort search results: %s", err)
        return posts

    def pre_sort_format(self, posts):
        if self.sort_by != "size":
            return posts
        for post in posts:
            post["size"] = human_to_bytes(post["size"])
        return posts

    def post_sort_format(self, posts):
        # Convert size B -> human readable (K, M, G)
        if self.sort_by != "size":
            return posts
        for el in posts:
            el["size"] = bytes_to_human(el["size"])
        return posts

    def download(self, url: str, tracker: str) -> str:
        return self.trackers[tracker].download(url)
