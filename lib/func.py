import configparser
import os
import yaml
import sys
import tempfile
import uuid
from pathlib import Path
from functools import wraps
from tempfile import mkstemp
import logging
import logging.handlers
from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram.constants import ParseMode
import qrcode
import pydash as _
import math

size_names = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]

# Configure actions to work with torrent
TORRENT_ACTIONS=[
        "🔍 List",
       # "⏹ Stop All",
       # "▶️ Start All"
        ]
torrent_reply_markup = ReplyKeyboardMarkup( [[KeyboardButton(text=str(key)) for key in TORRENT_ACTIONS]], resize_keyboard=True )


lang = configparser.ConfigParser()
lang.read(str(Path(__file__).parent.parent) +str(os.path.sep)+ 'torrentino.lang')

CONFIG = None


def load_config(config_file):
    if not os.path.isfile(config_file):
        print(f"Configuration file {config_file} not found.")
        sys.exit(1)
    with open(config_file, 'r') as config_file:
        CONFIG = yaml.load(config_file, Loader=yaml.FullLoader)
        return CONFIG

def get_config():
    CONFIG = load_config(str(Path(__file__).parent.parent) +str(os.path.sep)+ 'torrentino.yaml')
    return CONFIG

def sizeof_fmt(num, suffix='B'):
   for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
      if abs(num) < 1024.0:
         return "%3.1f%s%s" % (num, unit, suffix)
      num /= 1024.0
   return "%.1f%s%s" % (num, 'Yi', suffix)

def trans(STRING,L_CODE):
    logging.debug(f"Translate: {STRING}, {L_CODE}")
    if L_CODE in lang.sections():
        if STRING in lang[L_CODE]:
            STRING=lang[L_CODE][STRING]
    else:
        if STRING in lang["en"]:
            STRING = lang["en"][STRING]
    return STRING


def save_config():
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(CONFIG, f)


def adduser(id):
    if id not in CONFIG['bot']['allowed_users']:
        CONFIG['bot']['allowed_users'].append(id)
        save_config()


def restricted(func):
    @wraps(func)
    async def wrapped(update, context, *args, **kwargs):
        
        user_id = update.effective_user.id

        if 'super_user' not in CONFIG['bot'] or CONFIG['bot']['super_user'] == '':
            logging.warn(f"Adding new super user {user_id}")
            CONFIG['bot']['super_user'] = user_id
            save_config()
        elif user_id not in CONFIG['bot']['allowed_users']:
            logging.info(f"{user_id} != {CONFIG['bot']['allowed_users']}")
            context.bot.send_message(chat_id=user_id,
                                     text=trans('ACCESS_RESTRICTED', update.message.from_user.language_code),
                                     parse_mode=ParseMode.HTML,
                                     reply_markup=torrent_reply_markup)
            logging.debug(update)
            logging.error("Unauthorized access denied for {}.".format(user_id))
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

def get_logger(class_name: str) -> logging.Logger:
    log_level = os.environ.get('log_level', CONFIG['bot']['log_level']).upper()
    # Configure telegram bot logging
    log_handlers=[ logging.StreamHandler(sys.stdout) ]
    if CONFIG['bot']['log_file']:
        # First run: create directory
        if not os.path.isdir(os.path.dirname(CONFIG['bot']['log_file'])):
            os.makedirs(os.path.dirname(CONFIG['bot']['log_file']))
        log_handlers.append(logging.handlers.RotatingFileHandler(
                                            filename = CONFIG['bot']['log_file'],
                                            maxBytes = (1048576*5),
                                            backupCount = 1,
                                            )
                        )
    logging.basicConfig( format = '[%(asctime)s] [%(levelname)s] %(name)s %(message)s',
                        level = logging.getLevelName(log_level),
                        handlers = log_handlers )
    # Silence for httpx
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    log = logging.getLogger(class_name)
    return log


def get_qr_code(input_data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(input_data)
    qr.make(fit=True)
    img_file = mkstemp()[1]
    log.debug(f"Temporal file created: {img_file}")
    img = qr.make_image(fill='black', back_color='white')
    img.save(img_file)
    return img_file


def bytes_to_human(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0B"
    try:
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return "%s%s" % (s, size_names[i])
    except TypeError:
        return size_bytes


def save_file(path: str, content: bytes):
    with open(path, 'wb') as f:
        f.write(content)
    return path

def save_torrent_to_tempfile(content: bytes) -> str:
    """Save torrent as temporal file and return full file path"""
    temp_file = os.path.join(tempfile.gettempdir(),           # Temporal directory
                             str(uuid.uuid4()) + ".torrent")  # Random file name
    with open(temp_file, 'wb') as f:
        f.write(content)
    log.info("Temporal file path: %s, size: %s",
             temp_file,
             bytes_to_human(os.path.getsize(temp_file)))

    return temp_file


def human_to_bytes(size_human: str) -> int:
    try:
        size, size_name = size_human[:-2], size_human[-2:]
        if size_name in size_names:
            i = size_names.index(size_name)
            p = math.pow(1024, i)
            return int(float(size) * p )
    except TypeError:
        return size_human


CONFIG_FILE = str(Path(__file__).parent.parent) +str(os.path.sep)+ 'torrentino.yaml'
CONFIG = load_config(CONFIG_FILE)
log = get_logger("function")
