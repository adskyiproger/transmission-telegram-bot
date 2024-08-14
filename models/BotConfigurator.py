import os
import yaml
import sys
import asyncio
import pydash as _
from typing import Dict, Any
import argparse
import shutil
from lib.func import get_logger
from telegram import (Bot,
                      ReplyKeyboardMarkup,
                      KeyboardButton,
                      ReplyKeyboardRemove,
                      InlineKeyboardMarkup,
                      InlineKeyboardButton)
from telegram.error import InvalidToken
from lib.constants import CONFIG_FILE, BOT_FOLDER

log = get_logger("BotConfigurator")


class BotConfigurator():

    config_file = CONFIG_FILE
    args = None
    _init_args = False


    def __init__(self) -> None:
        if not BotConfigurator.config_file:
            log.critical("Please set BotConfigurator.config_file before instantiating class objects")
            raise ValueError("BotConfigurator.config_file not set")
        self.commands = None
        self._config = None

        if BotConfigurator._init_args:
            # Make sure this logic will run only once
            BotConfigurator._init_args = False
            self.init_args()

    @staticmethod
    def argparser():
        """
        Method is used to parse CLI input and environment variables and merge
        input data with existing values in configuration file.

        NOTE: Most properties can be changed only inside configuration file.

        Values precedence:
        - CLI
        - Environemnt variables
        - Configuration file
        """

        parser = argparse.ArgumentParser(
            prog="Torrentino",
            description="Torrentino configuration options: ",
            epilog="Passed as command line arguments or environment variables"
                   "are stored to configuration file and available for next run.")
        parser.add_argument('--config', type=str,
                            default=os.getenv("CONFIG_FILE", CONFIG_FILE),
                            help='Configuration file location')
        parser.add_argument('--token', type=str, default=os.getenv("TOKEN"),
                            help='Token received from https://t.me/Botfather!')
        parser.add_argument('--transmission-host', type=str, 
                            default=os.getenv("TRANSMISSION_HOST"),
                            help='Transmission server host')
        parser.add_argument('--transmission-port', type=str, 
                            default=os.getenv("TRANSMISSION_PORT"),
                            help='Transmission server port')
        parser.add_argument('--transmission-user', type=str,
                            default=os.getenv("TRANSMISSION_USER"),
                            help='User name for remote transmission authentication')
        parser.add_argument('--transmission-password', type=str,
                            default=os.getenv("TRANSMISSION_PASSWORD"),
                            help='Password for remote transmission user')
        parser.add_argument('--log', type=str,
                            default=os.getenv("LOG_FILE", 'logs/torrentino.log'),
                            help='Log file location')
        parser.add_argument('--log-level', type=str,
                            default=os.getenv("LOG_LEVEL"),
                            help='Log level')
        parser.add_argument('--download-log', type=str,
                            default=os.getenv("DOWNLOAD_LOG", ),
                            help='Download history log file')
        BotConfigurator.args = parser.parse_args()
        BotConfigurator.config_file = BotConfigurator.args.config or CONFIG_FILE
        BotConfigurator._init_args = True

    def init_args(self):
        args = BotConfigurator.args
        args_list = {
            'bot.token': args.token,
            'bot.log_file': args.log,
            'bot.log_level': args.log_level,
            'bot.download_log_file': args.download_log,
            'transmission.host': args.transmission_host,
            'transmission.port': args.transmission_port,
            'transmission.user': args.transmission_user,
            'transmission.password': args.transmission_password,
        }
        for k in args_list:
            self.set(k, args_list[k])

    @property
    def config(self) -> Dict:
        """
        Return configuration file as dict:
        - if file doesn't exist, create new file from template
        """
        if self._config:
            return self._config
        if not os.path.exists(BotConfigurator.config_file):
            log.info("Configuration file %s not found", BotConfigurator.config_file)
            try:
                shutil.copy(os.path.join(BOT_FOLDER, 'templates', 'torrentino.template.yaml'), BotConfigurator.config_file)
                log.info("Created new configuration file from template: %s", BotConfigurator.config_file)
            except Exception as e:
                log.critical("Configuration file %s not found. Failed to create configuration file from template",
                            BotConfigurator.config_file)
                sys.exit(1)
        with open(BotConfigurator.config_file, 'r') as config_file:
            self._config = yaml.load(config_file, Loader=yaml.FullLoader)

        return self._config

    def set(self, path: str, value: str) -> None:
        if not (value and value != _.get(self.config, path)):
            return
        _.set_(self._config, path, value)
        log.info('Added configuration value: %s = %s', path, value)
        self.save_config()

    def get(self, path: str, default: Any = None) -> Dict:
        return _.get(self.config, path, default)

    def save_config(self) -> None:
        log.info("Updating configuration file: %s", self.config_file)
        with open(self.config_file, 'w') as f:
            yaml.dump(self._config, f)

    def validate(self) -> bool:
        failed_checks = []
        warning_checks = []
        if not _.has(self.config, 'bot.token'):
            warning_checks.append("You must pass the token you received from https://t.me/Botfather!")
        if not (_.has(self.config, 'transmission.host')
                and _.has(self.config, 'transmission.port')
                and _.has(self.config, 'transmission.user')
                and _.has(self.config, 'transmission.password')):
            warning_checks.append(
                "Provide add transmission configuration options to configuration file: host, user, password")
        if warning_checks:
            for check in warning_checks:
                log.warning(check)
        if failed_checks:
            for check in failed_checks:
                log.critical(check)
            return False
        return True

    def get_actions_keyboard(self, actions) -> ReplyKeyboardMarkup:
        if actions:
            return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=str(key)) for key in actions]],
                                       resize_keyboard=True)
        return ReplyKeyboardRemove()

    def get_downloads_keyboard(self) -> InlineKeyboardMarkup:
        # Download directories
        # Transmission server needs write access to these directories
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton(key.capitalize(), callback_data=value) for key, value in dict(self.config['directories']).items()]])

    def set_bot_commands(self, commands) -> "BotConfigurator":
        """Adds/Updates Bot menu commands"""
        self.commands = commands
        loop = asyncio.get_event_loop()
        coroutine = Bot(token=self.config['bot']['token']).set_my_commands(self.commands)
        try:
            loop.run_until_complete(coroutine)
        except InvalidToken as err:
            log.critical("Invalid token provided: %s", str(err))
            sys.exit(1)
        except Exception as err:
            log.critical("Generic error occured: %s", str(err))
        log.info("Synchronized bots's commands: \n - %s", "\n - ".join([':\t\t'.join(c) for c in self.commands]))
        return self

    def add_user(self, id: int) -> "BotConfigurator":
        if id not in self._config['bot']['allowed_users']:
            log.info("Adding user_id %s to allowed users", id)
            self._config['bot']['allowed_users'].append(id)
            self.save_config()
            return self
