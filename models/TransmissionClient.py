from transmission_rpc.client import Client
from transmission_rpc.lib_types import File
import logging
import os

logger = logging.getLogger(__name__)


class TransmissionClient(Client):
    def stop_all(self):
        for torrent in self.get_torrents():
            self.stop_torrent(torrent.id)
            logger.info("Stopped torrent {1} (id: {0})".format(torrent.id,torrent.name))

    def start_all(self):
        for torrent in self.get_torrents():
            self.start_torrent(torrent.id)
            logger.info("Started torrent {1} (id: {0})".format(torrent.id,torrent.name))

    def info(self,torrent_id):
        torrent=self.get_torrents(int(torrent_id))[0]
        _info=f"\n<b>{torrent.name}</b>:\n" \
            f"Progress: {round(torrent.progress)}% ETA: {torrent.format_eta()}  Status: {torrent.status}\n" \
            f"---------------------------\n"
        _info=_info+"Files:\n"
        for file_id, file in enumerate(torrent.files()):
            _info=_info+f"{file_id}: {file.name}: completed/size: {sizeof_fmt(file.completed)}/{sizeof_fmt(file.size)} Bytes \n"
        return _info


def sizeof_fmt(num, suffix='B'):
   for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
      if abs(num) < 1024.0:
         return "%3.1f%s%s" % (num, unit, suffix)
      num /= 1024.0
   return "%.1f%s%s" % (num, 'Yi', suffix)


