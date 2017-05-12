from os import path, environ
from dotenv import load_dotenv

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, CallbackQueryHandler, RegexHandler, Filters

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
        level=logging.DEBUG
    )
    logger = logging.getLogger(__name__)

    # tag mode handler
    tag_handler = ConversationHandler(
        entry_points=[CommandHandler('tag', tag, pass_user_data=True)],

        states={
            CHOOSING_TAG_ACTION: [CallbackQueryHandler(tag_action_handler,
                                    pass_user_data=True),
                                ],

            ADDING_TAG: [MessageHandler(Filters.text,
                            add_tag_to_db,
                            pass_user_data=True),
                        CommandHandler('back', tag, pass_user_data=True),
                        ],
        },

        fallbacks=[RegexHandler('^end$', tag_end, pass_user_data=True)]
    )

    dispatcher.add_handler(tag_handler)

    # log all errors
    dispatcher.add_error_handler(error)

    # start poll
    updater.start_polling()
    updater.idle()


def tag(bot, update, user_data):
    # return inline keyboard to choose tag action (add or delete)
    tag_action_keyboard = [[InlineKeyboardButton("Add tag", callback_data="tag_action_0"),
                 InlineKeyboardButton("Delete tag", callback_data="tag_action_1")]]

    update.message.reply_text("Choose action:", reply_markup=InlineKeyboardMarkup(tag_action_keyboard))

    user_data['id'] = update.message.from_user.id


    return CHOOSING_TAG_ACTION

def tag_action_handler(bot, update, user_data):
    query = update.callback_query

    if query.data == "tag_action_0":
        query.message.reply_text("Enter tag name (or /back):")
        return ADDING_TAG

    if query.data == "tag_action_1":
        query.message.reply_text("Choose tag:")
        return DELETING_TAG


def add_tag_to_db(bot, update, user_data):
    # add tag to database

    # send msg to user
    update.message.reply_text("Enter tag name (or /back):")

    return ADDING_TAG

def tag_end(bot, update, user_data):
    update.message.reply_text("Bye bye")
    user_data.clear()

    return ConversationHandler.END

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


if __name__ == '__main__':
    main()