import os
import yaml
import sys
import pydash as _
from typing import Dict, Any
import argparse
import shutil
from lib.func import get_logger
from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from lib.constants import CONFIG_FILE, BOT_FOLDER

log = get_logger("BotConfigurator")


class BotConfigurator:

    config_file = CONFIG_FILE
    args = None
    _runtime_overrides: Dict[str, Any] = {}

    def __init__(self) -> None:
        if not BotConfigurator.config_file:
            log.critical(
                "Please set BotConfigurator.config_file before instantiating class objects"
            )
            raise ValueError("BotConfigurator.config_file not set")
        self.commands = None
        self._config = None

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
            "are stored to configuration file and available for next run.",
        )
        parser.add_argument(
            "--config-file",
            type=str,
            default=os.getenv("CONFIG_FILE", CONFIG_FILE),
            help="Configuration file location",
        )
        parser.add_argument(
            "--token",
            type=str,
            default=os.getenv("TOKEN"),
            help="Token received from https://t.me/Botfather!",
        )
        parser.add_argument(
            "--super-user",
            type=int,
            default=os.getenv("SUPER_USER"),
            help="Telegram user ID allowed to administer the bot",
        )
        parser.add_argument(
            "--transmission-host",
            type=str,
            default=os.getenv("TRANSMISSION_HOST"),
            help="Transmission server host",
        )
        parser.add_argument(
            "--transmission-port",
            type=str,
            default=os.getenv("TRANSMISSION_PORT"),
            help="Transmission server port",
        )
        parser.add_argument(
            "--transmission-user",
            type=str,
            default=os.getenv("TRANSMISSION_USER"),
            help="User name for remote transmission authentication",
        )
        parser.add_argument(
            "--transmission-password",
            type=str,
            default=os.getenv("TRANSMISSION_PASSWORD"),
            help="Password for remote transmission user",
        )
        parser.add_argument(
            "--log",
            type=str,
            default=os.getenv("LOG_FILE", "logs/torrentino.log"),
            help="Log file location",
        )
        parser.add_argument(
            "--log-level", type=str, default=os.getenv("LOG_LEVEL"), help="Log level"
        )
        parser.add_argument(
            "--download-log",
            type=str,
            default=os.getenv(
                "DOWNLOAD_LOG",
            ),
            help="Download history log file",
        )
        BotConfigurator.args = parser.parse_args()
        BotConfigurator.config_file = BotConfigurator.args.config_file or CONFIG_FILE
        BotConfigurator._runtime_overrides = {
            "bot.token": BotConfigurator.args.token,
            "bot.super_user": BotConfigurator.args.super_user,
            "bot.log_file": BotConfigurator.args.log,
            "bot.log_level": BotConfigurator.args.log_level,
            "bot.download_log_file": BotConfigurator.args.download_log,
            "transmission.host": BotConfigurator.args.transmission_host,
            "transmission.port": BotConfigurator.args.transmission_port,
            "transmission.user": BotConfigurator.args.transmission_user,
            "transmission.password": BotConfigurator.args.transmission_password,
        }

    def init_args(self):
        """Apply CLI/environment values in memory without persisting secrets."""
        for path, value in BotConfigurator._runtime_overrides.items():
            if value is not None:
                _.set_(self._config, path, value)

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
                template_file = os.path.join(BOT_FOLDER, "templates", "torrentino.yaml")
                os.makedirs(os.path.dirname(BotConfigurator.config_file), exist_ok=True)
                shutil.copy(template_file, BotConfigurator.config_file)
                log.info(
                    "Created new configuration file from template: %s",
                    BotConfigurator.config_file,
                )
            except Exception as e:
                log.critical(
                    "Failed to create configuration file %s from template: %s due to error: %s",
                    BotConfigurator.config_file,
                    template_file,
                    e,
                )
                log.critical("Stopping bot startup...")
                sys.exit(1)
        with open(BotConfigurator.config_file, "r", encoding="utf-8") as config_file:
            self._config = yaml.safe_load(config_file) or {}
        self.init_args()

        return self._config

    def set(self, path: str, value: str) -> None:
        if not (value and value != _.get(self.config, path)):
            return
        _.set_(self._config, path, value)
        if path in {"bot.token", "transmission.password"} or path.endswith("password"):
            log.info("Updated sensitive configuration value: %s", path)
        else:
            log.info("Updated configuration value: %s = %s", path, value)
        self.save_config()

    def get(self, path: str | list[str], default: Any = None) -> Any:
        return _.get(self.config, path, default)

    def save_config(self) -> None:
        log.info("Updating configuration file: %s", self.config_file)
        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(self._config, f, sort_keys=False, allow_unicode=True)

    def validate(self) -> bool:
        failed_checks = []
        warning_checks = []
        if not self.get("bot.token"):
            failed_checks.append(
                "You must pass the token you received from https://t.me/Botfather!"
            )
        if not self.get("bot.super_user"):
            failed_checks.append(
                "Set bot.super_user, SUPER_USER, or --super-user before starting the bot"
            )
        if not all(
            [
                self.get("transmission.host"),
                self.get("transmission.port"),
                self.get("transmission.user"),
                self.get("transmission.password"),
            ]
        ):
            warning_checks.append("Provide Transmission host, port, user, and password")
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
            return ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=str(key)) for key in actions]],
                resize_keyboard=True,
            )
        return ReplyKeyboardRemove()

    def get_downloads_keyboard(self) -> InlineKeyboardMarkup:
        # Download directories
        # Transmission server needs write access to these directories
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(key.capitalize(), callback_data=value)
                    for key, value in dict(self.config["directories"]).items()
                ]
            ]
        )

    def set_bot_commands(self, commands) -> "BotConfigurator":
        """Store commands to synchronize during application startup."""
        self.commands = commands
        return self

    def add_user(self, user_id: int) -> "BotConfigurator":
        if user_id not in self.config["bot"]["allowed_users"]:
            log.info("Adding user_id %s to allowed users", user_id)
            self._config["bot"]["allowed_users"].append(user_id)
            self.save_config()
        return self
