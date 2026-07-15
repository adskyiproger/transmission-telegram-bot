from unittest.mock import Mock

import pytest

from models.SearchBase import SearchBase


class Search(SearchBase):
    TRACKER_URL = "https://example.test"
    TRACKER_SEARCH_URL_TPL = "/search?q="


def test_search_term_is_url_encoded():
    search = Search(None, None)
    response = Mock(content=b"<html></html>")
    search._session = Mock()
    search._session.get.return_value = response

    search.get_data("a b&c")

    search._session.get.assert_called_once_with(
        "https://example.test/search?q=a%20b%26c", timeout=10
    )
    response.raise_for_status.assert_called_once()


def test_download_rejects_oversized_response(monkeypatch):
    search = Search(None, None)
    response = Mock(content=b"12345")
    search._session = Mock()
    search._session.get.return_value = response
    monkeypatch.setattr(
        "models.SearchBase.bot_config.get",
        lambda path, default=None: 4 if path == "bot.max_torrent_size" else default,
    )

    with pytest.raises(ValueError, match="size limit"):
        search.download("https://example.test/file.torrent")
