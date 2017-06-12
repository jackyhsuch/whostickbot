from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    name = Column(String)


class Sticker(Base):
    __tablename__ = 'stickers'

    id = Column(Integer, primary_key=True)
    sticker_uuid = Column(String)
    user_id = Column(Integer)
    tag_id = Column(Integer)


class UserSession(Base):
    __tablename__ = 'sessions'

    user_id = Column(Integer, primary_key=True)
    state = Column(Integer)
    mode = Column(Integer)
    tag_id = Column(Integer)