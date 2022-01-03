#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Usage:
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
from math import ceil
import os
import threading
import time
import copy
import tempfile
import random
import string
from models.TransmissionClient import TransmissionClient
from models.SearchTorrents import SearchTorrents

from lib.func import restricted, \
                     trans, get_config, get_logger, \
                     get_qr_code, adduser

from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler
from telegram import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ParseMode

# Read configuration file, torrentino.ini
# File is in the same directory as script
config = get_config()

# Telegram bot token
BOT_TOKEN = config['BOT']['TOKEN']
# Client connection to Transmission torrent server
# User environment variables or defaults from configuration file
TORRENT_CLIENT = TransmissionClient(
                    host=os.getenv("TR_HOST", config['TRANSMISSION']['HOST'] ),
                    port=int(os.getenv("TR_PORT", config['TRANSMISSION']['PORT'])),
                    username=os.getenv("TR_USER", config['TRANSMISSION']['USER']),
                    password=os.getenv("TR_PASSWORD", config['TRANSMISSION']['PASSWORD'])
                    )
# Mockup:
# TORRENT_CLIENT = None

# Download directories
# Transmission server needs write access to these directories
reply_markup = InlineKeyboardMarkup( [[ InlineKeyboardButton(key.capitalize(), callback_data=config['DIRECTORIES'][key]) for key in config['DIRECTORIES'] ]] )

# This variable is used to auth new users
WELCOME_HASHES = []

logging = get_logger(__file__)


# Configure actions to work with torrent
TORRENT_ACTIONS=[
        "📁 Torrents",
        "🔍 Search",
        # "⏹ Stop All",
        # "▶️ Start All"
        ]
torrent_reply_markup = ReplyKeyboardMarkup( [[KeyboardButton(text=str(key)) for key in TORRENT_ACTIONS]], resize_keyboard=True )


# tracker_reply_markup = InlineKeyboardMarkup( [[InlineKeyboardButton(key, callback_data=key)] for key in SearchTorrents.CLASSES.keys()], resize_keyboard=True )

tracker_list="|".join(SearchTorrents.CLASSES.keys())

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.

def help_command(update, context):
    """Send a message when the command /help is issued."""
    HELP = trans("HELP",update.message.from_user.language_code)
    if update.message.chat.id == config['BOT']['SUPER_USER']:
        HELP += "\n"+trans("HELP_ADMIN",update.message.from_user.language_code)
    context.bot.send_message(chat_id=update.message.chat.id, text=HELP, parse_mode=ParseMode.HTML)


def start(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)
    logging.debug("echo: "+str(update))


def notifyOnDone(context,user_id, torrent_id, user_lang="en_US"):
    context.bot.send_message(chat_id=user_id,
                             text=trans("I will notify you once download complete.",user_lang),
                             parse_mode=ParseMode.HTML)
    while "seeding" != TORRENT_CLIENT.status(torrent_id):
        time.sleep(60)
        logging.debug(f"Torrent {torrent_id} is in status {TORRENT_CLIENT.status(torrent_id)}")
    _message = trans("Download completed", L_CODE=user_lang)+":\n"+TORRENT_CLIENT.info(int(torrent_id))
    # truncate long messages 
    _message = _message[:4000]+'..\n' if len(_message)>4000 else _message
    _message = _message+"--------------------------\n" \
            "[▶ /start_{0}] [⏹ /stop_{0}] [⏏ /delete_{0}]\n".format(torrent_id)
    context.bot.send_message(chat_id=user_id, text=_message, parse_mode=ParseMode.HTML)


@restricted
def askDownloadDirFile(update, context):
    """Download file"""
    logging.debug(update)
    logging.info(f"Searching for download file dir")
    if update.message.document.mime_type == 'application/x-bittorrent':
        update.message.reply_text(trans('Please choose download folder for {}',update.message.from_user.language_code).format(update.message.document.file_name)+":", reply_markup=reply_markup)
        context.user_data['torrent']={'type':'torrent','file_name':update.message.document.file_name,'file_id':update.message.document.file_id}
    else:
        update.message.reply_text("Error: Unsupported mime type: \n"+
                    f"File name: {update.message.document.file_name}"+
                    f"\nMime type: {update.message.document.mime_type}")


@restricted
def askDownloadDirURL(update, context):
    """
    Ask download directory for Magnet URL.
    Next step: 
    """
    logging.info(f"Downloading URL {update.message.text}")
    update.message.reply_text(trans('CHOOSE_DOWNLOAD_DIR',
                                    update.message.from_user.language_code).format(update.message.text)+":",
                              reply_markup=reply_markup)
    context.user_data['torrent']={'type':'url', 'url':update.message.text}


@restricted
def askDownloadDirPageLink(update,context):
    logging.info(f"Downloading page link {update.message.text}")
    _id=int(update.message.text.split("_")[1])
    update.message.reply_text(trans('CHOOSE_DOWNLOAD_DIR',update.message.from_user.language_code).format(context.user_data['posts'][_id]['dl'])+":", reply_markup=reply_markup)
    context.user_data['torrent']={'type':'url','url':context.user_data['posts'][_id]['dl']}
    logging.info("Added torrent URL to download list: {}".format(context.user_data['posts'][_id]['dl']))


@restricted
def getMenuPage(update, context):
    # logging.debug(update)
    query = update.callback_query
    query.answer()
    page = query.data
    try:
        if str(query.data) != 'x':
            context.bot.edit_message_text(chat_id=update.callback_query.message.chat_id,
                                          message_id=update.callback_query.message.message_id,
                                          text=getPage(context, int(page), query.from_user.language_code),
                                          parse_mode=ParseMode.HTML,
                                          reply_markup=getKeyboard(context, page),
                                          disable_web_page_preview=True)
        else:
            logging.warn("You are trying to click the same page")
    except ValueError as err:
        logging.error(f"Wrong menu page {page}: {err}")


@restricted
def lastSearchResults(update, context):
    if 'posts' in context.user_data:
        update.message.reply_text(text=getPage(context, user_lang=update.message.from_user.language_code),
                reply_markup=getKeyboard(context),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True)
    else:
        context.bot.send_message(chat_id=update.message.chat.id,
                            text=trans('NO_SEARCH_RESULTS', update.message.from_user.language_code),
                            reply_markup=torrent_reply_markup)

def getNumPages(context):
    num_pages = int(len(context.user_data['posts']) /5 )
    if len(context.user_data['posts']) % 5 > 0:
        num_pages += 1
    return num_pages

def getPage(context, _page=1, user_lang="en"):
    page = int(_page)
    _message=trans("NAV_HEADER", user_lang).format(page, getNumPages(context))
    # Add first and last posts index
    first, last = ( page * 5 ) - 5, page * 5
    ii = first
    for post in context.user_data['posts'][first:last]:
        _message += f"\n<b>{post['title']}</b>: {post['size']}  {post['date']}\n<a href='{post['info']}'>Info</a>     [ ▼ /download_{ii} ]\n"
        ii += 1
    return _message


def getKeyboard(context, _page=1):
    pages = getNumPages(context)
    page = int(_page)
    # Edge case for first page
    if page == 1 or page < 4:
        KEYBOARD=[InlineKeyboardButton(str(jj), callback_data=str(jj)) for jj in range(1, 8) if jj < pages]
    # Edge case for last page
    elif pages - page < 4:
        KEYBOARD=[InlineKeyboardButton(str(jj), callback_data=str(jj)) for jj in range(pages - 6, pages + 1) if jj <= pages]
    # Regular navigation
    else:
        KEYBOARD=[InlineKeyboardButton(str(jj), callback_data=str(jj)) for jj in range(page - 3, page + 4) if jj <= pages]
    
    FOOTER_KEYS = []
    if page > 10:
        FOOTER_KEYS.append(InlineKeyboardButton("«« -10", callback_data=str(page-10)))
    if pages > page + 10:
        FOOTER_KEYS.append(InlineKeyboardButton("+10 »»", callback_data=str(page+10)))

    for key in KEYBOARD:
        print(key)
        if str(key.text) == str(page):
            key.text = "..."
            key.callback_data="x"
    
    return InlineKeyboardMarkup( [ KEYBOARD, FOOTER_KEYS ] )


@restricted
def processUserKey(update, context):
    logging.debug(update)
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    if context.user_data['torrent']['type'] == 'torrent':
       query.edit_message_text(text=trans('FILE_WILL_BE_DOWNLOADED', 
                                          query.from_user.language_code).format(context.user_data['torrent']['file_name'],
                                                                                str(query.data)))
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


# @restricted
# def askTrackerSelection(update,context):
#    context.user_data['search_string']=update.message.text
#    update.message.reply_text(trans('Please choose torrent tracker:',update.message.from_user.language_code)+":", reply_markup=tracker_reply_markup)


@restricted
def searchOnWebTracker(update, context):
    logging.debug(update)

    msg = update.message.reply_text(text=trans('DOING_SEARCH', update.message.from_user.language_code)+f" {update.message.text}")

    SR=SearchTorrents(update.message.text)
    context.user_data['posts']=SR.POSTS
    # Display search results if something was found
    if len(context.user_data['posts'])>0:
        context.bot.edit_message_text(chat_id=msg.chat.id,
                                      message_id=msg.message_id,
                                      text=getPage(context),
                                      reply_markup=getKeyboard(context),
                                      parse_mode=ParseMode.HTML,
                                      disable_web_page_preview=True)
    # Tell user about empty search results
    else:
        context.bot.edit_message_text(chat_id=update.message.chat.id,
                                      message_id=msg.message_id,
                                      text=trans('NOTHING_FOUND', update.message.from_user.language_code))


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
        if torrent.status in ['seeding', 'downloading']:
            _message=_message+"\n<b>{1}</b>\n Progress: {2}% Status: {3} \n[ℹ /info_{0}] [⏹  /stop_{0}] [⏏ /delete_{0}]\n".format(torrent.id,torrent.name,round(torrent.progress),torrent.status,torrent.format_eta())
        else:
            _message=_message+"\n<b>{1}</b>\n Progress: {2}% Status: {3} \n[ℹ /info_{0}] [▶ /start_{0}] [⏏ /delete_{0}]\n".format(torrent.id,torrent.name,round(torrent.progress),torrent.status,torrent.format_eta())
    context.bot.send_message(chat_id=update.message.chat.id,
                             text=_message,parse_mode=ParseMode.HTML,
                             reply_markup=torrent_reply_markup)


@restricted
def torrentInfo(update,context):
    """Show detailed information about torrent"""
    logging.debug(update)
    torrent_id = update.message.text.split('_')[1]
    logging.info("Loading torrent id {0}".format(torrent_id))
    _message = TORRENT_CLIENT.info(int(torrent_id))
    # truncate long messages 
    _message = _message[:4000]+'..\n' if len(_message)>4000 else _message
    _message = _message+"--------------------------\n" \
            "[▶ /start_{0}] [⏹ /stop_{0}] [⏏ /delete_{0}]\n".format(torrent_id)
    try:        
        context.bot.send_message(chat_id=update.message.chat.id,
                                 text=_message,parse_mode=ParseMode.HTML,
                                 reply_markup=torrent_reply_markup)
    except Exception as err:
        context.bot.send_message(chat_id=update.message.chat.id,
                                 text="Something went wrong: {err}",
                                 parse_mode=ParseMode.HTML,
                                 reply_markup=torrent_reply_markup)


@restricted
def torrentDelete(update,context):
    """Remove torrent by torrent_id"""
    logging.debug(update)
    torrent_id = update.message.text.replace('/delete_', '')
    logging.info("Removing torrent id {0}".format(torrent_id))
    context.bot.send_message(chat_id=update.message.chat.id,
                             text=trans('TORRENT_REMOVED',
                             update.message.from_user.language_code).format(TORRENT_CLIENT.get_torrents(int(torrent_id))[0].name),
                             parse_mode=ParseMode.HTML,
                             reply_markup=torrent_reply_markup)
    TORRENT_CLIENT.remove_torrent(int(torrent_id), delete_data=config['TRANSMISSION']['DELETE_DATA'])


@restricted
def addNewUser(update, context):
    if update.message.chat.id == config['BOT']['SUPER_USER']:
        hash = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        WELCOME_HASHES.append(hash)
        logging.info(context.bot)
        message = f"https://t.me/{context.bot.username}?start=welcome_{hash}"
        img = get_qr_code(message)
        context.bot.send_photo(update.message.chat.id,
                               open(img, 'rb'),
                               caption=message)
    else:
        context.bot.send_message(update.message.chat.id, "Nice try!")


def welcomeNewUser(update, context):
    hash_code = update.message.text.replace('/start welcome_', '')
    if hash_code in WELCOME_HASHES and update.message.chat.id:
        config['BOT']['ALLOWED_USERS'].append(update.message.chat.id)
        adduser(update.message.chat.id)
        WELCOME_HASHES.remove(hash_code)
        context.bot.send_message(update.message.chat.id,
                                 f"Welcome {update.message.chat.first_name}!",
                                 reply_markup=torrent_reply_markup)
        logging.info(f"New user {update.message.chat.id}, {update.message.chat.first_name} was added.")
        help_command(update, context)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(BOT_TOKEN, use_context=True)
    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    # Admin commands
    dp.add_handler(MessageHandler(Filters.regex(r'^/help$'), help_command))
    # Issue user token:
    dp.add_handler(MessageHandler(Filters.regex(r'^/adduser$'), addNewUser))
    # Process new user request:
    dp.add_handler(MessageHandler(Filters.regex(r'^/start\ welcome_[A-Za-z0-9]+$'), welcomeNewUser))
    # Add Transmission handlers to dispatcher:
    dp.add_handler(MessageHandler(Filters.regex(r'Torrents$'), torrentList))
    # Show last search results
    dp.add_handler(MessageHandler(Filters.regex(r'Search$'), lastSearchResults))
    dp.add_handler(MessageHandler(Filters.regex(r'^/info_[0-9]+$'), torrentInfo))
    dp.add_handler(MessageHandler(Filters.regex(r'Stop All$'), torrentStopAll))
    dp.add_handler(MessageHandler(Filters.regex(r'Start All$'), torrentStartAll))
    dp.add_handler(MessageHandler(Filters.regex(r'^/stop_[0-9]+$'), torrentStop))
    dp.add_handler(MessageHandler(Filters.regex(r'^/start_[0-9]+$'), torrentStart))
    dp.add_handler(MessageHandler(Filters.regex(r'^/delete_[0-9]+$'), torrentDelete))
    # Add Search/Download/Navigation handlers to dispatcher
    # dp.add_handler(CallbackQueryHandler(searchOnWebTracker, pattern=tracker_list))
    # Ask download directory for Menu URL
    dp.add_handler(MessageHandler(Filters.regex(r'^/download_[0-9]+$'), askDownloadDirPageLink))
    # Ask download directory for magnet/http(s) link
    dp.add_handler(MessageHandler(Filters.regex(r'(magnet:\?xt=urn:btih:[a-zA-Z0-9]*|[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*))'), askDownloadDirURL))
    # Ask download directory for torrent file
    dp.add_handler(MessageHandler(Filters.document, askDownloadDirFile))
    # Navigation buttons switcher (inline keyboard)
    dp.add_handler(CallbackQueryHandler(getMenuPage, pattern=r'^[x0-9]+$'))
    # Select download folder switcher (inline keyboard)
    dp.add_handler(CallbackQueryHandler(processUserKey))
    # Default search input text
    dp.add_handler(MessageHandler(Filters.all, searchOnWebTracker))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
