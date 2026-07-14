from pathlib import Path

from transmission_rpc.utils import _try_read_torrent


def test_local_torrent_path_is_encoded_as_metainfo(tmp_path: Path):
    torrent = tmp_path / "download.torrent"
    torrent.write_bytes(b"torrent metainfo")

    encoded = _try_read_torrent(torrent)

    assert encoded is not None


def test_plain_local_path_string_is_misinterpreted_as_server_filename(
    tmp_path: Path,
):
    torrent = tmp_path / "download.torrent"
    torrent.write_bytes(b"torrent metainfo")

    assert _try_read_torrent(str(torrent)) is None
