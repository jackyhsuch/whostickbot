from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Tag, Sticker, UserSession
    
class Database:
    def __init__(self, db_uri):
        engine = create_engine(db_uri)
        Session = sessionmaker(bind=engine)

        # initiate a session to db
        self.session = Session()


    def add_tag(self, tagObject):
        self.session.add(tagObject)
        self.session.commit()

        return


    def add_sticker(self, stickerObject):
        self.session.add(stickerObject)
        self.session.commit()

        return

    def delete_sticker_by_userid_and_tagid_stickeruuid(self, user_id, tag_id, sticker_uuid):
        stickerObject = self.session.query(Sticker).filter_by(user_id=user_id, tag_id=tag_id, sticker_uuid=sticker_uuid).first()
        self.session.delete(stickerObject)
        self.session.commit()

        return

    def delete_tag_by_id(self, tag_id):
        tagObject = self.session.query(Tag).get(tag_id)
        self.session.delete(tagObject)

        # delete all the stickers tagged under the tag_id
        stickerObjects = self.session.query(Sticker).filter_by(tag_id=tag_id)
        if stickerObjects.first():
            self.session.delete(stickerObjects)

        self.session.commit()

        return


    def get_tag_by_userid(self, user_id):
        result = self.session.query(Tag).filter(Tag.user_id == user_id)

        return result


    def get_tag_by_userid_and_tagname(self, user_id, tag_name):
        result = self.session.query(Tag).filter(Tag.user_id == user_id, Tag.name.like(tag_name + "%"))

        return result

    def get_tagname_by_tagid(self, tag_id):
        result = self.session.query(Tag).filter(Tag.id == tag_id)

        return result.first().name


    def get_sticker_by_userid_and_tagid(self, user_id, tag_id):
        result = self.session.query(Sticker).filter(Sticker.user_id == user_id, Sticker.tag_id == tag_id)

        return result


    def add_session(self, userSessionObject):
        self.session.add(userSessionObject)
        self.session.commit()

        return


    def get_session_by_userid(self, user_id):
        result = self.session.query(UserSession).filter_by(user_id=user_id)

        return result.first()


    def update_session(self, user_id, state, tag_id=0):
        userSessionObject = self.session.query(UserSession).filter_by(user_id=user_id).first()

        userSessionObject.state = state
        userSessionObject.tag_id = tag_id

        self.session.commit()

        return