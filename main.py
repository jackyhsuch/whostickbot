from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ParseMode
from telegram.ext import Updater
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, CallbackQueryHandler, RegexHandler, Filters

from models import Tag
from database import Database
from environment import Environment

import logging

# tag states
CHOOSING_TAG_ACTION = 0
ADDING_TAG = 1
DELETING_TAG = 2

# sticker states
CHOOSING_STICKER = 3
CHOOSING_STICKER_ACTION = 4
ADDING_STICKER = 5
DELETING_STICKER = 6

environment = Environment()
database = Database(environment.DB_URI)


def Main():
    # set environment
    updater = Updater(environment.TOKEN)
    dispatcher = updater.dispatcher

    # logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG
    )
    logger = logging.getLogger(__name__)

    # main menu
    dispatcher.add_handler(CommandHandler("start", start))



    ### tag mode handler ########################################
    tag_handler = ConversationHandler(
        entry_points=[CommandHandler('tag', tag, pass_user_data=True)],

        states={
            CHOOSING_TAG_ACTION: [CallbackQueryHandler(choose_tag_action,
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
    #############################################################

    ### stciker mode handler ####################################
    sticker_handler = ConversationHandler(
        entry_points=[CommandHandler('sticker', sticker, pass_user_data=True)],

        states={
            CHOOSING_STICKER: [CallbackQueryHandler(choose_sticker,
                                    pass_user_data=True),
                            ],

            ADDING_STICKER: [MessageHandler(Filters.sticker,
                                add_sticker_to_db,
                                pass_user_data=True),
                            ],

        },

        fallbacks=[RegexHandler('^end$', tag_end, pass_user_data=True)]
    )

    dispatcher.add_handler(sticker_handler)
    #############################################################


    # log all errors
    dispatcher.add_error_handler(error)

    # start poll
    updater.start_polling()
    updater.idle()


def start(bot, update):
    # let users choose tag mode or sticker mode
    mode_keyboard = [['/tag', '/sticker']]
    reply_markup = ReplyKeyboardMarkup(mode_keyboard, one_time_keyboard=True)

    update.message.reply_text("Choose mode:", reply_markup=reply_markup)


def sticker(bot, update, user_data):
    user_data['id'] = update.message.from_user.id

    #get all user's tag
    tagObjects = database.find_tag_by_user(user_data['id'])

    sticker_tag_keyboard = []
    for tagObject in tagObjects:
        sticker_tag_keyboard.append([InlineKeyboardButton(tagObject.name, callback_data=tagObject.name)])


    update.message.reply_text("Choose tag:", reply_markup=InlineKeyboardMarkup(sticker_tag_keyboard))

    return CHOOSING_STICKER


def choose_sticker(bot, update, user_data):
    query = update.callback_query
    query.message.reply_text("Send me sticker to tag it under *" + query.data +"*", parse_mode=ParseMode.MARKDOWN)

    return ADDING_STICKER


def add_sticker_to_db(bot, update, user_data):
    pass


def tag(bot, update, user_data):
    # return inline keyboard to choose tag action (add or delete)
    tag_action_keyboard = [[InlineKeyboardButton("Add tag", callback_data="tag_action_0"),
                 InlineKeyboardButton("Delete tag", callback_data="tag_action_1")]]

    update.message.reply_text("Choose action:", reply_markup=InlineKeyboardMarkup(tag_action_keyboard))

    user_data['id'] = update.message.from_user.id

    return CHOOSING_TAG_ACTION


def choose_tag_action(bot, update, user_data):
    query = update.callback_query

    if query.data == "tag_action_0":
        query.message.reply_text("Enter tag name (or /back):")
        return ADDING_TAG

    if query.data == "tag_action_1":
        query.message.reply_text("Choose tag (or /back):")
        return DELETING_TAG


def add_tag_to_db(bot, update, user_data):
    # add tag to database
    tagObject = Tag(user_uuid=user_data['id'] , name=update.message.text)
    database.add_tag(tagObject)

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
    Main()