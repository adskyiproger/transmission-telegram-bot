import asyncio
import threading
from typing import Union, Dict, Any, BinaryIO
from copy import deepcopy
from telegram import Bot
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

    DOWNLOAD_QUEUE: Dict[str, Any] = {}
    QUEUE_LOCK = threading.Lock()

    def __init__(
        self,
        *,
        protocol: Literal["http", "https"] = "http",
        username: str | None = None,
        password: str | None = None,
        host: str = "127.0.0.1",
        port: int = 9091,
        path: str = "/transmission/",
        telegram_token: str | None = None,
    ):
        self.telegram_token = telegram_token
        super().__init__(
            protocol=protocol,
            username=username,
            password=password,
            host=host,
            port=port,
            path=path,
        )

    async def monitor_downloads(self, bot: Bot) -> None:
        """Periodically check downloads for the lifetime of the Telegram app."""
        log.info("Initializing scheduler")
        while True:
            await asyncio.sleep(QUEUE_CHECK_INTERVAL)
            if not TransmissionClient.DOWNLOAD_QUEUE:
                continue
            with TransmissionClient.QUEUE_LOCK:
                download_queue = deepcopy(TransmissionClient.DOWNLOAD_QUEUE)
            for torrent_id in download_queue.keys():
                try:
                    status = await asyncio.to_thread(self.status, torrent_id)
                    if not status.seeding:
                        continue
                except KeyError:
                    with TransmissionClient.QUEUE_LOCK:
                        TransmissionClient.DOWNLOAD_QUEUE.pop(torrent_id, None)
                    log.warning(
                        "Torrent %s doesn't exist on server, cleaning up download queue",
                        torrent_id,
                    )
                    continue
                with TransmissionClient.QUEUE_LOCK:
                    user = TransmissionClient.DOWNLOAD_QUEUE.get(torrent_id)
                if not user:
                    continue
                torrent = await asyncio.to_thread(
                    self.get_torrent, torrent_id=torrent_id
                )

                log.info("Download completed: %s %s", torrent.name, status.seeding)

                DownloadHistory.add(
                    torrent.done_date,
                    torrent.name,
                    torrent.download_dir,
                    torrent.size_when_done,
                )
                with TransmissionClient.QUEUE_LOCK:
                    TransmissionClient.DOWNLOAD_QUEUE.pop(torrent_id, None)
                message = trans("DOWNLOAD_COMPLETED", user["lang_code"]).format(
                    torrent.name
                )
                log.info(
                    "Sending message to user: %s, lang: %s, message: %s",
                    user["chat_id"],
                    user["lang_code"],
                    message,
                )
                await bot.send_message(chat_id=user["chat_id"], text=message)

    def add_torrent(
        self, chat_id, lang_code, torrent: Union[BinaryIO, str], **kwargs: Any
    ) -> Torrent:  # type: ignore[override]
        """Add torrent to transmission server"""
        _torrent = super().add_torrent(torrent, **kwargs)

        # Add torrent to download queue
        with TransmissionClient.QUEUE_LOCK:
            TransmissionClient.DOWNLOAD_QUEUE[_torrent.id] = {
                "chat_id": chat_id,
                "lang_code": lang_code,
            }

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
