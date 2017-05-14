from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Tag, Sticker
    
class Database:
    def __init__(self, db_uri):
        engine = create_engine(db_uri)

        # connection = engine.connect()

        Session = sessionmaker(bind=engine)

        # initiate a session to db
        self.session = Session()

        # connection.close()

    def add_tag(self, tagObject):
        self.session.add(tagObject)
        self.session.commit()

        return

    def find_tag_by_user(self, user_uuid):
        result = self.session.query.filter(Tag.user_uuid == user_uuid)

        return result
