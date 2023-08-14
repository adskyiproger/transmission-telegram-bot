import configparser
import os
import yaml
import sys
import tempfile
import uuid
import logging
import logging.handlers
import qrcode
import pydash as _
import math

from functools import wraps
from tempfile import mkstemp
from lib.constants import LANGUAGE_FILE, DEFAULT_LANGUAGE, CONFIG_FILE


size_names = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]

lang = configparser.ConfigParser()
lang.read(LANGUAGE_FILE)

CONFIG = None


def load_config(config_file):
    if not os.path.isfile(config_file):
        print(f"Configuration file {config_file} not found.")
        sys.exit(1)
    with open(config_file, 'r') as config_file:
        return yaml.load(config_file, Loader=yaml.FullLoader)


def get_config():
    config = load_config(CONFIG_FILE)
    return config


def save_config():
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(CONFIG, f)


def trans(text, lang_code):
    """"""
    logging.debug(f"Translate: {text}, {lang_code}")
    return _.get(lang,
                 [lang_code, text],
                 _.get(lang,
                       [DEFAULT_LANGUAGE, text],
                       text))


def get_logger(class_name: str, log_level: str = None, log_file: str = None) -> logging.Logger:
    if not log_level:
        log_level = os.environ.get('log_level', "INFO").upper()
    # Configure telegram bot logging
    log_handlers=[ logging.StreamHandler(sys.stdout) ]
    if log_file:
        logging.info("Adding file handler: %s", log_file)
        # First run: create directory
        if not os.path.isdir(os.path.dirname(log_file)):
            os.makedirs(os.path.dirname(log_file))
        log_handlers.append(
            logging.handlers.RotatingFileHandler(filename = log_file,
                                                 maxBytes = (1048576*5),
                                                 backupCount = 1))
    logging.basicConfig( format = '[%(asctime)s] [%(levelname)s] %(name)s %(message)s',
                        level = logging.getLevelName(log_level),
                        handlers = log_handlers )
    # Silence for httpx
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    return logging.getLogger(class_name)


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
    size_bytes = int(size_bytes)
    if int(size_bytes) == 0:
        return "0B"
    try:
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return "%s%s" % (s, size_names[i])
    except TypeError as err:
        log.warning("Wrong value for conversion to bytes %s: %s", size_bytes, err)
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


CONFIG = load_config(CONFIG_FILE)
log = get_logger("function")
