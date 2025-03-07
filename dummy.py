from models.Config import Config as config
from lib.config_tools import bot_argparser, build_config
if __name__ == "__main__":
    args = bot_argparser()
    bot_config = build_config(args)
    print(bot_config)
    # bot()
