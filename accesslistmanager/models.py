from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
engine = create_engine('sqlite:///accesslist.db')
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'neos_user'

    id = Column(Integer, primary_key=True)
    neos_username = Column(Text, unique=True, nullable=False)
    discord_id = Column(Text, nullable=False)
    verifier = Column(Text, nullable=False)
    verified_date = Column(DateTime, default=datetime.utcnow)

    def __init__(
            self, neos_username, discord_id, verifier,
            verified_date = None
    ):
        self.neos_username = neos_username
        self.discord_id = discord_id
        self.verifier = verifier
        if verified_date:
            self.verified_date = verified_date

    def __str__(self):
        return self.neos_username

    def __repr__(self):
        return self.__str__()