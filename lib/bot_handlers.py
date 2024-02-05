import os
import tempfile
import random
import string
import pydash as _
import asyncio
import re

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.ext import MessageHandler, CallbackQueryHandler, CommandHandler
from telegram.ext.filters import Regex, Document, ALL, Entity

from lib.auth import restricted
from lib.func import (
    trans,
    get_logger,
    get_qr_code)

from models.BotConfigurator import BotConfigurator
from models.TransmissionClient import TransmissionClient
from models.SearchTorrents import SearchTorrents
from models.Browser import Browser
from models.HistoryBrowser import HistoryBrowser
from models.PostsBrowser import PostsBrowser
from models.TorrentsListBrowser import TorrentsListBrowser
from models.TorrentInfoBrowser import TorrentInfoBrowser
from models.DownloadHistory import DownloadHistory


bot_config = BotConfigurator()

log = get_logger("main")

# Init search object with trackers
def get_search():
    return SearchTorrents(credentials=bot_config.get("trackers", {}),
                          sort_by=bot_config.get("bot.sort_by", "date"))

def get_torrent_connection():
    try:
        return TransmissionClient(
            telegram_token=bot_config.get('bot.token'),
            host=bot_config.get('transmission.host'),
            port=bot_config.get('transmission.port'),
            username=bot_config.get('transmission.user'),
            password=bot_config.get('transmission.password'))
    except Exception as err:
        log.error("Transmission %s:%s is not available due to error: %s",
                bot_config.get('transmission.host'),
                bot_config.get('transmission.port'),
                err)


# Configure Bot commands and actions
commands = []
actions = []

# This variable is used to auth new users
WELCOME_HASHES = []

# Add Transmission buttons and menus only if server is available

actions.append("📁 Torrents")
commands.extend([
    ("torrents", "📁 Torrents"),
    ("last_search", "🔎 Last search"),
    ("stop_all", "⏹ Stop all Torrents"),
    ("start_all", "⏩ Start all Torrents")
])
# Add search related commands
actions.append("🔍 Search")
commands.extend([
    ("history", "🕑 Download history"),
    ("adduser", "👤 Add new user"),
    ("help", "❓ Help")])


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    HELP = trans("HELP", update.message.from_user.language_code)
    if update.message.chat.id == bot_config.get(['bot', 'super_user']):
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
async def chooseDownloadDir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        title = update.message.document.file_name
        context.user_data['torrent'] = {
            'type': 'torrent',
            'file_name': title,
            'file_id': update.message.document.file_id}
    elif re.match(r'^/download_[0-9]+$', update.message.text):
        _id = int(update.message.text.split("_")[1])
        post = context.user_data['posts'].posts[_id]
        title = post['title']
        context.user_data['torrent'] = {'type': 'url',
                                        'url': post['dl'],
                                        'tracker': post['tracker']}
    else:
        title = update.message.text
        context.user_data['torrent'] = {'type': 'url', 'url': title}
    await update.message.reply_text(trans('CHOOSE_DOWNLOAD_DIR',
                                    update.message.from_user.language_code).format(title),
                                    reply_markup=bot_config.get_downloads_keyboard())


@restricted
async def getMenuPage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    page = query.data
    try:
        nav_type = context.user_data['nav_type']
        posts: Browser = context.user_data[nav_type]
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
    except Exception as err:
        user_lang = update.callback_query.from_user.language_code
        log.error(f"Wrong menu page {page}: {err}")
        await context.bot.edit_message_text(
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id,
            text=trans('BAD_PAGE_ACCESS', user_lang),
            reply_markup=None,
            disable_web_page_preview=True)

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
        if _.has(bot_config.get('trackers'), _.get(context.user_data, 'torrent.tracker')):
            _tmp_file_path = get_search().download(context.user_data['torrent']['url'],
                                             context.user_data['torrent']['tracker'])
            tmp_file_path = f"file://{_tmp_file_path}"
    lang_code = query.from_user.language_code
    log.info("Adding file/URL %s to Transmission", tmp_file_path)
    message = query.message.text
    message += "\n----------------------\n"
    try:
        get_torrent_connection().add_torrent(
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

    # 1. Warning for user if wrong content type was passed
    if update.message.effective_attachment:
        await update.message.reply_text(text=trans('UNSUPPORTED_MIME_TYPE', lang_code))
        return
    # 2. Warning for user if too long message was passed
    if len(update.message.text) > 256:
        await update.message.reply_text(text=trans('MESSAGE_IS_TOO_LONG', lang_code))
        return
    # 3. Display dumb message while search is running, so user will understand all is good
    msg = await update.message.reply_text(text=trans('DOING_SEARCH', lang_code) + " " + update.message.text)

    # Create search object
    searcher = SearchTorrents(credentials=bot_config.get("trackers", {}), sort_by=bot_config.get("bot.sort_by", "date"))
    # Get search results
    posts = PostsBrowser(
        user_id=msg.chat_id,
        user_lang=lang_code,
        posts=searcher.search(update.message.text))
    context.user_data['nav_type'] = 'posts'
    context.user_data['posts'] = posts

    # Get search results
    if posts.number_of_pages > 0:
        text = posts.get_page()
        reply_markup = posts.get_keyboard()
    # Tell user about empty search results
    else:
        text=trans('NOTHING_FOUND', lang_code)
        reply_markup=None

    # Add warning message if something went wrong while searching on trackers
    if len(searcher.FAILED_SEARCH) > 0:
        text += "\n--------------\n" + trans('FAILED_SEARCH_ON_TRACKERS', lang_code) + " " + ", ".join(searcher.FAILED_SEARCH)
    if len(searcher.FAILED_TRACKERS) > 0:
        text += "\n--------------\n" + trans("FAILED_INIT_TRACKERS", lang_code) + " " + ", ".join(searcher.FAILED_TRACKERS)

    await context.bot.edit_message_text(
        chat_id=update.message.chat.id,
        message_id=msg.message_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True)


@restricted
async def torrentStop(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Stop torrent by torrent_id"""
    get_torrent_connection().stop_torrent(int(update.message.text.split('_')[1]))
    await asyncio.sleep(1)


@restricted
async def torrentStopAll(_: Update, __: ContextTypes.DEFAULT_TYPE):
    """Stop All Torrents"""
    get_torrent_connection().stop_all()
    await asyncio.sleep(1)


@restricted
async def torrentStart(update: Update, __: ContextTypes.DEFAULT_TYPE):
    """Start torrent by torrent_id"""
    get_torrent_connection().start_torrent(int(update.message.text.split('_')[1]))
    await asyncio.sleep(1)


@restricted
async def torrentStartAll(_: Update, __: ContextTypes.DEFAULT_TYPE):
    """Stop All Torrents"""
    get_torrent_connection().start_all()
    await asyncio.sleep(1)


@restricted
async def torrentList(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all torrents on Transmission server"""
    torrents = TorrentsListBrowser(
        user_id=update.message.chat.id,
        user_lang=update.message.from_user.language_code,
        posts=get_torrent_connection().get_torrents())
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
        posts=get_torrent_connection().get_torrent(int(torrent_id))
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
                   update.message.from_user.language_code).format(get_torrent_connection().get_torrents(int(torrent_id))[0].name),
        parse_mode=ParseMode.HTML)
    get_torrent_connection().remove_torrent(int(torrent_id), delete_data=bot_config.get('transmission.delete_data'))


@restricted
async def addNewUser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id == bot_config.get('bot.super_user'):
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
        bot_config.add_user(update.message.chat.id)
        WELCOME_HASHES.remove(hash_code)
        await context.bot.send_message(update.message.chat.id,
                                       f"Welcome {update.message.chat.first_name}!",
                                       reply_markup=bot_config.get_actions_keyboard(actions))
        log.info(f"New user {update.message.chat.id}, {update.message.chat.first_name} was added.")
        await help_command(update, context)


HANDLERS = [
    # Process new user request:
    MessageHandler(Regex(r'^/start\ welcome_[A-Za-z0-9]+$'), welcomeNewUser),
    # Add Transmission handlers to dispatcher:
    MessageHandler(Regex(r'Torrents$'), torrentList),
    MessageHandler(Regex(r'Search$'), lastSearchResults),
    CommandHandler("help", help_command),
    CommandHandler("adduser", addNewUser),
    CommandHandler("last_search", lastSearchResults),
    CommandHandler("torrents", torrentList),
    CommandHandler("stop_all", torrentStopAll),
    CommandHandler("start_all", torrentStartAll),
    CommandHandler("history", history),
    MessageHandler(Regex(r'^/info_[0-9]+$'), torrentInfo),
    MessageHandler(Regex(r'^/stop_[0-9]+$'), torrentStop),
    MessageHandler(Regex(r'^/start_[0-9]+$'), torrentStart),
    MessageHandler(Regex(r'^/delete_[0-9]+$'), torrentDelete),
    # Ask download directory for Menu URL
    MessageHandler(Regex(r'^/download_[0-9]+$'), chooseDownloadDir),
    # Ask download directory for magnet/http(s) link
    MessageHandler(Regex(r'^(magnet:\?xt=urn:btih:[a-zA-Z0-9]*|[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*))$'),
                   chooseDownloadDir),
    MessageHandler(Entity("url"), chooseDownloadDir),
    # Ask download directory for torrent file
    MessageHandler(Document.MimeType('application/x-bittorrent'), chooseDownloadDir),

    # Navigation buttons switcher (inline keyboard)
    CallbackQueryHandler(getMenuPage, pattern=r'^[x0-9]+$'),
    # Select download folder switcher (inline keyboard)
    CallbackQueryHandler(addTorrentToTransmission),
    # Default search input text
    MessageHandler(ALL, searchOnWebTracker)
]
