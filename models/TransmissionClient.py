import asyncio
import threading
import time
from copy import deepcopy
from telegram.ext import Application
from typing import Any, BinaryIO
from typing_extensions import Literal
from transmission_rpc.client import Client
from transmission_rpc.lib_types import _Timeout
import logging
from logging import Logger
from transmission_rpc.torrent import Torrent


log = logging.getLogger(__name__)


class TransmissionClient(Client):
    """
    Features on top of transmission_rpc Client:
    - stop/start all torrents at once
    - get detailed information about torrent
    - notify user on torrent download done
    """

    DOWNLOAD_QUEUE = {}
    QUEUE_CHECK_INTERVAL = 60

    def __init__(self, *, protocol: Literal['http', 'https'] = "http",
                 username: str = None, password: str = None,
                 host: str = "127.0.0.1", port: int = 9091,
                 path: str = "/transmission/", timeout: int | float = 30,
                 logger: Logger = log, telegram_token: str = None):
        self.telegram_token = telegram_token
        # Background thread for tracking torrent status
        _thread = threading.Thread(target=self._between_callback)
        _thread.start()

        super().__init__(protocol=protocol, username=username, password=password,
                         host=host, port=port, path=path, timeout=timeout, logger=logger)

    def _between_callback(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self._notifier())
        loop.close()

    async def _notifier(self):
        """Periodically check download queue"""
        log.info("Initializing scheduler")
        while True:
            time.sleep(TransmissionClient.QUEUE_CHECK_INTERVAL)
            if not TransmissionClient.DOWNLOAD_QUEUE:
                continue
            app = Application.builder().token(self.telegram_token).build()
            download_queue = deepcopy(TransmissionClient.DOWNLOAD_QUEUE)
            for torrent_id, chat_id in download_queue.items():
                status = self.status(torrent_id)
                if not status.seeding:
                    continue

                name = self.get_torrent(torrent_id=torrent_id).name
                log.info("Download completed: %s %s", name, status.seeding)
                del TransmissionClient.DOWNLOAD_QUEUE[torrent_id]
                await app.bot.send_message(chat_id=chat_id, text=f"Download completed: {name}")

    def add_torrent(self, chat_id, torrent: BinaryIO | str, timeout: _Timeout = None, **kwargs: Any) -> Torrent:
        """Add torrent to transmission server"""
        _torrent = super().add_torrent(torrent, timeout, **kwargs)

        # Add torrent to download queue
        TransmissionClient.DOWNLOAD_QUEUE[_torrent.id] = chat_id

        return _torrent

    def stop_all(self) -> None:
        """Stop all torrent on server"""
        for torrent in self.get_torrents():
            self.stop_torrent(torrent.id)
            log.info("Stopped torrent %s (id: %s)", torrent.id, torrent.name)

    def start_all(self) -> None:
        """Start all torrent on server"""
        for torrent in self.get_torrents():
            self.start_torrent(torrent.id)
            log.info("Started torrent %s (id: %s)", torrent.id, torrent.name)

    def status(self, torrent_id):
        return self.get_torrents(int(torrent_id))[0].status

    def info(self, torrent_id: str) -> str:
        """Information about torrent (status per file)"""
        torrent = self.get_torrents(int(torrent_id))[0]
        _info = f"\n<b>{torrent.name}</b>:\n" \
                f"Progress: {round(torrent.progress)}% ETA: {torrent.format_eta()}  Status: {torrent.status}\n" \
                "---------------------------\n" \
                "Files:\n"
        for file in torrent.files():
            _info += f"{file.name}: completed/size: {sizeof_fmt(file.completed)}/{sizeof_fmt(file.size)} Bytes \n"
        return _info


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
