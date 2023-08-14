#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Usage:
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import sys
import os
import tempfile
import random
import string
import pydash as _
import asyncio

from telegram.ext import Application, MessageHandler, CallbackQueryHandler, ContextTypes, CommandHandler
from telegram.ext.filters import Regex, Document, ALL, Entity
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

from models.TransmissionClient import TransmissionClient
from models.SearchTorrents import SearchTorrents
from models.PostsBrowser import PostsBrowser
from models.TorrentsListBrowser import TorrentsListBrowser
from models.TorrentInfoBrowser import TorrentInfoBrowser
from models.DownloadHistory import DownloadHistory
from models.HistoryBrowser import HistoryBrowser
from models.BotConfigurator import BotConfigurator
from lib.auth import restricted
from lib.func import (
    trans,
    get_logger,
    get_qr_code)


bot_config = BotConfigurator()
# Read configuration file, torrentino.yaml
# File is in the same directory as script
config = bot_config.config
token = _.get(config, 'bot.token')
log = get_logger("main", _.get(config, 'bot.log_file'))
DownloadHistory.set_log_file(_.get(config, 'bot.download_log_file', 'download.log'))


# Client connection to Transmission torrent server
# User environment variables or defaults from configuration file
try:
    host = os.getenv("HOST", _.get(config, 'transmission.host'))
    port = os.getenv("PORT", _.get(config, 'transmission.port'))
    TORRENT_CLIENT = TransmissionClient(
        telegram_token=token,
        host=host,
        port=port,
        username=os.getenv("USER", _.get(config, 'transmission.user')),
        password=os.getenv("PASSWORD", _.get(config, 'transmission.password')))
    log.info("Connection to Transmission server ininitialized: %s:%s", host, port)
except Exception as err:
    TORRENT_CLIENT = None
    log.error("Transmission is not available: %s", err)

if not bot_config.validate():
    sys.exit(1)

# Configure actions to work with torrent
commands = []
actions = []

# Add Transmission buttons and menus only if server is available
if TORRENT_CLIENT:
    actions.append("📁 Torrents")
    commands.extend([
        ("torrents", "📁 Torrents"),
        ("stop_all", "⏹ Stop all Torrents"),
        ("start_all", "⏩ Start all Torrents"),
        ("history", "🕑 Download history")
    ])

actions.append("🔍 Search")
commands.extend([
    ("last_search", "🔎 Last search"),
    ("adduser", "👤 Add new user"),
    ("help", "❓ Help")])

bot_config.set_bot_commands(commands)


# This variable is used to auth new users
WELCOME_HASHES = []

SEARCH = SearchTorrents(credentials=_.get(config, "trackers", {}),
                        sort_by=_.get(config, "bot.sort_by", "date"))



async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    HELP = trans("HELP", update.message.from_user.language_code)
    if update.message.chat.id == config['bot']['super_user']:
        HELP += "\n"+trans("HELP_ADMIN", update.message.from_user.language_code)
    log.info("%s, %s, %s", update.message.chat.id, update.message.chat_id, context.user_data)
    await context.bot.send_message(chat_id=update.message.chat.id, text=HELP, parse_mode=ParseMode.HTML, reply_markup=bot_config.get_actions_keyboard(actions))

@restricted
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    history = HistoryBrowser(
        user_id=update.message.chat.id,
        user_lang=update.message.from_user.language_code,
        posts=DownloadHistory.show())
    context.user_data['nav_type'] = 'history'
    context.user_data['history'] = history
    await context.bot.send_message(chat_id=update.message.chat.id,
                                   text=history.get_page(),
                                   parse_mode=ParseMode.HTML,
                                   reply_markup=history.get_keyboard())    


@restricted
async def askDownloadDirFile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for download file directory, value is passed to Transimission"""
    log.debug(update)
    log.info("Searching for download file dir")

    await update.message.reply_text(
        trans('Please choose download folder for {}',
              update.message.from_user.language_code).format(update.message.document.file_name)+":", 
        reply_markup=bot_config.get_downloads_keyboard())
    context.user_data['torrent'] = {
        'type': 'torrent',
        'file_name': update.message.document.file_name,
        'file_id': update.message.document.file_id}


@restricted
async def askDownloadDirURL(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask download directory for Magnet URL, value is passed to Transimission"""
    log.info(f"Downloading URL {update.message.text}")
    await update.message.reply_text(trans('CHOOSE_DOWNLOAD_DIR',
                                    update.message.from_user.language_code).format(update.message.text),
                                    reply_markup=bot_config.get_downloads_keyboard())
    context.user_data['torrent'] = {'type': 'url', 'url': update.message.text}


@restricted
async def askDownloadDirPageLink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # FIXME: refactor to PostsBrowser
    log.info(f"Downloading page link {update.message.text}")
    _id = int(update.message.text.split("_")[1])
    post = context.user_data['posts'].posts[_id]
    await update.message.reply_text(trans('CHOOSE_DOWNLOAD_DIR',
                                    update.message.from_user.language_code).format(post['title']),
                                    reply_markup=reply_markup)

    context.user_data['torrent'] = {'type': 'url',
                                    'url': post['dl'],
                                    'tracker': post['tracker']}
    log.info("Added torrent URL to download list: %s", post)


@restricted
async def getMenuPage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    nav_type = context.user_data['nav_type']

    posts = context.user_data[nav_type]
    page = query.data
    try:
        if str(page) == 'x':
            log.warn("You are trying to click the same page")
            return
        await context.bot.edit_message_text(
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id,
            text=posts.get_page(int(page)),
            parse_mode=ParseMode.HTML,
            reply_markup=posts.get_keyboard(page),
            disable_web_page_preview=True)
    except ValueError as err:
        log.error(f"Wrong menu page {page}: {err}")


@restricted
async def lastSearchResults(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if _.has(context.user_data, 'posts'):
        context.user_data['nav_type'] = 'posts'
        posts: PostsBrowser = context.user_data['posts']
        await update.message.reply_text(
            text=posts.get_page(),
            reply_markup=posts.get_keyboard(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True)
    else:
        user_lang = update.message.from_user.language_code
        await context.bot.send_message(
            chat_id=update.message.chat.id,
            text=trans('NO_SEARCH_RESULTS', user_lang))


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
        if _.has(config['trackers'], _.get(context.user_data, 'torrent.tracker')):
            _tmp_file_path = SEARCH.download(context.user_data['torrent']['url'],
                                             context.user_data['torrent']['tracker'])
            tmp_file_path = f"file://{_tmp_file_path}"
    lang_code = query.from_user.language_code
    log.info("Adding file/URL %s to Transmission", tmp_file_path)
    message = query.message.text
    message += "\n----------------------\n"
    try:
        TORRENT_CLIENT.add_torrent(
            chat_id=update.effective_user.id,
            lang_code=lang_code,
            torrent=tmp_file_path,
            download_dir=query.data)
        message += trans('ADDING_TORRENT_FILE_WILL_BE_DOWNLOADED', lang_code).format(str(query.data))
    except Exception as err:
        if 'invalid or corrupt torrent file' in str(err):
            message += trans('ADDING_TORRENT_FILE_IS_CORRUPTED', lang_code)
        else:
            message += trans('ADDING_FILE_SOMETHING_WENT_WRONG', lang_code) + ':\n' + str(err)
        log.error("File %s was not added due to error %s", tmp_file_path, str(err))
    await query.edit_message_text(text=message)


@restricted
async def searchOnWebTracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search on web trackers and return results back to user"""
    lang_code = update.message.from_user.language_code

    # FIXME: Initial validation for wrong content passed in message
    # It could be implemented as message handlers
    if update.message.effective_attachment:
        await update.message.reply_text(text=trans('UNSUPPORTED_MIME_TYPE', lang_code))
        return
    if len(update.message.text) > 256:
        await update.message.reply_text(text=trans('MESSAGE_IS_TOO_LONG', lang_code))
        return

    msg = await update.message.reply_text(text=trans('DOING_SEARCH', lang_code)+f" {update.message.text}")

    posts = PostsBrowser(
        user_id=msg.chat_id,
        user_lang=lang_code,
        posts=SEARCH.search(update.message.text))
    context.user_data['nav_type'] = 'posts'
    context.user_data['posts'] = posts
    # Display search results if something was found
    if posts.number_of_pages > 0:
        text = posts.get_page()
        if len(SEARCH.FAILED_SEARCH) > 0:
            text += "--------------\n" \
            "⚠ Failed search on trackers: " + ", ".join(SEARCH.FAILED_SEARCH)

        await context.bot.edit_message_text(chat_id=msg.chat.id,
                                            message_id=msg.message_id,
                                            text=text,
                                            reply_markup=posts.get_keyboard(),
                                            parse_mode=ParseMode.HTML,
                                            disable_web_page_preview=True)
    # Tell user about empty search results
    else:
        await context.bot.edit_message_text(
            chat_id=update.message.chat.id,
            message_id=msg.message_id,
            text=trans('NOTHING_FOUND', lang_code))


@restricted
async def torrentStop(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Stop torrent by torrent_id"""
    TORRENT_CLIENT.stop_torrent(int(update.message.text.split('_')[1]))
    await asyncio.sleep(1)


@restricted
async def torrentStopAll(_: Update, __: ContextTypes.DEFAULT_TYPE):
    """Stop All Torrents"""
    TORRENT_CLIENT.stop_all()
    await asyncio.sleep(1)


@restricted
async def torrentStart(update: Update, __: ContextTypes.DEFAULT_TYPE):
    """Start torrent by torrent_id"""
    TORRENT_CLIENT.start_torrent(int(update.message.text.split('_')[1]))
    await asyncio.sleep(1)


@restricted
async def torrentStartAll(_: Update, __: ContextTypes.DEFAULT_TYPE):
    """Stop All Torrents"""
    TORRENT_CLIENT.start_all()
    await asyncio.sleep(1)


@restricted
async def torrentList(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all torrents on Transmission server"""
    torrents = TorrentsListBrowser(
        user_id=update.message.chat.id,
        user_lang=update.message.from_user.language_code,
        posts=TORRENT_CLIENT.get_torrents())
    context.user_data['nav_type'] = 'torrents'
    context.user_data['torrents'] = torrents
    await context.bot.send_message(chat_id=update.message.chat.id,
                                   text=torrents.get_page(),
                                   parse_mode=ParseMode.HTML,
                                   reply_markup=torrents.get_keyboard())


@restricted
async def torrentInfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed information about torrent"""
    log.debug(update)
    torrent_id = update.message.text.split('_')[1]
    user_id = update.message.chat.id
    log.info("Loading torrent id {0}".format(torrent_id))
    torrent_info = TorrentInfoBrowser(
        user_id=user_id,
        user_lang=update.message.from_user.language_code,
        posts=TORRENT_CLIENT.get_torrent(int(torrent_id))
    )
    context.user_data['nav_type'] = 'torrent_info'
    context.user_data['torrent_info'] = torrent_info

    try:
        await context.bot.send_message(chat_id=user_id,
                                       text=torrent_info.get_page(),
                                       parse_mode=ParseMode.HTML,
                                       reply_markup=torrent_info.get_keyboard())
    except Exception as err:
        await context.bot.send_message(chat_id=update.message.chat.id,
                                       text=f"Something went wrong: {err}",
                                       parse_mode=ParseMode.HTML)


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
        parse_mode=ParseMode.HTML)
    TORRENT_CLIENT.remove_torrent(int(torrent_id), delete_data=config['transmission']['delete_data'])


@restricted
async def addNewUser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id == config['bot']['super_user']:
        hash = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        WELCOME_HASHES.append(hash)
        log.info(context.bot)
        message = f"https://t.me/{context.bot.username}?start=welcome_{hash}"
        img = get_qr_code(message)
        await context.bot.send_photo(update.message.chat.id,
                                     open(img, 'rb'),
                                     caption=message)
    else:
        await context.bot.send_message(update.message.chat.id, "Nice try!")


async def welcomeNewUser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hash_code = update.message.text.replace('/start welcome_', '')
    if hash_code in WELCOME_HASHES and update.message.chat.id:
        config['bot']['allowed_users'].append(update.message.chat.id)
        bot_config.add_user(update.message.chat.id)
        WELCOME_HASHES.remove(hash_code)
        await context.bot.send_message(update.message.chat.id,
                                       f"Welcome {update.message.chat.first_name}!",
                                       reply_markup=bot_config.get_actions_keyboard(actions))
        log.info(f"New user {update.message.chat.id}, {update.message.chat.first_name} was added.")
        help_command(update, context)


def main():
    """Start the bot."""
    app = Application.builder().token(token).build()
    # Process new user request:
    app.add_handler(MessageHandler(Regex(r'^/start\ welcome_[A-Za-z0-9]+$'), welcomeNewUser))

    # Add Transmission handlers to dispatcher:
    app.add_handler(MessageHandler(Regex(r'Torrents$'), torrentList))
    app.add_handler(MessageHandler(Regex(r'Search$'), lastSearchResults))

    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("adduser", addNewUser))
    app.add_handler(CommandHandler("last_search", lastSearchResults))
    app.add_handler(CommandHandler("torrents", torrentList))
    app.add_handler(CommandHandler("stop_all", torrentStopAll))
    app.add_handler(CommandHandler("start_all", torrentStartAll))
    app.add_handler(CommandHandler("history", history))

    app.add_handler(MessageHandler(Regex(r'^/info_[0-9]+$'), torrentInfo))

    app.add_handler(MessageHandler(Regex(r'^/stop_[0-9]+$'), torrentStop))
    app.add_handler(MessageHandler(Regex(r'^/start_[0-9]+$'), torrentStart))
    app.add_handler(MessageHandler(Regex(r'^/delete_[0-9]+$'), torrentDelete))

    # Ask download directory for Menu URL
    app.add_handler(MessageHandler(Regex(r'^/download_[0-9]+$'), askDownloadDirPageLink))
    # Ask download directory for magnet/http(s) link
    app.add_handler(
        MessageHandler(Regex(r'^(magnet:\?xt=urn:btih:[a-zA-Z0-9]*|[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*))$'),
                       askDownloadDirURL))
    app.add_handler(
        MessageHandler(Entity("url"), askDownloadDirURL))
    # Ask download directory for torrent file
    app.add_handler(MessageHandler(Document.MimeType('application/x-bittorrent'), askDownloadDirFile))

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
