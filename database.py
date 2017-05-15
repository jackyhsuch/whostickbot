from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Tag, Sticker
    
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


    def find_tag_by_user(self, user_uuid):
        result = self.session.query(Tag).filter(Tag.user_uuid == user_uuid)

        return result
