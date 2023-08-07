import asyncio
import threading
from lib.func import get_logger
from telegram import Bot, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


log = get_logger("configurator")


class BotConfigurator():

    def __init__(self, token: str) -> None:
        self.token = token
        self.commands = None

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
        await Bot(token=self.token).set_my_commands(self.commands)
        log.info("Commands updated")
