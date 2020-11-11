#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Usage:
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import os, re, sys, threading, time
import tempfile
import logging
import logging.handlers
import configparser
from pathlib import Path
from models.TransmissionClient import TransmissionClient
from models.SearchTorrents import SearchTorrents
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
TORRENT_CLIENT = TransmissionClient(
                    host=os.getenv("TR_HOST", config['TRANSMISSION']['HOST'] ),
                    port=int(os.getenv("TR_PORT", config['TRANSMISSION']['PORT'])),
                    username=os.getenv("TR_USER", config['TRANSMISSION']['USER']),
                    password=os.getenv("TR_PASSWORD", config['TRANSMISSION']['PASSWORD'])
                    )
# Download directories
# Transmission server needs write access to these directories
reply_markup = InlineKeyboardMarkup( [[ InlineKeyboardButton(key.capitalize(),callback_data=config['DIRECTORIES'][key]) for key in config['DIRECTORIES'] ]] )

# Configure telegram bot logging
log_handlers=[ logging.StreamHandler(sys.stdout) ]
if config['BOT']['LOG_FILE']:
    log_handlers.append(logging.handlers.RotatingFileHandler(
                                        filename = config['BOT']['LOG_FILE'],
                                        maxBytes = (1048576*5),
                                        backupCount = 1,
                                        )
                       )
logging.basicConfig( format = '[%(asctime)s] [%(levelname)s]: %(name)s %(message)s',
                     level = logging.getLevelName(config['BOT']['LOG_LEVEL']),
                     handlers = log_handlers )


# Configure actions to work with torrent
TORRENT_ACTIONS=[
        "🔁️ List",
        "⏹ Stop All",
        "▶️ Start All"
        ]
torrent_reply_markup = ReplyKeyboardMarkup( [[InlineKeyboardButton(key) for key in TORRENT_ACTIONS]], resize_keyboard=True )


tracker_reply_markup = InlineKeyboardMarkup( [[InlineKeyboardButton(key, callback_data=key)] for key in SearchTorrents.CLASSES.keys()], resize_keyboard=True )

tracker_list="|".join(SearchTorrents.CLASSES.keys())

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
        if str(user_id) not in config['BOT']['ALLOWED_USERS'].split(','):
            context.bot.send_message(chat_id=user_id,text=trans("You are not authorized to use this bot. Please contact bot owner to get access.",L_CODE=update.message.from_user.language_code),parse_mode=ParseMode.HTML,reply_markup=torrent_reply_markup)
            logging.debug(update)
            logging.error("Unauthorized access denied for {}.".format(user_id))
            return
        return func(update, context, *args, **kwargs)
    return wrapped


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.

def help_command(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def start(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)
    logging.debug("echo: "+str(update))

def notifyOnDone(context,user_id,torrent_id,user_lang="en_US"):
    
    context.bot.send_message(chat_id=user_id,text=trans("I will notify you once download complete.",L_CODE=user_lang),parse_mode=ParseMode.HTML)
    while "seeding" != TORRENT_CLIENT.status(torrent_id):
        time.sleep(60)
        logging.debug("Torrent {0} is in status {1}".format(torrent_id,TORRENT_CLIENT.status(torrent_id)))

    _message=trans("Download completed",L_CODE=user_lang)+":\n"+TORRENT_CLIENT.info(int(torrent_id))

    # truncate long messages 
    _message = _message[:4000]+'..\n' if len(_message)>4000 else _message
    _message=_message+"--------------------------\n" \
            "[▶ /start_{0}] [⏹ /stop_{0}] [⏏ /delete_{0}]\n".format(torrent_id)
    try:        
        context.bot.send_message(chat_id=user_id,text=_message,parse_mode=ParseMode.HTML)
    except:
        context.bot.send_message(chat_id=user_id,text="Something went wrong, probably too many files in this torrent",parse_mode=ParseMode.HTML,reply_markup=torrent_reply_markup)



@restricted
def askDownloadDirFile(update, context):
    """Download file"""
    logging.debug(update)
    if update.message.document.mime_type == 'application/x-bittorrent':
        update.message.reply_text(trans('Please choose download folder for {}',update.message.from_user.language_code).format(update.message.document.file_name)+":", reply_markup=reply_markup)
        context.user_data['torrent']={'type':'torrent','file_name':update.message.document.file_name,'file_id':update.message.document.file_id}
    else:
        update.message.reply_text("Error: Unsupported mime type: \n"+
                    "File name: "+update.message.document.file_name+
                   "\nMime type: "+update.message.document.mime_type
                )

@restricted
def askDownloadDirURL(update, context):
    update.message.reply_text(trans('Please choose download folder for {}',update.message.from_user.language_code).format(update.message.text)+":", reply_markup=reply_markup)
    context.user_data['torrent']={'type':'url','url':update.message.text}

@restricted
def askDownloadMenuLink(update,context):
    _id=update.message.text.split("_")[1]
    update.message.reply_text(trans("Please choose download folder for {}",update.message.from_user.language_code).format(context.user_data['download_links'][_id])+":", reply_markup=reply_markup)
    context.user_data['torrent']={'type':'url','url':context.user_data['download_links'][_id]}
    logging.info("Added torrent URL to download list: {}".format(context.user_data['download_links'][_id]))

@restricted
def getMenuPage(update,context):
    logging.debug(update)
    query = update.callback_query
    query.answer()
    context.bot.edit_message_text(chat_id=update.callback_query.message.chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text=context.user_data['pages'][str(query.data)],
                                  parse_mode=ParseMode.HTML,
                                  reply_markup=context.user_data['pages_markup'],
                                  disable_web_page_preview=True)
 
@restricted
def processUserKey(update, context):
    logging.debug(update)
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    if context.user_data['torrent']['type'] == 'torrent':
       query.edit_message_text(text=trans("File {0} will be downloaded into {1}",query.from_user.language_code).format(context.user_data['torrent']['file_name'],str(query.data)))
       _file = context.bot.getFile(context.user_data['torrent']['file_id'])
       _file.download(tempfile.gettempdir()+os.path.sep+context.user_data['torrent']['file_name'])
       logging.debug("Torrent file {0} was downloaded into temporal directpry {1}".format(context.user_data['torrent']['file_id'],tempfile.gettempdir()+os.path.sep+context.user_data['torrent']['file_name']))
       with open(tempfile.gettempdir()+os.path.sep+context.user_data['torrent']['file_name'], 'rb') as f:
           TORRENT_CLIENT.add_torrent(f,download_dir=query.data)

       logging.info("File {0} will be placed into {1}".format(context.user_data['torrent']['file_name'],query.data))

    elif context.user_data['torrent']['type'] in [ 'magnet', 'url' ]:
       query.edit_message_text(text=trans("URL {0} will be downloaded into {1}.",query.from_user.language_code).format(context.user_data['torrent']['url'],query.data))
       TORRENT_CLIENT.add_torrent(context.user_data['torrent']['url'],download_dir=query.data)
       logging.info("URL {0} will be placed into {1}".format(context.user_data['torrent']['url'],query.data))
    _t=threading.Thread(target=notifyOnDone, args=(context,query.message.chat.id,TORRENT_CLIENT.get_torrents()[-1].id,query.from_user.language_code))
    _t.start()

@restricted
def askTrackerSelection(update,context):
    context.user_data['search_string']=update.message.text
    update.message.reply_text(trans('Please choose torrent tracker:',update.message.from_user.language_code)+":", reply_markup=tracker_reply_markup)


@restricted
def searchOnWebTracker(update, context):
    query = update.callback_query
    print(update)
    # if at least one page exist, add pager        
    SR=SearchTorrents(query.data,context.user_data['search_string'])
    context.user_data['pages']=SR.PAGES
    context.user_data['download_links']=SR.LINKS
    if len(context.user_data['pages'])>0:
        context.bot.send_message(chat_id=query.message.chat.id,parse_mode=ParseMode.HTML,text=context.user_data['pages']['1'],reply_markup=InlineKeyboardMarkup( [ SR.KEYBOARD ] ),disable_web_page_preview=True)
        context.user_data['pages_markup']=InlineKeyboardMarkup( [ SR.KEYBOARD ] )
    else:
        context.bot.send_message(chat_id=query.message.chat.id,
                                 text=trans('What would you like to do? Please choose actions from keyboard. You could also send torrent file or magnet link.',query.message.from_user.language_code),
                                 reply_markup=torrent_reply_markup)
    logging.debug(update)

@restricted
def torrentStop(update,context):
    """Stop torrent by torrent_id"""
    logging.debug(update)
    TORRENT_CLIENT.stop_torrent(int(update.message.text.split('_')[1]))

@restricted
def torrentStopAll(update,context):
    """Stop All Torrents"""
    TORRENT_CLIENT.stop_all()

@restricted
def torrentStart(update,context):
    """Start torrent by torrent_id"""
    logging.debug(update)
    TORRENT_CLIENT.start_torrent(int(update.message.text.split('_')[1]))

@restricted
def torrentStartAll(update,context):
    """Stop All Torrents"""
    TORRENT_CLIENT.start_all()

@restricted
def torrentList(update,context):
    """List all torrents on Transmission server"""
    _message=trans("Torrents list",update.message.from_user.language_code)+": \n"
    for torrent in TORRENT_CLIENT.get_torrents():
        _message=_message+"\n<b>{1}</b>  ℹ /info_{0} \n Progress: {2}% Status: {3} \n[▶ /start_{0}] [⏹ /stop_{0}] [⏏ /delete_{0}]\n".format(torrent.id,torrent.name,round(torrent.progress),torrent.status,torrent.format_eta())
    context.bot.send_message(chat_id=update.message.chat.id,text=_message,parse_mode=ParseMode.HTML,reply_markup=torrent_reply_markup)

@restricted
def torrentInfo(update,context):
    """Show detailed information about torrent"""
    logging.debug(update)
    torrent_id=update.message.text.split('_')[1]
    logging.info("Loading torrent id {0}".format(torrent_id))
    _message=TORRENT_CLIENT.info(int(torrent_id))
    # truncate long messages 
    _message = _message[:4000]+'..\n' if len(_message)>4000 else _message
    _message=_message+"--------------------------\n" \
            "[▶ /start_{0}] [⏹ /stop_{0}] [⏏ /delete_{0}]\n".format(torrent_id)
    try:        
        context.bot.send_message(chat_id=update.message.chat.id,text=_message,parse_mode=ParseMode.HTML,reply_markup=torrent_reply_markup)
    except:
        context.bot.send_message(chat_id=update.message.chat.id,text="Something went wrong, probably too many files in this torrent",parse_mode=ParseMode.HTML,reply_markup=torrent_reply_markup)

@restricted
def torrentDelete(update,context):
    """Remove torrent by torrent_id"""
    logging.debug(update)
    torrent_id=update.message.text.replace('/delete_', '')
    logging.info("Removing torrent id {0}".format(torrent_id))
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
    # Add Transmission handlers to dispatcher:
    dp.add_handler(MessageHandler(Filters.regex(r'List$'), torrentList))
    dp.add_handler(MessageHandler(Filters.regex(r'^/info_[0-9]+$'), torrentInfo))
    dp.add_handler(MessageHandler(Filters.regex(r'Stop All$'), torrentStopAll))
    dp.add_handler(MessageHandler(Filters.regex(r'Start All$'), torrentStartAll))
    dp.add_handler(MessageHandler(Filters.regex(r'^/stop_[0-9]+$'), torrentStop))
    dp.add_handler(MessageHandler(Filters.regex(r'^/start_[0-9]+$'), torrentStart))
    dp.add_handler(MessageHandler(Filters.regex(r'^/delete_[0-9]+$'), torrentDelete))
    # Add Search/Download/Navigation handlers to dispatcher
    dp.add_handler(CallbackQueryHandler(searchOnWebTracker,pattern=tracker_list))
    # Ask download directory for Menu URL 
    dp.add_handler(MessageHandler(Filters.regex(r'^/download_[0-9]+$'), askDownloadMenuLink))
    # Ask download directory for magnet/http(s) link
    dp.add_handler(MessageHandler(Filters.regex(r'(magnet:\?xt=urn:btih:[a-zA-Z0-9]*|[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*))'), askDownloadDirURL))
    # Ask download directory for torrent file
    dp.add_handler(MessageHandler(Filters.document, askDownloadDirFile))
    # Navigation buttons switcher (inline keyboard)
    dp.add_handler(CallbackQueryHandler(getMenuPage,pattern=r'^[0-9]+$'))
    # Select download folder switcher (inline keyboard)
    dp.add_handler(CallbackQueryHandler(processUserKey))
    # Default search input text
    dp.add_handler(MessageHandler(Filters.all, askTrackerSelection))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
