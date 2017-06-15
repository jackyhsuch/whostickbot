from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ParseMode, InlineQueryResultCachedSticker
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, CallbackQueryHandler, InlineQueryHandler, RegexHandler, Filters
from telegram.ext.dispatcher import run_async

from models import Tag, Sticker, UserSession
from database import Database
from environment import Environment
from uuid import uuid4

import logging
import json

NO_STATE = 0

# tag states
TAG_ACTION_QUERY_WAITING_STATE = 1
TAG_ADD_WAITING_STATE = 2
TAG_DELETE_WAITING_STATE = 3

# sticker states
STICKER_TAG_WAITING_STATE = 4
STICKER_ACTION_WAITING_STATE = 5
STICKER_ADD_WAITING_STATE = 6
STICKER_DELETE_WAITING_STATE = 7

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

    # start - choosing tag or sticker mode
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
    # create new tag
    newtag_handler = CommandHandler('newTag', newtag)
    dispatcher.add_handler(newtag_handler)
    # delete tag
    deletetag_handler = CommandHandler('deleteTag', deletetag)
    dispatcher.add_handler(deletetag_handler)
    # edit tag - add stickers
    edittag_handler = CommandHandler('editTag', edittag)
    dispatcher.add_handler(edittag_handler)
    # end - exit bot
    end_handler = CommandHandler('end', end)
    dispatcher.add_handler(end_handler)


    # tag add - adding tag name
    tag_add_handler = MessageHandler(Filters.text, tag_add)
    dispatcher.add_handler(tag_add_handler)
    # sticker add - adding sticker to db
    sticker_action_handler = MessageHandler(Filters.sticker, sticker_action)
    dispatcher.add_handler(sticker_action_handler)


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


def check_new_user(user_id):
    userSessionObject = database.get_session_by_userid(user_id)

    if not userSessionObject:
        userSessionObject = UserSession(user_id=user_id, state=NO_STATE)
        database.add_session(userSessionObject)


def check_session(user_id, state):
    # if user_id in db check for mode and state
    userSessionObject = database.get_session_by_userid(user_id)

    # if not in db, add in new user session
    if not userSessionObject:
        userSessionObject = UserSession(user_id=user_id, state=NO_STATE)
        database.add_session(userSessionObject)

    if userSessionObject.state == state:
        return userSessionObject
    
    return False

@run_async
def inlinequery(bot, update):
    tag_name = update.inline_query.query.lower()
    user_id = update.inline_query.from_user.id

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
    user_id = update.message.from_user.id
    check_new_user(user_id)

    update.message.reply_text("Welcome to WhoStickBot!\n\n/newTag : to add tag\n/editTag : to add stickers\n/deleteTag : to delete tag\n/end : to exit bot", parse_mode=ParseMode.MARKDOWN)

    return

def newtag(bot, update):
    user_id = update.message.from_user.id
    check_new_user(user_id)

    update.message.reply_text("Enter tag name:")
    database.update_session(user_id, TAG_ADD_WAITING_STATE)

    return


def deletetag(bot, update):
    user_id = update.message.from_user.id
    check_new_user(user_id)

    #get all user's tag
    tagObjects = database.get_tag_by_userid(user_id)

    tag_keyboard = []
    for tagObject in tagObjects:
        callbackDict = {
            'id': tagObject.id,
            'name': tagObject.name
        }

        tag_keyboard.append([InlineKeyboardButton(tagObject.name, callback_data=json.dumps(callbackDict, ensure_ascii=False))])


    update.message.reply_text("Choose tag to delete:", reply_markup=InlineKeyboardMarkup(tag_keyboard))

    database.update_session(user_id, TAG_DELETE_WAITING_STATE)

    return


def edittag(bot, update):
    user_id = update.message.from_user.id
    check_new_user(user_id)

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

    database.update_session(user_id, STICKER_TAG_WAITING_STATE)

    return


def sticker_action(bot, update):
    user_id = update.message.from_user.id

    userSessionObject = check_session(user_id, STICKER_ADD_WAITING_STATE)
    if userSessionObject:
        tag_id = userSessionObject.tag_id

        stickerObject = Sticker(sticker_uuid=update.message.sticker.file_id,
                                user_id=userSessionObject.user_id,
                                tag_id=userSessionObject.tag_id)
        database.add_sticker(stickerObject)

        update.message.reply_text("Sticker added!\nContinue sending to add more!\n\n/end : exit bot", parse_mode=ParseMode.MARKDOWN)

        database.update_session(user_id, STICKER_ADD_WAITING_STATE, tag_id)

    
    userSessionObject = check_session(user_id, STICKER_DELETE_WAITING_STATE)
    if userSessionObject:
        sticker_to_delete_uuid = update.message.sticker.file_id
        tag_id = userSessionObject.tag_id

        database.delete_sticker_by_userid_and_tagid_stickeruuid(user_id, tag_id, sticker_to_delete_uuid)

        update.message.reply_text("Sticker deleted!\nContinue sending to delete more!\n\n/end : exit bot", parse_mode=ParseMode.MARKDOWN)

        database.update_session(user_id, STICKER_DELETE_WAITING_STATE, tag_id)

    return


def tag_add(bot, update):
    user_id = update.message.from_user.id

    if check_session(user_id, TAG_ADD_WAITING_STATE):
        # add tag to database
        tagObject = Tag(user_id=user_id, name=update.message.text.lower())
        database.add_tag(tagObject)

        update.message.reply_text("/editTag : add sticker to tag\n/newTag : add more tags\n/end : exit bot", parse_mode=ParseMode.MARKDOWN)
        database.update_session(user_id, TAG_ACTION_QUERY_WAITING_STATE)

    return


def all_callback_query(bot, update):
    user_id = update.callback_query.from_user.id
    query = update.callback_query

    userSessionObject = check_session(user_id, STICKER_ACTION_WAITING_STATE)
    if userSessionObject:
        if query.data == "sticker_action_add":
            tag_name = database.get_tagname_by_tagid(userSessionObject.tag_id)

            query.message.reply_text("Send sticker to tag it under *" + tag_name +"*", parse_mode=ParseMode.MARKDOWN)
            database.update_session(user_id, STICKER_ADD_WAITING_STATE, userSessionObject.tag_id)

        elif query.data == "sticker_action_delete":
            tag_name = database.get_tagname_by_tagid(userSessionObject.tag_id)

            query.message.reply_text("Send sticker to delete it under *" + tag_name +"*", parse_mode=ParseMode.MARKDOWN)
            database.update_session(user_id, STICKER_DELETE_WAITING_STATE, userSessionObject.tag_id)


    userSessionObject = check_session(user_id, STICKER_TAG_WAITING_STATE)
    if userSessionObject:
        tag_dictionary = json.loads(query.data)

        sticker_action_keyboard = [[InlineKeyboardButton("Add sticker", callback_data="sticker_action_add")],
             [InlineKeyboardButton("Delete sticker", callback_data="sticker_action_delete")]]

        query.message.reply_text("Choose action:", reply_markup=InlineKeyboardMarkup(sticker_action_keyboard))
        database.update_session(user_id, STICKER_ACTION_WAITING_STATE, tag_dictionary['id'])


    userSessionObject = check_session(user_id, TAG_DELETE_WAITING_STATE)
    if userSessionObject:
        tag_dictionary = json.loads(query.data)
        tag_id = tag_dictionary['id']

        database.delete_tag_by_id(tag_id)

        query.message.reply_text("/deleteTag : delete more tags\n/end : exit bot", parse_mode=ParseMode.MARKDOWN)
        database.update_session(user_id, NO_STATE)

    return

def end(bot, update):
    update.message.reply_text("Thank you for using WhoStickBot!")
    database.update_session(update.message.from_user.id, NO_STATE)

    return

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


if __name__ == '__main__':
    Main()