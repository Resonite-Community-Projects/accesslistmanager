from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
engine = create_engine('sqlite:///accesslist.db')
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'resonite_user'

    id = Column(Integer, primary_key=True)
    resonite_username = Column(Text, unique=True, nullable=False)
    discord_id = Column(Text, nullable=False)
    verifier = Column(Text, nullable=False)
    verified_date = Column(DateTime, default=datetime.utcnow)

    def __init__(
            self, resonite_username, discord_id, verifier,
            verified_date = None
    ):
        self.resonite_username = resonite_username
        self.discord_id = discord_id
        self.verifier = verifier
        if verified_date:
            self.verified_date = verified_date

    def __str__(self):
        return self.resonite_username

    def __repr__(self):
        return self.__str__()