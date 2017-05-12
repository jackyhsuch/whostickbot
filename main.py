from os import path, environ
from dotenv import load_dotenv

from telegram.ext import Updater
from telegram.ext import CommandHandler

import logging

# tag states
CHOOSING_TAG_ACTION = 0
ADDING_TAG = 1
DELETING_TAG = 2

# sticker states
CHOOSING_STICKER_TAG = 3
CHOOSING_STICKER_ACTION = 4
ADDING_STICKER = 5
DELETING_STICKER = 6

def main():
    try:
        dotenv_path = path.join(path.dirname(__file__), '.env')
        load_dotenv(dotenv_path)
    except Exception as e:
        raise

    # set environment
    updater = Updater(token=environ.get('TOKEN'))
    dispatcher = updater.dispatcher

    # logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)

    # tag mode handler
    tag_handler = ConversationHandler(
        entry_points=[CommandHandler('tag', tag, pass_user_data=True)],

        states={
            CHOOSING_TAG_ACTION: [RegexHandler('^Add new tag$',
                                    add_tag_action,
                                    pass_user_data=True),
                                ],

            ADDING_TAG: [MessageHandler(Filters.text,
                                           add_tag_to_db,
                                           pass_user_data=True),
                            ],
        },

        fallbacks=[RegexHandler('^Done$', done, pass_user_data=True)]
    )

    dispatcher.add_handler(tag_handler)

    # start poll
    updater.start_polling()
    updater.idle()


def tag(bot, update, user_data):
    # return inline keyboard to choose tag action (add or delete)
    user_id = update.message.from_user.id
    update.message.reply_text(user_id)

    return CHOOSING_TAG_ACTION

def add_tag_action(bot, update, user_data):
    # ask user for tag name input

    return ADDING_TAG

def add_tag_to_db(bot, update, user_data):
    # add tag to database

    return CHOOSING_TAG_ACTION


if __name__ == '__main__':
    main()