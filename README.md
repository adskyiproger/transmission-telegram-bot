# Transmission telegram bot

Telegram bot for Searching torrents and passing to Transmission torrent server.

## Features
1. Search torrents on web portals and passing to Transmission. (Today http://nnmclub.to/ is the only supporter tracer)
2. Direct send torrent files and magnet urls to transmission server for download.
3. Essentials Transmission server actions such as Stop, Start, Delete, View info.

#Usage
Please register new telegram bot using `BotFather`.
Place bot security token into torrents.ini.

## Preparation steps
1. Install and configure transmission server web interface with username and password.
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
