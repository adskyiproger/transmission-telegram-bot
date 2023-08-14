"""
File is used to store constants user withing code
"""

import os
from pathlib import Path

# Find bot root folder
BOT_FOLDER = str(Path(__file__).parent.parent)

# Configuration file
CONFIG_FILE = os.path.join(BOT_FOLDER, 'config', 'torrentino.yaml')

# Translation file
LANGUAGE_FILE = os.path.join(BOT_FOLDER, 'lib', 'torrentino.lang')

# Use this language if client language doesn't mach with any of
# supported languages
DEFAULT_LANGUAGE = "en"

# How often check status of torrents on transmissions,
# Variable is used to send notification to user
# about completed downloads
QUEUE_CHECK_INTERVAL = 60

# Number of posts per page to display user while
# browsing torrent, search results, download history, etc
POSTS_PER_PAGE = 5
