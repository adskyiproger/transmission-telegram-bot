import asyncio
import threading
import time

from copy import deepcopy
from telegram.ext import Application
from typing import Any, BinaryIO
from typing_extensions import Literal
from transmission_rpc.client import Client
from transmission_rpc.torrent import Torrent

from lib.func import trans, get_logger
from lib.constants import QUEUE_CHECK_INTERVAL

from models.DownloadHistory import DownloadHistory


log = get_logger("TransmissionClient")


class TransmissionClient(Client):
    """
    Features on top of transmission_rpc Client:
    - stop/start all torrents at once
    - get detailed information about torrent
    - notify user on torrent download done
    """

    DOWNLOAD_QUEUE = {}

    def __init__(self, *, protocol: Literal['http', 'https'] = "http",
                 username: str = None, password: str = None,
                 host: str = "127.0.0.1", port: int = 9091,
                 path: str = "/transmission/", telegram_token: str = None):
        self.telegram_token = telegram_token
        # Background thread for tracking torrent status
        download_status_monitor = threading.Thread(target=self._between_callback)
        download_status_monitor.start()

        super().__init__(protocol=protocol, username=username, password=password,
                         host=host, port=port, path=path)

    def _between_callback(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self._download_status_monitor())
        loop.close()

    async def _download_status_monitor(self):
        """Periodically check download queue"""
        log.info("Initializing scheduler")
        while True:
            time.sleep(QUEUE_CHECK_INTERVAL)
            if not TransmissionClient.DOWNLOAD_QUEUE:
                continue
            app = Application.builder().token(self.telegram_token).build()
            download_queue = deepcopy(TransmissionClient.DOWNLOAD_QUEUE)
            for torrent_id in download_queue.keys():
                status = self.status(torrent_id)
                if not status.seeding:
                    continue
                user = TransmissionClient.DOWNLOAD_QUEUE[torrent_id]
                torrent = self.get_torrent(torrent_id=torrent_id)

                log.info("Download completed: %s %s", torrent.name, status.seeding)

                DownloadHistory.add(torrent.date_done, torrent.name, torrent.download_dir, torrent.size_when_done)
                del TransmissionClient.DOWNLOAD_QUEUE[torrent_id]
                log.info("User: %s, language: %s", user["chat_id"], user["lang_code"])
                await app.bot.send_message(chat_id=user["chat_id"], text=trans("DOWNLOAD_COMPLETED", user["lang_code"]).format(torrent.name))

    def add_torrent(self, chat_id, lang_code, torrent: BinaryIO | str, **kwargs: Any) -> Torrent:
        """Add torrent to transmission server"""
        _torrent = super().add_torrent(torrent, **kwargs)

        # Add torrent to download queue
        TransmissionClient.DOWNLOAD_QUEUE[_torrent.id] = {"chat_id": chat_id,
                                                          "lang_code": lang_code}

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
        return self.get_torrent(int(torrent_id)).status
