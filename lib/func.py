import configparser
import os
import yaml
import sys
from pathlib import Path
from functools import wraps
import logging
import logging.handlers
from telegram import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ParseMode


# Configure actions to work with torrent
TORRENT_ACTIONS=[
        "🔍 List",
        "⏹ Stop All",
        "▶️ Start All"
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
    if L_CODE in lang.sections():
        if STRING in lang[L_CODE]:
            STRING=lang[L_CODE][STRING]
    return STRING

def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if str(user_id) not in CONFIG['BOT']['ALLOWED_USERS'].split(','):
            context.bot.send_message(chat_id=user_id,
                                     text=trans("You are not authorized to use this bot. Please contact bot owner to get access.",update.message.from_user.language_code),
                                     parse_mode=ParseMode.HTML,
                                     reply_markup=torrent_reply_markup)
            logging.debug(update)
            logging.error("Unauthorized access denied for {}.".format(user_id))
            return
        return func(update, context, *args, **kwargs)
    return wrapped

def get_logger(class_name: str):
    log_level = os.environ.get('LOG_LEVEL', CONFIG['BOT']['LOG_LEVEL']).upper()
    # Configure telegram bot logging
    log_handlers=[ logging.StreamHandler(sys.stdout) ]
    if CONFIG['BOT']['LOG_FILE']:
        # First run: create directory
        if not os.path.isdir(os.path.dirname(CONFIG['BOT']['LOG_FILE'])):
            os.makedirs(os.path.dirname(CONFIG['BOT']['LOG_FILE']))
        log_handlers.append(logging.handlers.RotatingFileHandler(
                                            filename = CONFIG['BOT']['LOG_FILE'],
                                            maxBytes = (1048576*5),
                                            backupCount = 1,
                                            )
                        )
    logging.basicConfig( format = '[%(asctime)s] [%(levelname)s]: %(name)s %(message)s',
                        level = logging.getLevelName(log_level),
                        handlers = log_handlers )
    log = logging.getLogger(class_name)
    return log


CONFIG = load_config(str(Path(__file__).parent.parent) +str(os.path.sep)+ 'torrentino.yaml')