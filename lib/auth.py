from functools import wraps
import pydash as _
from telegram import Update
from telegram.ext import ContextTypes

from models.BotConfigurator import BotConfigurator
from lib.func import get_logger, trans

bot_config = BotConfigurator()
# config = bot_config.config

log_file = _.get(bot_config.config, 'bot.log_file')
log = get_logger("Authentication", log_file)

def restricted(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        # Add super user at first run
        if not _.has(bot_config.config, 'bot.super_user'):
            log.warning(f"Adding new super user {user_id}")
            bot_config.set('bot.super_user', user_id)
            bot_config.save_config()
        # Check if user is allowed
        if user_id not in _.get(bot_config.config, 'bot.allowed_users', []) and user_id != _.get(bot_config.config, 'bot.super_user'):
            log.debug(update)

            await context.bot.send_message(chat_id=user_id,
                                     text=trans('ACCESS_RESTRICTED', update.message.from_user.language_code))
            log.error("User %s is not authorized",user_id)
            return
        # If user is authorized, then execute wrapped function
        return await func(update, context, *args, **kwargs)
    return wrapped

