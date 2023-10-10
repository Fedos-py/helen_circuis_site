import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

"""

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(250), nullable=False)
    
class Basket(Base):
    __tablename__ = 'basket'

    id = Column(Integer, primary_key=True, autoincrement=True)
    hall_id = Column(Integer, nullable=False)
    user_id = Column(String, nullable=False)
    place = Column(String(250), nullable=False)
    status = Column(String(250), nullable=False)
    time = Column(String(250), nullable=False)



class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(250), nullable=False)
    locality = Column(String(250), nullable=False)
    location = Column(String(250), nullable=False)
    date = Column(String(250), nullable=False)
    time = Column(String(250), nullable=False)
    price = Column(Integer)
    hall_length = Column(String(250))
    hall_width = Column(String(250))
"""
class Hall(Base):
    __tablename__ = 'halls'

    hall_id = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(Integer, nullable=False)
    place = Column(String(250), nullable=False)
    status = Column(String(250), nullable=False)
    reserver = Column(String(250), nullable=False)

engine = create_engine('sqlite:///db/events.db')

Base.metadata.create_all(engine)