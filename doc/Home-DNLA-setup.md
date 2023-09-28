
# Home DLNA on Raspberry Pi4 setup guide

This section describes how to build home DLNA solution on Raspberry Pi4 with external HDD. 

## Hardware list:

1. Raspberry Pi4 device (4G RAM).
2. External HDD formatted as `ext4` (this guide use `/data/Media` as mountpoint). 

## Software list:

1. Docker with docker-compose. Guides how to setup docker and docker-compose could be found online.
2. Jellyfin docker imagei https://hub.docker.com/r/linuxserver/jellyfin (https://jellyfin.org/).
3. Transmission docker image https://hub.docker.com/r/linuxserver/transmission (https://transmissionbt.com/).
4. Transmission telegram bot docker image built from this repo.


## Installation steps

1. Create folders inside `/data/Media` to organize your data.
For example: Video, TVShows, Soft, Music.:
   ```
   mkdir -p /data/Media/{Video,TVShows,Soft,Music}
   ```
   **NOTE:** You are not limited to single directory and you can use existing folders. Check `directories` section in configuration file `torrentino.yaml`

2. Create dedicated user `dlna` for running docker containers and make this user owner of `/data/Media`:
   ```
   sudo useradd -m -G docker dlna
   sudo chown -R dlna:dnla /data/Media
   ```
3. Login as `dlna` user: 
   ```
   sudo su - dlna
   ```
4. Clone this git repo into home folder and build transmission-telegram-bot docker image:
   ```
   git clone https://github.com/adskyiproger/transmission-telegram-bot.git
   cd transmission-telegram-bot/
   docker build -t transmission-telegram-bot .
   ```
5. Navigate back into home directory and create directory structure to persist docker containers data:
   ```
   cd ~
   mkdir -p docker/{jellyfin,torrentino,transmission}/config
   ```
6. Copy Bot configuration file `torrentino.docker.yaml` into `~/docker/torrentino/config` and create empty log file:
   ```
   cp ~/transmission-telegram-bot/torrentino.docker.yaml ~/docker/torrentino/config/torrentino.yaml
   touch docker/torrentino/torrentino.log
   ```
7. Change owner, bot is running under non-root user and to get read/write access to `~/docker/torrentino/`, owner need to be changed to UID 2022 and GUID 2022:
   ```
   chown -R 2022:2022 ~/docker/torrentino/
   ```
8. Open `~/docker/torrentino/config/torrentino.yaml` in text editor and update `token`, `super_user` and `allowed_users` variables.
9. Copy docker-compose.yaml into `~/docker` directory
   ```
   cp ~/transmission-telegram-bot/docker-compose.yaml docker/
   ```
10. Update `PUID`, `PGID` variables. Please also update other variables that are not defaults.
11. Run everything:
   ```
   cd ~/docker
   docker-compose up -d
   ```
12. Login into Jellyfin web UI and configure DLNA folders.


### Environemnt description

* Jellyfin web interface is available at `http://<Pi4 hostname or ip>:8096`
* Transmission web interface is available at `http://<Pi4 hostname or ip>:9091`

