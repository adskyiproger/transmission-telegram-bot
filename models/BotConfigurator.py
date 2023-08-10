import asyncio
import threading
import pydash as _
from lib.func import get_logger
from telegram import Bot, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


log = get_logger("configurator")


class BotConfigurator():

    def __init__(self, config: str) -> None:
        self.config = config
        self.commands = None

    def validate(self) -> bool:
        failed_checks = []
        if not _.has(self.config, 'bot.token'):
            failed_checks.append("You must pass the token you received from https://t.me/Botfather!")
        if not ( _.has(self.config, 'transmission.host') and \
                 _.has(self.config, 'transmission.port') and \
                 _.has(self.config, 'transmission.user') and \
                 _.has(self.config, 'transmission.password')):
            failed_checks.append(
                "Provide transmission configuration options: host, user, password")
        if failed_checks:
            for check in failed_checks:
                log.critical(check)
            return False
        return True

    def get_keyboard(self, actions):
        if actions:
            return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=str(key)) for key in actions]],
                                       resize_keyboard=True)
        return ReplyKeyboardRemove()

    def set_bot_commands(self, commands):
        self.commands = commands
        _thread = threading.Thread(target=self._between_callback)
        _thread.start()

    def _between_callback(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self._set_bot_commands())
        loop.close()

    async def _set_bot_commands(self):
        await Bot(token=self.config['bot']['token']).set_my_commands(self.commands)
        log.info("Commands updated")
