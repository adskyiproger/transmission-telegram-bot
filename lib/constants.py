import os
from pathlib import Path

# Find bot root folder
BOT_FOLDER = str(Path(__file__).parent.parent)

# Configuration file
CONFIG_FILE = os.path.join(BOT_FOLDER, 'config', 'torrentino.yaml')

# Translation file
LANGUAGE_FILE = os.path.join(BOT_FOLDER, 'lib', 'torrentino.lang')
