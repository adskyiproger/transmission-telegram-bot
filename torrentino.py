#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Usage:
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import asyncio
import sys
from contextlib import suppress
from telegram.ext import Application
from telegram import Update
from telegram.error import InvalidToken
from models.BotConfigurator import BotConfigurator
from models.DownloadHistory import DownloadHistory

from lib.func import get_logger
from lib.bot_handlers import HANDLERS, commands, get_torrent_connection


def bot():

    bot_config = BotConfigurator()

    DownloadHistory.set_log_file(bot_config.get("bot.download_log_file"))

    log = get_logger(
        "main", bot_config.get("bot.log_level"), bot_config.get("bot.log_file")
    )

    if not bot_config.validate():
        raise SystemExit(2)

    bot_config.set_bot_commands(commands)

    """Start the bot."""
    try:
        monitor_task = None

        async def post_init(application):
            nonlocal monitor_task
            await application.bot.set_my_commands(commands)
            client = get_torrent_connection()
            monitor_task = application.create_task(
                client.monitor_downloads(application.bot),
                name="transmission-download-monitor",
            )

        async def post_shutdown(_application):
            if monitor_task is not None:
                monitor_task.cancel()
                with suppress(asyncio.CancelledError):
                    await monitor_task

        app = (
            Application.builder()
            .token(bot_config.get("bot.token"))
            .post_init(post_init)
            .post_shutdown(post_shutdown)
            .build()
        )
        """Add bot handlers"""
        app.add_handlers(HANDLERS)
        """Run the bot until the user presses Ctrl-C"""
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except InvalidToken as err:
        log.info("Invalid token provided: %s", str(err))
        sys.exit(1)
    except Exception as err:
        log.exception("Unhandled bot error: %s", err)
        sys.exit(1)


if __name__ == "__main__":
    BotConfigurator.argparser()
    bot()
