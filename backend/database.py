from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./library.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

Base = declarative_base()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from sqlalchemy import Column, Integer, String

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    author = Column(String)
    genre = Column(String)
    publication = Column(String, nullable=True)
    available_quantity = Column(Integer)
    reserved_quantity = Column(Integer)
    issued_quantity = Column(Integer)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)
    class_name = Column(String, nullable=True)   # e.g. FY, SY, TY, 11th, 12th
    roll_no = Column(String, nullable=True)
    course = Column(String, nullable=True)        # e.g. BSc CS, IT, BA, B.Com


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer)
    username = Column(String)
    status = Column(String)              # "reserved", "issued", or "returned"
    reserved_on = Column(String)
    issued_on = Column(String, nullable=True)
    returned_on = Column(String, nullable=True)
    extended_days = Column(Integer, default=0)   # set to 7 if renewed once
    fine_amount = Column(Integer, default=0)
    fine_paid = Column(Integer, default=0)         # 0 = unpaid, 1 = paid
    damaged = Column(Integer, default=0)          # 0 = no, 1 = yes
    rating = Column(Integer, nullable=True)        # 1-5, given after return


class Wishlist(Base):
    __tablename__ = "wishlist"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer)
    username = Column(String)
    added_on = Column(String)


class BookRequest(Base):
    __tablename__ = "book_requests"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    title = Column(String)
    author = Column(String, nullable=True)
    requested_on = Column(String)
    status = Column(String, default="pending")   # "pending" or "fulfilled"


Base.metadata.create_all(bind=engine)