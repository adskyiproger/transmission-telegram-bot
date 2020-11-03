# Transmission telegram bot

Telegram bot for Searching torrents and passing to Transmission torrent server.

## Features
1. Search torrents on web portals and passing to Transmission. (Today http://nnmclub.to/ is the only supported torrent tracker, but new will arrive soon)
2. Direct send torrent files and magnet urls to transmission server for download.
3. Essentials Transmission server actions such as Stop, Start, Delete, View info.

#Usage
Please register new telegram bot using `BotFather`.
Place bot security token into torrents.ini.

## Preparation steps
1. Install and configure transmission server web interface with username and password. You could use docker image https://hub.docker.com/r/linuxserver/transmission instead of manual (rpm/deb) setup.
2. Update torrentino.ini configuration file.


## Run in docker

1. Build docker image:
   ```
   docker build -t my-bot . 
   ```
2. Start docker container as daemon process:
   ```
   docker run -d -v `pwd`/torrentino.ini:/usr/src/app/torrentino.ini my-bot
   ```
3. Check container logs.


# `torrentino.ini` Configuration options

```
[BOT]
# TOKEN, Use BotFather to create new token
TOKEN=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# Your telegram ID
ALLOWED_USERS=XXXXXXXXXX

[TRANSMISSION]
# HOST, Transmission server host
HOST=192.168.88.225
# PORT, Transmission server port
PORT=9091
# USER, Transmission server user name
USER=test
# PASSWORD, Transmission server user password
PASSWORD=test
# DELETE_DATA, delete torrent from transmission and remove data from file system
DELETE_DATA=True

[DIRECTORIES]
# List names and file system path to directories on Transmission server
Video=/data/Media/Video
TVShows=/data/Media/TVShows
Music=/data/Media/Music
Soft=/data/Media/Soft
```
