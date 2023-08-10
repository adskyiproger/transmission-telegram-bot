# Transmission telegram bot


This Telegram bot is a small piece of software for Searching torrents on tracker websites and passing to Transmission torrent server.

**Features:**

- **Manage** torrents on Transmission server:
  - Start, Stop, Delete and view torrents on transmission server
  - Select download folder before adding torrent to transmission
  - You could use built-in search option on list of predefined trackers or copy/paste torrent file, url or magnet link into the bot chat.
- **Search** torrents using bot:
  - Bot has pre-configured websites to find torrents
  - You can configure the way to display search results by changing sort and filter options. It will help you to find torrents with great number of seaders, or video content with better quality.
- **Authentication and Security**:
  - Bot uses built-in protection authentication verification. You don't have to worry about hacking.
  - You can easily share access to bot with family members using QR Code or link. Check `/adduser` command.

Features are independent of each other. E/g: If you would like to manage torrents only you could disable search and vice versa.

Additionally you could setup home DLNA server like Jellyfin, Plex or MiniDLNA and stream downloaded Video and Audio content to your smartTV, speakers, etc.

![image](doc/images/network-diagram.jpg)


**Supported trackers:**
* http://nnmclub.to/
* http://rutor.info 
* https://kat.sx/
* https://toloka.to

(new will arrive soon)

# Installation

## What you will need to run bot?
1. **Hardware:**
   - If you are planning to use Bot as standalone application for searching torrent and pushing them to external Transmission, no specific configuration is required.
   - If you are planning to run Bot and Transmission on the same hardware, make sure you have at least 2G of RAM and 100G+ storage. Actual setup takes less then 1G, but you will need place to download torrents.
   - Bot and transmission will run on any hardware architecture including Apple M1/2 chips and ARMs.
2. **Software:** 
   - Bot will work well on one of the following configuration:
      - Any Windows, Mac OS, Linux, FreeBSD OS/distribution with Python 3.10+. Bot may also run on any other operating system with Python 3.10+ support.
      - Any OS with support for Docker 20.0.4+ and docker-compose 3+.
   - Transmission, please check available packages at: https://transmissionbt.com/download or use one of the available docker images
   
   

## Preparation
1. Register new telegram bot using [@BotFather](https://t.me/botfather).
2. Configure Transmission server authentication with username and password:
   - For rpm or deb package use official doc: https://github.com/transmission/transmission/tree/main. Detailed setup instruction is [here](doc/Transmission-setup.md)
   - For docker image https://hub.docker.com/r/linuxserver/transmission please check `docker-compose.yaml` for available options.


## Run bot locally

1. Clone this repository
   ```
   git clone https://github.com/adskyiproger/transmission-telegram-bot.git
   ```
   or download as zip file: https://github.com/adskyiproger/transmission-telegram-bot/archive/refs/heads/master.zip
2. Update torrentino.yaml configuration file. Follow up comments inside configuration file:
   ```
   torrentino.yaml
   ```
3. Run:
   ```
   pip install --user pipenv
   pipenv install
   pipenv run ./torrentino.py
   ```

## Run in docker

1. Clone this repository
   ```
   git clone https://github.com/adskyiproger/transmission-telegram-bot.git
   ```
2. Update torrentino.yaml configuration file. Follow up comments inside configuration file:
   ```
   torrentino.yaml
   ```

3. Build docker image:
   ```
   docker build -t my-bot . 
   ```
4. Start docker container as daemon process:
   ```
   docker run -d -v `pwd`/torrentino.yaml:/usr/src/app/torrentino.yaml my-bot
   ```
5. Check container logs.



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



# Screenshots

## Bot Main window
- Last search results are available by pressing "Search" button.
- List of downloaded torrents is available by pressing "Torrents" button.

![image](doc/images/screen-0.png)

## Adding new user

After initial configuration new users can be added by typing `/adduser` command. As output you will get a registration link and QR-code.

![image](doc/images/screen-1.png)

