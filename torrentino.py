#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Usage:
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import sys
from telegram.ext import Application
from telegram import Update
from telegram.error import InvalidToken
from models.BotConfigurator import BotConfigurator
from models.DownloadHistory import DownloadHistory

from lib.func import get_logger
from lib.bot_handlers import HANDLERS, commands
from lib.constants import CONFIG_FILE

def bot():

    bot_config = BotConfigurator()

    DownloadHistory.set_log_file(bot_config.get('bot.download_log_file'))

    log = get_logger("main", bot_config.get('bot.log_level'), bot_config.get('bot.log_file'))

    bot_config.set_bot_commands(commands)

    if not bot_config.get('bot.token'):
        log.critical("You must pass the token you received from https://t.me/Botfather!, check documentation")

    """Start the bot."""
    try:
        app = Application.builder().token(bot_config.get('bot.token')).build()
        """Add bot handlers"""
        app.add_handlers(HANDLERS)
        """Run the bot until the user presses Ctrl-C"""
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except InvalidToken as err:
        log.info("Invalid token provided: %s", str(err))
        sys.exit(1)
    except Exception as err:
        log.info("Generic error occured: %s", str(err))


if __name__ == '__main__':
    BotConfigurator.argparser()
    bot()
