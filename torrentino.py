#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Usage:
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import os, re
import tempfile
import logging
import configparser
from pathlib import Path
from functools import wraps

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, InlineQueryHandler
from telegram import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ParseMode
from transmission_rpc.client import Client
from transmission_rpc.lib_types import File

lang = configparser.ConfigParser()
lang.read(str(Path(__file__).parent) +str(os.path.sep)+ 'torrentino.lang')
# Read configuration file, torrentino.ini
# File is in the same directory as script
config = configparser.ConfigParser()
config.read(str(Path(__file__).parent) +str(os.path.sep)+ 'torrentino.ini')
# Telegram bot token
BOT_TOKEN=config['BOT']['TOKEN']
# Client connection to Transmission torrent server
# User environment variables or defaults from configuration file
TORRENT_CLIENT = Client(
                    host=os.getenv("TR_HOST", config['TRANSMISSION']['HOST'] ),
                    port=int(os.getenv("TR_PORT", config['TRANSMISSION']['PORT'])),
                    username=os.getenv("TR_USER", config['TRANSMISSION']['USER']),
                    password=os.getenv("TR_PASSWORD", config['TRANSMISSION']['PASSWORD'])
                    )
# Download directories
# Transmission server needs write access to these directories
reply_markup = InlineKeyboardMarkup( [[ InlineKeyboardButton(key.capitalize(),callback_data=config['DIRECTORIES'][key]) for key in config['DIRECTORIES'] ]] )

# Configure telegram bot logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configure actions to work with torrent
TORRENT_ACTIONS=[
        "🔁️ List",
        "⏹ Stop All",
        "▶️ Start All"
        ]
torrent_reply_markup = ReplyKeyboardMarkup( [[InlineKeyboardButton(key) for key in TORRENT_ACTIONS]], resize_keyboard=True )

def trans(STRING,L_CODE):
    if L_CODE in lang.sections():
        if STRING in lang[L_CODE]:
            STRING=lang[L_CODE][STRING]
    return STRING

def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if str(user_id) not in config['BOT']['ALLOWED_USERS'].split(','):
            context.bot.send_message(chat_id=user_id,text=trans("You are not authorized to use this bot. Please contact bot owner to get access.",L_CODE=update.message.from_user.language_code),parse_mode=ParseMode.HTML,reply_markup=torrent_reply_markup)
            logger.debug(update)
            logger.error("Unauthorized access denied for {}.".format(user_id))
            return
        return func(update, context, *args, **kwargs)
    return wrapped
# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.

def help_command(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)
    logger.debug("echo: "+str(update))

@restricted
def askDownloadDirFile(update, context):
    """Download file"""
    logger.debug(update)
    if update.message.document.mime_type == 'application/x-bittorrent':
        update.message.reply_text(trans('Please choose destination folder',update.message.from_user.language_code)+":", reply_markup=reply_markup)
        context.user_data['torrent']={'type':'torrent','file_name':update.message.document.file_name,'file_id':update.message.document.file_id}
    else:
        update.message.reply_text("Error: Unsupported mime type: \n"+
                    "File name: "+update.message.document.file_name+
                   "\nMime type: "+update.message.document.mime_type
                )

@restricted
def askDownloadDirMagnet(update, context):
    update.message.reply_text(trans('Please choose destination folder',update.message.from_user.language_code)+":", reply_markup=reply_markup)
    context.user_data['torrent']={'type':'magnet','url':update.message.text}

@restricted
def processUserKey(update, context):
    logger.debug(update)
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    if context.user_data['torrent']['type'] == 'torrent':
        #query.edit_message_text(text="File: "+context.user_data['torrent']['file_name']+" will be downloaded into "+str(query.data))
        query.edit_message_text(text=trans("File {0} will be downloaded into {1}",query.from_user.language_code).format(context.user_data['torrent']['file_name'],str(query.data)))
        _file = context.bot.getFile(context.user_data['torrent']['file_id'])
        _file.download(tempfile.gettempdir()+os.path.sep+context.user_data['torrent']['file_name'])
        logger.debug("Torrent file {0} was downloaded into temporal directpry {1}".format(context.user_data['torrent']['file_id'],tempfile.gettempdir()+os.path.sep+context.user_data['torrent']['file_name']))
        with open(tempfile.gettempdir()+os.path.sep+context.user_data['torrent']['file_name'], 'rb') as f:
            TORRENT_CLIENT.add_torrent(f,download_dir=query.data)

        logger.info("File {0} will be placed into {1}".format(context.user_data['torrent']['file_name'],query.data))

    elif context.user_data['torrent']['type'] == 'magnet':
        query.edit_message_text(text="Magnet URL "+context.user_data['torrent']['url']+" will be downloaded into "+str(query.data))
        TORRENT_CLIENT.add_torrent(context.user_data['torrent']['url'],download_dir=query.data)
        logger.info("Magnet URL {0} will be placed into {1}".format(context.user_data['torrent']['url'],query.data))
    else:
        logger.error("Something went wrong, please check debug output.")
        logger.debug(context)
        logger.debug(update)

def hell(update, context):
    update.message.reply_text(trans('What would you like to do? Please choose actions from keyboard. You could also send torrent file or magnet link.',update.message.from_user.language_code))
    logger.debug(update)

@restricted
def torrentStop(update,context):
    """Stop torrent by torrent_id"""
    logger.debug(update)
    if re.match(r'/stop_',update.message.text):
        torrent_id=update.message.text.replace('/stop_', '')
        logger.info("Stopping torrent id {0}".format(torrent_id))
        TORRENT_CLIENT.stop_torrent(int(torrent_id))
    else:
        for torrent in TORRENT_CLIENT.get_torrents():
            TORRENT_CLIENT.stop_torrent(torrent.id)
            logger.info("Stopped torrent {1} (id: {0})".format(torrent.id,torrent.name))

@restricted
def torrentStart(update,context):
    """Start torrent by torrent_id"""
    logger.debug(update)
    if re.match(r'/start_',update.message.text):
        torrent_id=update.message.text.replace('/start_', '')
        logger.info("Starting torrent id {0}".format(torrent_id))
        TORRENT_CLIENT.start_torrent(int(torrent_id))
    else:
        for torrent in TORRENT_CLIENT.get_torrents():
            TORRENT_CLIENT.start_torrent(torrent.id)
            logger.info("Started torrent {1} (id: {0})".format(torrent.id,torrent.name))

@restricted
def torrentStartStop(update,context):
    """Start/Stop torrent by torrent_id"""
    logger.debug(update)
    torrent_id=update.message.text.replace('/start_stop_', '')
    if TORRENT_CLIENT.get_torrents(int(torrent_id))[0].status == 'seeding':
        TORRENT_CLIENT.stop_torrent(int(torrent_id))
    else:
        TORRENT_CLIENT.start_torrent(int(torrent_id))

@restricted
def torrentList(update,context):
    """List all torrents on Transmission server"""
    _message=trans("Torrents list",update.message.from_user.language_code)+": \n"
    for torrent in TORRENT_CLIENT.get_torrents():
        _message=_message+"\n<b>{1}</b>  ℹ /info_{0} \n Progress: {2}% Status: {3} \n[ ▶ /start_{0} ] [ ⏹ /stop_{0} ] [ ⏏  /delete_{0} ]\n".format(torrent.id,torrent.name,torrent.progress,torrent.status,torrent.format_eta())
    context.bot.send_message(chat_id=update.message.chat.id,text=_message,parse_mode=ParseMode.HTML,reply_markup=torrent_reply_markup)

@restricted
def torrentInfo(update,context):
    """Show detailed information about torrent"""
    logger.debug(update)
    torrent_id=update.message.text.replace('/info_', '')
    logger.info("Loading torrent id {0}".format(torrent_id))
    _message=""
    torrent=TORRENT_CLIENT.get_torrents(int(torrent_id))[0]
    _message=f"\n<b>{torrent.name}</b>:\n" \
            f"Progress: {torrent.progress}% ETA: {torrent.format_eta()}  Status: {torrent.status}\n" \
            f"---------------------------\n"
    _message=_message+"Files:\n"
    for file_id, file in enumerate(torrent.files()):
        _message=_message+f"{file_id}: {file.name}: completed/size: {file.completed}/{file.size} Bytes \n"
    _message=_message+"--------------------------\n" \
            "[ ▶ /start_{0} ] [ ⏹ /stop_{0} ] [ ⏏ /delete_{0} ]\n".format(torrent.id)
    context.bot.send_message(chat_id=update.message.chat.id,text=_message,parse_mode=ParseMode.HTML,reply_markup=torrent_reply_markup)

@restricted
def torrentDelete(update,context):
    """Remove torrent by torrent_id"""
    logger.debug(update)
    torrent_id=update.message.text.replace('/delete_', '')
    logger.info("Removing torrent id {0}".format(torrent_id))
    context.bot.send_message(chat_id=update.message.chat.id,text=trans("Torrent {0} was removed from Transmission server".format(TORRENT_CLIENT.get_torrents(int(torrent_id))[0].name),update.message.from_user.language_code),parse_mode=ParseMode.HTML,reply_markup=torrent_reply_markup)
    TORRENT_CLIENT.remove_torrent(int(torrent_id),delete_data=config['TRANSMISSION']['DELETE_DATA'])


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(BOT_TOKEN, use_context=True)
    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    # list torrents
    dp.add_handler(MessageHandler(Filters.regex(r'List'), torrentList))
    dp.add_handler(MessageHandler(Filters.regex(r'/info'), torrentInfo))
    dp.add_handler(MessageHandler(Filters.regex(r'Stop All'), torrentStop))
    dp.add_handler(MessageHandler(Filters.regex(r'Start All'), torrentStart))
    dp.add_handler(MessageHandler(Filters.regex(r'/start_stop'), torrentStartStop))
    dp.add_handler(MessageHandler(Filters.regex(r'/stop_'), torrentStop))
    dp.add_handler(MessageHandler(Filters.regex(r'/start_'), torrentStart))
    dp.add_handler(MessageHandler(Filters.regex(r'/delete'), torrentDelete))
    # Process magnet link
    dp.add_handler(MessageHandler(Filters.regex(r'(magnet:\?xt=urn:btih:[a-zA-Z0-9]*)'), askDownloadDirMagnet))
    # Process file
    dp.add_handler(MessageHandler(Filters.document, askDownloadDirFile))
    # Process Button
    dp.add_handler(CallbackQueryHandler(processUserKey))
    # Default action
    dp.add_handler(MessageHandler(Filters.all, hell))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
