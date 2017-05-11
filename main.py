from os import path, environ
from dotenv import load_dotenv

from telegram.ext import Updater
from telegram.ext import CommandHandler

import logging

def main():
    try:
        dotenv_path = path.join(path.dirname(__file__), '.env')
        load_dotenv(dotenv_path)
    except Exception as e:
        raise


    updater = Updater(token=environ.get('TOKEN'))
    dispatcher = updater.dispatcher

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )


    start_handler = CommandHandler('new_tag', new_tag)
    dispatcher.add_handler(start_handler)

    updater.start_polling()
    updater.idle()

def new_tag(bot, update):
    user_id = update.message.from_user.id

    update.message.reply_text(user_id)

if __name__ == '__main__':
    main()