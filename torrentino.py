#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Usage:
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import requests
import os
import tempfile
import random
import string
import pydash as _

from models.TransmissionClient import TransmissionClient
from models.SearchTorrents import SearchTorrents

from lib.func import (
    restricted,
    trans,
    get_config,
    get_logger,
    get_qr_code,
    adduser,
    save_torrent_to_tempfile)

from telegram.ext import Application, MessageHandler, CallbackQueryHandler, ContextTypes
from telegram.ext.filters import Regex, Document, ALL
from telegram import Update, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.constants import ParseMode

# Read configuration file, torrentino.ini
# File is in the same directory as script
config = get_config()

# Telegram bot token
BOT_TOKEN = config['BOT']['TOKEN']
# Client connection to Transmission torrent server
# User environment variables or defaults from configuration file
TORRENT_CLIENT = TransmissionClient(
    telegram_token=BOT_TOKEN,
    host=os.getenv("TR_HOST", config['TRANSMISSION']['HOST']),
    port=int(os.getenv("TR_PORT", config['TRANSMISSION']['PORT'])),
    username=os.getenv("TR_USER", config['TRANSMISSION']['USER']),
    password=os.getenv("TR_PASSWORD", config['TRANSMISSION']['PASSWORD']))

# Download directories
# Transmission server needs write access to these directories
reply_markup = InlineKeyboardMarkup(
    [[InlineKeyboardButton(key.capitalize(), callback_data=value) for key, value in dict(config['DIRECTORIES']).items()]])

# This variable is used to auth new users
WELCOME_HASHES = []

log = get_logger("main")

# Configure actions to work with torrent
TORRENT_ACTIONS = ["📁 Torrents", "🔍 Search"]

torrent_reply_markup = ReplyKeyboardMarkup([[KeyboardButton(text=str(key)) for key in TORRENT_ACTIONS]], resize_keyboard=True)


SEARCH_TORRENTS = SearchTorrents(credentials=_.get(config, "CREDENTIALS", {}),
                                 sort_by=_.get(config, "BOT.SORT_BY", "date"))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    HELP = trans("HELP", update.message.from_user.language_code)
    if update.message.chat.id == config['BOT']['SUPER_USER']:
        HELP += "\n"+trans("HELP_ADMIN", update.message.from_user.language_code)
    log.info("%s, %s, %s", update.message.chat.id, update.message.chat_id, context.user_data)
    await context.bot.send_message(chat_id=update.message.chat.id, text=HELP, parse_mode=ParseMode.HTML, reply_markup=torrent_reply_markup)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echo the user message."""
    await update.message.reply_text(update.message.text, reply_markup=torrent_reply_markup)
    log.debug("echo: "+str(update))


@restricted
async def askDownloadDirFile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for download file directory, value is passed to Transimission"""
    log.debug(update)
    log.info("Searching for download file dir")

    await update.message.reply_text(
        trans('Please choose download folder for {}',
              update.message.from_user.language_code).format(update.message.document.file_name)+":", reply_markup=reply_markup)
    context.user_data['torrent'] = {
        'type': 'torrent',
        'file_name': update.message.document.file_name,
        'file_id': update.message.document.file_id}


async def unsupportedMime(update: Update, _: ContextTypes.DEFAULT_TYPE):
    update.message.reply_text("Error: File %s has unsupported mime type %s",
                              update.message.document.file_name,
                              update.message.document.mime_type)


@restricted
async def askDownloadDirURL(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask download directory for Magnet URL, value is passed to Transimission"""
    log.info(f"Downloading URL {update.message.text}")
    await update.message.reply_text(trans('CHOOSE_DOWNLOAD_DIR',
                                    update.message.from_user.language_code).format(update.message.text)+":",
                                    reply_markup=reply_markup)
    context.user_data['torrent'] = {'type': 'url', 'url': update.message.text}


@restricted
async def askDownloadDirPageLink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info(f"Downloading page link {update.message.text}")
    _id = int(update.message.text.split("_")[1])
    await update.message.reply_text(trans('CHOOSE_DOWNLOAD_DIR',
                                    update.message.from_user.language_code).format(context.user_data['posts'][_id]['dl'])+":",
                                    reply_markup=reply_markup)
    context.user_data['torrent'] = {'type': 'url',
                                    'url': context.user_data['posts'][_id]['dl'],
                                    'tracker': context.user_data['posts'][_id]['tracker']}
    log.info("Added torrent URL to download list: {}".format(context.user_data['posts'][_id]['dl']))


@restricted
async def getMenuPage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    page = query.data
    try:
        if str(page) == 'x':
            log.warn("You are trying to click the same page")
            return
        await context.bot.edit_message_text(
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id,
            text=getPage(context, int(page), query.from_user.language_code),
            parse_mode=ParseMode.HTML,
            reply_markup=getKeyboard(context, page),
            disable_web_page_preview=True)
    except ValueError as err:
        log.error(f"Wrong menu page {page}: {err}")


@restricted
async def lastSearchResults(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'posts' in context.user_data:
        await update.message.reply_text(
            text=getPage(context, user_lang=update.message.from_user.language_code),
            reply_markup=getKeyboard(context),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True)
    else:
        await context.bot.send_message(
            chat_id=update.message.chat.id,
            text=trans('NO_SEARCH_RESULTS',
                       update.message.from_user.language_code),
            reply_markup=torrent_reply_markup)

def getNumPages(context: ContextTypes.DEFAULT_TYPE) -> int:
    num_pages = int(len(context.user_data['posts']) / 5)
    if len(context.user_data['posts']) % 5 > 0:
        num_pages += 1
    return num_pages

def getPage(context: ContextTypes.DEFAULT_TYPE, _page: int = 1, user_lang: str = "en") -> str:
    page = int(_page)
    posts = context.user_data['posts']
    _message = trans("NAV_HEADER", user_lang).format(page, getNumPages(context), len(posts))
    # Add first and last posts index
    post_num = (page - 1) * 5
    for post in posts[post_num:post_num+5]:
        _message += f"\n<b>{post['title']}</b>: {post['size']}  {post['date']} ⬆{post['seed']} ⬇{post['leach']}\n" \
                    f"<a href='{post['info']}'>Info</a>     [ ▼ /download_{post_num} ]\n"
        post_num += 1
    return _message


def getKeyboard(context, _page=1):
    pages = getNumPages(context)
    # Edge case for first page
    page = int(_page)
    if page == 1 or page < 4:
        KEYBOARD = [InlineKeyboardButton(str(jj), callback_data=str(jj)) for jj in range(1, 8) if jj < pages]
    # Edge case for last page
    elif pages - page < 4:
        KEYBOARD = [InlineKeyboardButton(str(jj), callback_data=str(jj)) for jj in range(pages - 6, pages + 1) if jj <= pages]
    # Regular navigation
    else:
        KEYBOARD = [InlineKeyboardButton(str(jj), callback_data=str(jj)) for jj in range(page - 3, page + 4) if jj <= pages]

    FOOTER_KEYS = []
    if page > 10:
        FOOTER_KEYS.append(InlineKeyboardButton("«« -10", callback_data=str(page-10)))
    if pages > page + 10:
        FOOTER_KEYS.append(InlineKeyboardButton("+10 »»", callback_data=str(page+10)))

    for key in KEYBOARD:
        if str(key.text) == str(page):
            idx = KEYBOARD.index(key)
            KEYBOARD.remove(key)
            KEYBOARD.insert(idx, InlineKeyboardButton("...", callback_data="x"))

    return InlineKeyboardMarkup([KEYBOARD, FOOTER_KEYS])


@restricted
async def addTorrentToTransmission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.debug(update)

    query = update.callback_query
    await query.answer()
    if context.user_data['torrent']['type'] == 'torrent':
        # Temporal file location
        _tmp_file_path = os.path.join(tempfile.gettempdir(), context.user_data['torrent']['file_name'])
        # Download file from telegram bot to temporal location
        _file = await context.bot.getFile(context.user_data['torrent']['file_id'])
        await _file.download_to_drive(_tmp_file_path)
        tmp_file_path = f"file://{_tmp_file_path}"
    elif context.user_data['torrent']['type'] in ['url', 'magnet']:
        # Magnet URLs and regular URLs are processed by transmission
        tmp_file_path = context.user_data['torrent']['url']
        # If tracker has credential, download file and path file path to Transmission
        if _.has(config['CREDENTIALS'], _.get(context.user_data, 'torrent.tracker')):
            _tmp_file_path = download_with_auth(context.user_data['torrent']['url'],
                                                config['CREDENTIALS'][context.user_data['torrent']['tracker']])
            tmp_file_path = f"file://{_tmp_file_path}"

    log.info("Adding file/URL %s to Transmission", tmp_file_path)
    TORRENT_CLIENT.add_torrent(chat_id=update.effective_user.id,
                               torrent=tmp_file_path,
                               download_dir=query.data)
    await query.edit_message_text(text=trans('FILE_WILL_BE_DOWNLOADED',
                                             query.from_user.language_code).format(tmp_file_path, str(query.data)))


def download_with_auth(file_url: str, auth_info: dict) -> str:
    """Download file from phpbb torrent tracker, return path to downloaded file"""
    x = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0'}
    payload = {
        "username": auth_info['USERNAME'],
        "password": auth_info['PASSWORD'],
        'redirect': 'index.php?',
        'sid': '',
        'login': 'Login'
    }
    x.post(auth_info['login_url'], headers=headers, data=payload)
    content = x.get(file_url, allow_redirects=True).content
    log.info("Downloading file %s with authorization", file_url)
    return save_torrent_to_tempfile(content)


@restricted
async def searchOnWebTracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.debug(update)

    msg = await update.message.reply_text(text=trans('DOING_SEARCH', update.message.from_user.language_code)+f" {update.message.text}")

    context.user_data['posts'] = SEARCH_TORRENTS.search(update.message.text)
    # Display search results if something was found
    if len(context.user_data['posts']) > 0:
        await context.bot.edit_message_text(chat_id=msg.chat.id,
                                            message_id=msg.message_id,
                                            text=getPage(context),
                                            reply_markup=getKeyboard(context),
                                            parse_mode=ParseMode.HTML,
                                            disable_web_page_preview=True)
    # Tell user about empty search results
    else:
        await context.bot.edit_message_text(
            chat_id=update.message.chat.id,
            message_id=msg.message_id,
            text=trans('NOTHING_FOUND', update.message.from_user.language_code))


@restricted
def torrentStop(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Stop torrent by torrent_id"""
    TORRENT_CLIENT.stop_torrent(int(update.message.text.split('_')[1]))


@restricted
def torrentStopAll(_: Update, __: ContextTypes.DEFAULT_TYPE):
    """Stop All Torrents"""
    TORRENT_CLIENT.stop_all()


@restricted
def torrentStart(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Start torrent by torrent_id"""
    TORRENT_CLIENT.start_torrent(int(update.message.text.split('_')[1]))


@restricted
def torrentStartAll(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Stop All Torrents"""
    TORRENT_CLIENT.start_all()


@restricted
async def torrentList(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all torrents on Transmission server"""
    _message = trans("Torrents list", update.message.from_user.language_code)+": \n"
    for torrent in TORRENT_CLIENT.get_torrents():
        if torrent.status in ['seeding', 'downloading']:
            _message += "\n<b>{1}</b>\n Progress: {2}% Status: {3} \n[ℹ /info_{0}] [⏹  /stop_{0}] [⏏ /delete_{0}]\n" \
                .format(torrent.id, torrent.name, round(torrent.progress), torrent.status)
        else:
            _message += "\n<b>{1}</b>\n Progress: {2}% Status: {3} \n[ℹ /info_{0}] [▶ /start_{0}] [⏏ /delete_{0}]\n" \
                .format(torrent.id, torrent.name, round(torrent.progress), torrent.status)
    await context.bot.send_message(chat_id=update.message.chat.id,
                                   text=_message,
                                   parse_mode=ParseMode.HTML,
                                   reply_markup=torrent_reply_markup)


@restricted
async def torrentInfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed information about torrent"""
    log.debug(update)
    torrent_id = update.message.text.split('_')[1]
    log.info("Loading torrent id {0}".format(torrent_id))
    _message = TORRENT_CLIENT.info(int(torrent_id))
    # truncate long messages
    _message = _message[:4000]+'..\n' if len(_message) > 4000 else _message
    _message += "--------------------------\n" \
                "[▶ /start_{0}] [⏹ /stop_{0}] [⏏ /delete_{0}]\n".format(torrent_id)
    try:
        await context.bot.send_message(chat_id=update.message.chat.id,
                                       text=_message,
                                       parse_mode=ParseMode.HTML,
                                       reply_markup=torrent_reply_markup)
    except Exception as err:
        await context.bot.send_message(chat_id=update.message.chat.id,
                                       text=f"Something went wrong: {err}",
                                       parse_mode=ParseMode.HTML,
                                       reply_markup=torrent_reply_markup)


@restricted
async def torrentDelete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove torrent by torrent_id"""
    log.debug(update)
    torrent_id = update.message.text.replace('/delete_', '')
    log.info("Removing torrent id {0}".format(torrent_id))
    await context.bot.send_message(
        chat_id=update.message.chat.id,
        text=trans('TORRENT_REMOVED',
                   update.message.from_user.language_code).format(TORRENT_CLIENT.get_torrents(int(torrent_id))[0].name),
        parse_mode=ParseMode.HTML,
        reply_markup=torrent_reply_markup)
    TORRENT_CLIENT.remove_torrent(int(torrent_id), delete_data=config['TRANSMISSION']['DELETE_DATA'])


@restricted
def addNewUser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id == config['BOT']['SUPER_USER']:
        hash = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        WELCOME_HASHES.append(hash)
        log.info(context.bot)
        message = f"https://t.me/{context.bot.username}?start=welcome_{hash}"
        img = get_qr_code(message)
        context.bot.send_photo(update.message.chat.id,
                               open(img, 'rb'),
                               caption=message)
    else:
        context.bot.send_message(update.message.chat.id, "Nice try!")


def welcomeNewUser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hash_code = update.message.text.replace('/start welcome_', '')
    if hash_code in WELCOME_HASHES and update.message.chat.id:
        config['BOT']['ALLOWED_USERS'].append(update.message.chat.id)
        adduser(update.message.chat.id)
        WELCOME_HASHES.remove(hash_code)
        context.bot.send_message(update.message.chat.id,
                                 f"Welcome {update.message.chat.first_name}!",
                                 reply_markup=torrent_reply_markup)
        log.info(f"New user {update.message.chat.id}, {update.message.chat.first_name} was added.")
        help_command(update, context)


def main():
    """Start the bot."""
    app = Application.builder().token(BOT_TOKEN).build()
    # scheduler(app.bot)
    # Admin commands
    app.add_handler(MessageHandler(Regex(r'^/(help|start)$'), help_command))
    # Issue user token:
    app.add_handler(MessageHandler(Regex(r'^/adduser$'), addNewUser))
    # Process new user request:
    app.add_handler(MessageHandler(Regex(r'^/start\ welcome_[A-Za-z0-9]+$'), welcomeNewUser))
    # Add Transmission handlers to dispatcher:
    app.add_handler(MessageHandler(Regex(r'Torrents$'), torrentList))
    # Show last search results
    app.add_handler(MessageHandler(Regex(r'Search$'), lastSearchResults))
    app.add_handler(MessageHandler(Regex(r'^/info_[0-9]+$'), torrentInfo))

    app.add_handler(MessageHandler(Regex(r'^/stop_[0-9]+$'), torrentStop))
    app.add_handler(MessageHandler(Regex(r'^/start_[0-9]+$'), torrentStart))
    app.add_handler(MessageHandler(Regex(r'^/delete_[0-9]+$'), torrentDelete))

    # Ask download directory for Menu URL
    app.add_handler(MessageHandler(Regex(r'^/download_[0-9]+$'), askDownloadDirPageLink))
    # Ask download directory for magnet/http(s) link
    app.add_handler(
        MessageHandler(Regex(r'(magnet:\?xt=urn:btih:[a-zA-Z0-9]*|[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*))'),
                       askDownloadDirURL))
    # Ask download directory for torrent file
    app.add_handler(MessageHandler(Document.MimeType('application/x-bittorrent'), askDownloadDirFile))

    app.add_handler(MessageHandler(Document.ALL, unsupportedMime))
    # Navigation buttons switcher (inline keyboard)
    app.add_handler(CallbackQueryHandler(getMenuPage, pattern=r'^[x0-9]+$'))
    # Select download folder switcher (inline keyboard)
    app.add_handler(CallbackQueryHandler(addTorrentToTransmission))
    # Default search input text
    app.add_handler(MessageHandler(ALL, searchOnWebTracker))

    # Run the bot until the user presses Ctrl-C
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
