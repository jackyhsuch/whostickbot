from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    user_uuid = Column(Integer)
    name = Column(String)


class Sticker(Base):
    __tablename__ = 'stickers'

    id = Column(Integer, primary_key=True)
    sticker_uuid = Column(Integer)
    user_uuid = Column(Integer)
    tag_id = Column(Integer)