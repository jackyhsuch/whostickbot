from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ParseMode, InlineQueryResultCachedSticker
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, CallbackQueryHandler, InlineQueryHandler, RegexHandler, Filters
from telegram.ext.dispatcher import run_async

from models import Tag, Sticker, UserSession
from database import Database
from environment import Environment
from uuid import uuid4

import logging
import json

NO_MODE = 0
NO_STATE = 0

TAG_MODE = 1
STICKER_MODE = 2

# tag states
TAG_ACTION_QUERY_WAITING_STATE = 1
TAG_ADD_WAITING_STATE = 2
TAG_DELETE_WAITING_STATE = 3

# sticker states
STICKER_TAG_QUERY_WAITING_STATE = 1
STICKER_ADD_WAITING_STATE = 2
STICKER_DELETE_WAITING_STATE = 3

environment = Environment()
database = Database(environment.DB_URI)

# logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)


def Main():
    # set environment
    updater = Updater(token=environment.TOKEN, workers=32)
    dispatcher = updater.dispatcher



    # # start - choosing tag or sticker mode
    # start_handler = CommandHandler('start', start)
    # dispatcher.add_handler(start_handler)

    # tag menu - choosing add/delete tag (using callbackquery)
    tag_handler = CommandHandler('tag', tag)
    dispatcher.add_handler(tag_handler)

    # tag add - adding tag name
    tag_add_handler = MessageHandler(Filters.text, tag_add)
    dispatcher.add_handler(tag_add_handler)




    # sticker menu - choose tag (using callbackquery)
    sticker_handler = CommandHandler('sticker', sticker)
    dispatcher.add_handler(sticker_handler)

    # sticker add - adding sticker to db
    sticker_add_handler = MessageHandler(Filters.sticker, sticker_add)
    dispatcher.add_handler(sticker_add_handler)



    # tag query - handle all the callback query of tag
    all_callback_query_handler = CallbackQueryHandler(all_callback_query)
    dispatcher.add_handler(all_callback_query_handler)




    # inline query
    dispatcher.add_handler(InlineQueryHandler(inlinequery))

    # log all errors
    dispatcher.add_error_handler(error)

    # start poll
    if environment.IS_PROD:
        updater.start_webhook(listen="0.0.0.0",
                                       port=environment.PORT,
                                       url_path=environment.TOKEN)
        updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(environment.APP_NAME, environment.TOKEN))
    else:
        updater.start_polling()

    updater.idle()


def check_session(user_id, mode, state):
    # if user_id in db check for mode and state
    userSessionObject = database.get_session_by_userid(user_id)

    # if not in db, add in new user session
    if not userSessionObject:
        userSessionObject = UserSession(user_id=user_id,
                        mode=NO_MODE,
                        state=NO_STATE)
        database.add_session(userSessionObject)

    if userSessionObject.mode == mode and userSessionObject.state == state:
        return userSessionObject
    
    return False

@run_async
def inlinequery(bot, update):
    tag_name = update.inline_query.query
    user_id = update.inline_query.from_user.id

    logger.info(user_id)
    logger.info(tag_name)

    results = list()

    # get tag id by user and tag name
    tagResult = database.get_tag_by_userid_and_tagname(user_id, tag_name)
    tagObject = tagResult.first()
    # get stickers by user uuid and tag id
    if tagObject is not None:
        stickerObjects = database.get_sticker_by_userid_and_tagid(user_id, tagObject.id)

        for stickerObject in stickerObjects:
            results.append(InlineQueryResultCachedSticker(id=stickerObject.id, sticker_file_id=stickerObject.sticker_uuid))
    
    update.inline_query.answer(results, is_personal=True, cache_time=0)


def start(bot, update):
    # let users choose tag mode or sticker mode
    mode_keyboard = [['/tag', '/sticker']]
    reply_markup = ReplyKeyboardMarkup(mode_keyboard, one_time_keyboard=True)

    update.message.reply_text("Choose mode:", reply_markup=reply_markup)


def sticker(bot, update):
    user_id = update.message.from_user.id

    #get all user's tag
    tagObjects = database.get_tag_by_userid(user_id)

    sticker_tag_keyboard = []
    for tagObject in tagObjects:
        callbackDict = {
            'id': tagObject.id,
            'name': tagObject.name
        }

        sticker_tag_keyboard.append([InlineKeyboardButton(tagObject.name, callback_data=json.dumps(callbackDict, ensure_ascii=False))])


    update.message.reply_text("Choose tag:", reply_markup=InlineKeyboardMarkup(sticker_tag_keyboard))

    database.update_session(user_id, STICKER_MODE, STICKER_TAG_QUERY_WAITING_STATE)

    return




def sticker_add(bot, update):
    user_id = update.message.from_user.id

    userSessionObject = check_session(user_id, STICKER_MODE, STICKER_ADD_WAITING_STATE)

    if userSessionObject:
        tag_id = userSessionObject.tag_id
        tag_name = database.get_tagname_by_tagid(tag_id)

        stickerObject = Sticker(sticker_uuid=update.message.sticker.file_id,
                                user_id=userSessionObject.user_id,
                                tag_id=userSessionObject.tag_id)
        database.add_sticker(stickerObject)

        # ask user to choose action - add more/done
        callbackDict = {
            'id': tag_id,
            'name': tag_name
        }

        sticker_add_keyboard = [[InlineKeyboardButton("Back", callback_data=json.dumps(callbackDict, ensure_ascii=False))],
                     [InlineKeyboardButton("Done", callback_data="sticker_done")]]

        update.message.reply_text('Sticker added!', reply_markup=InlineKeyboardMarkup(sticker_add_keyboard))

        database.update_session(user_id, STICKER_MODE, STICKER_TAG_QUERY_WAITING_STATE)

    
    userSessionObject = check_session(user_id, STICKER_MODE, STICKER_DELETE_WAITING_STATE)

    if userSessionObject:
        logger.info("here")
        sticker_to_delete_uuid = update.message.sticker.file_id
        tag_id = userSessionObject.tag_id
        tag_name = database.get_tagname_by_tagid(tag_id)

        database.delete_sticker_by_userid_and_tagid_stickeruuid(user_id, tag_id, sticker_to_delete_uuid)

        # ask user to choose action - add more/done
        callbackDict = {
            'id': tag_id,
            'name': tag_name
        }

        sticker_add_keyboard = [[InlineKeyboardButton("Back", callback_data=json.dumps(callbackDict, ensure_ascii=False))],
                     [InlineKeyboardButton("Done", callback_data="sticker_done")]]

        update.message.reply_text('Sticker deleted!', reply_markup=InlineKeyboardMarkup(sticker_add_keyboard))

        database.update_session(user_id, STICKER_MODE, STICKER_TAG_QUERY_WAITING_STATE)

    return


def tag(bot, update):
    user_id = update.message.from_user.id

    tag_action_keyboard = [[InlineKeyboardButton("Add tag", callback_data="tag_action_add")],
                 [InlineKeyboardButton("Delete tag", callback_data="tag_action_delete")]]

    update.message.reply_text("Choose action:", reply_markup=InlineKeyboardMarkup(tag_action_keyboard))

    database.update_session(user_id, TAG_MODE, TAG_ACTION_QUERY_WAITING_STATE)

    return


def tag_add(bot, update):
    user_id = update.message.from_user.id

    if check_session(user_id, TAG_MODE, TAG_ADD_WAITING_STATE):
        # add tag to database
        tagObject = Tag(user_id=user_id, name=update.message.text)
        database.add_tag(tagObject)

        # ask user to choose action - add more/done
        tag_action_keyboard = [[InlineKeyboardButton("Add more", callback_data="tag_action_add")],
                     [InlineKeyboardButton("Done", callback_data="tag_action_done")]]

        update.message.reply_text('"'+update.message.text+'" added!', reply_markup=InlineKeyboardMarkup(tag_action_keyboard))

        database.update_session(user_id, TAG_MODE, TAG_ACTION_QUERY_WAITING_STATE)

    return


def all_callback_query(bot, update):
    user_id = update.callback_query.from_user.id
    query = update.callback_query

    if check_session(user_id, TAG_MODE, TAG_ACTION_QUERY_WAITING_STATE):
        if query.data == "tag_action_add":
            query.message.reply_text("Enter tag name:")
            database.update_session(user_id, TAG_MODE, TAG_ADD_WAITING_STATE)

        if query.data == "tag_action_delete":
            query.message.reply_text("Choose tag:")
            database.update_session(user_id, TAG_MODE, TAG_DELETE_WAITING_STATE)

        if query.data == "tag_action_done":
            query.message.reply_text("Thank you for using WhoStickBot!")
            database.update_session(user_id, NO_MODE, NO_STATE)

    if check_session(user_id, STICKER_MODE, STICKER_TAG_QUERY_WAITING_STATE):
        userSessionObject = check_session(user_id, STICKER_MODE, STICKER_TAG_QUERY_WAITING_STATE)

        if query.data == "sticker_done":
            query.message.reply_text("Thank you for using WhoStickBot!")
            database.update_session(user_id, NO_MODE, NO_STATE)

        elif query.data == "sticker_action_add":
            if userSessionObject:
                tag_name = database.get_tagname_by_tagid(userSessionObject.tag_id)

                query.message.reply_text("Send sticker to tag it under *" + tag_name +"*", parse_mode=ParseMode.MARKDOWN)
                database.update_session(user_id, STICKER_MODE, STICKER_ADD_WAITING_STATE, userSessionObject.tag_id)

        elif query.data == "sticker_action_delete":
            if userSessionObject:
                tag_name = database.get_tagname_by_tagid(userSessionObject.tag_id)

                query.message.reply_text("Send sticker to delete it under *" + tag_name +"*", parse_mode=ParseMode.MARKDOWN)
                database.update_session(user_id, STICKER_MODE, STICKER_DELETE_WAITING_STATE, userSessionObject.tag_id)

        else:
            tag_dictionary = json.loads(query.data)

            sticker_action_keyboard = [[InlineKeyboardButton("Add sticker", callback_data="sticker_action_add")],
                 [InlineKeyboardButton("Delete sticker", callback_data="sticker_action_delete")]]

            query.message.reply_text("Choose action:", reply_markup=InlineKeyboardMarkup(sticker_action_keyboard))
            database.update_session(user_id, STICKER_MODE, STICKER_TAG_QUERY_WAITING_STATE, tag_dictionary['id'])

        
    return

# def tag_end(bot, update, user_data):
#     update.message.reply_text("Bye bye")
#     user_data.clear()

#     return ConversationHandler.END

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


if __name__ == '__main__':
    Main()