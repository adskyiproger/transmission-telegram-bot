# torrentino

Telegram bot for Transmission torrent server.

Please register new telegram bot using `BotFather`.
Place bot security token into torrents.ini.

## Preparation steps
1. Install and configure transmission server web interface with username and password.
2. Update torrentino.ini configuration file.


## Run in docker

1. Build docker image:
   ```
   docker build -t torrentino . 
   ```
2. Start docker container as daemon process:
   ```
   docker run -d -v `pwd`/torrentino.ini:/usr/src/app/torrentino.ini torrentino
   ```
3. Check container logs.
