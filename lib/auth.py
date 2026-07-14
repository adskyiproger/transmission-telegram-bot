from functools import wraps
import pydash as _
from telegram import Update
from telegram.ext import ContextTypes

from models.BotConfigurator import BotConfigurator
from lib.func import get_logger, trans

bot_config = BotConfigurator()
# config = bot_config.config

# log_file = _.get(bot_config.config, 'bot.log_file')
log = get_logger("Authentication")


def restricted(func):
    @wraps(func)
    async def wrapped(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        user_id = update.effective_user.id
        super_user = bot_config.get("bot.super_user")
        if not super_user:
            log.critical("Access denied because bot.super_user is not configured")
            await context.bot.send_message(
                chat_id=user_id,
                text=trans("ACCESS_RESTRICTED", update.effective_user.language_code),
            )
            return
        # Check if user is allowed
        is_allowed_user = user_id in _.get(bot_config.config, "bot.allowed_users", [])
        if not is_allowed_user and user_id != super_user:
            log.debug(update)

            await context.bot.send_message(
                chat_id=user_id,
                text=trans("ACCESS_RESTRICTED", update.effective_user.language_code),
            )
            log.error("User %s is not authorized", user_id)
            return
        # If user is authorized, then execute wrapped function
        return await func(update, context, *args, **kwargs)

    return wrapped
