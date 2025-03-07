import yaml
from typing import Dict, Any
import os
import argparse
import pydash as _
from lib.constants import CONFIG_FILE
def bot_argparser():
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
        "--log-level", type=str, default=os.getenv("LOG_LEVEL", "INFO"), help="Log level"
    )
    parser.add_argument(
        "--download-log",
        type=str,
        default=os.getenv(
            "DOWNLOAD_LOG",
        ),
        help="Download history log file",
    )
    return parser.parse_args()


def load_config_file(path: str) -> Dict[str, Any]:
    with open(path, "r") as config_file:
        return yaml.load(config_file, Loader=yaml.FullLoader)

def build_config(args):
    config = load_config_file(args.config_file)
    args_list = {
        "bot.token": args.token,
        "bot.log_file": args.log,
        "bot.log_level": args.log_level,
        "bot.download_log_file": args.download_log,
        "transmission.host": args.transmission_host,
        "transmission.port": args.transmission_port,
        "transmission.user": args.transmission_user,
        "transmission.password": args.transmission_password,
    }
    for path, value in args_list.items():
        if not value:
            continue
        _.set_(config, path, value)
    
    return config