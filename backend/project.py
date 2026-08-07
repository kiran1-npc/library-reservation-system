from passlib.context import CryptContext
from database import Base, engine, SessionLocal, Book, User, Reservation
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class NewBook(BaseModel):
    title: str
    author: str
    genre: str
    quantity: int


class NewUser(BaseModel):
    username: str
    password: str
    role: str


class LoginUser(BaseModel):
    username: str
    password: str


@app.get("/books")
def get_books():
    db = SessionLocal()
    books = db.query(Book).all()
    db.close()
    return books


@app.get("/books/{book_id}")
def get_book(book_id: int):
    db = SessionLocal()
    book = db.query(Book).filter(Book.id == book_id).first()
    db.close()
    if book:
        return book
    return {"error": "Book not found"}


@app.post("/books")
def add_book(new_book: NewBook, username: str):
    db = SessionLocal()

    user = db.query(User).filter(User.username == username).first()
    if not user or user.role != "admin":
        db.close()
        return {"error": "Only admins can add books"}

    book = Book(
        title=new_book.title,
        author=new_book.author,
        genre=new_book.genre,
        available_quantity=new_book.quantity,
        reserved_quantity=0,
        issued_quantity=0
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    db.close()
    return {"message": f"Book '{book.title}' has been added with {book.available_quantity} copies.", "book": book}


@app.post("/books/{book_id}/reserve")
def reserve_book(book_id: int, username: str):
    db = SessionLocal()

    user = db.query(User).filter(User.username == username).first()
    if not user:
        db.close()
        return {"error": "You must be logged in to reserve a book"}

    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        db.close()
        return {"error": "Book not found"}

    if book.available_quantity > 0:
        book.available_quantity -= 1
        book.reserved_quantity += 1

        new_reservation = Reservation(
            book_id=book.id,
            username=username,
            status="reserved",
            reserved_on=date.today().isoformat(),
            issued_on=None
        )
        db.add(new_reservation)

        db.commit()
        title = book.title
        db.close()
        return {"message": f"Book '{title}' has been reserved."}
    else:
        title = book.title
        db.close()
        return {"error": "No copies available for reservation."}


@app.get("/books/{book_id}/reservations")
def get_book_reservations(book_id: int):
    db = SessionLocal()
    reservations = db.query(Reservation).filter(
        Reservation.book_id == book_id,
        Reservation.status.in_(["reserved", "issued"])
    ).all()
    db.close()
    return reservations


@app.get("/my-reservations/{username}")
def my_reservations(username: str):
    db = SessionLocal()
    reservations = db.query(Reservation).filter(Reservation.username == username).all()

    results = []
    for r in reservations:
        book = db.query(Book).filter(Book.id == r.book_id).first()
        if book:
            results.append({
                "id": r.id,
                "book_title": book.title,
                "author": book.author,
                "status": r.status,
                "reserved_on": r.reserved_on,
                "issued_on": r.issued_on
            })

    db.close()
    return results


@app.post("/reservations/{reservation_id}/cancel")
def cancel_reservation(reservation_id: int, username: str):
    db = SessionLocal()

    user = db.query(User).filter(User.username == username).first()
    if not user:
        db.close()
        return {"error": "You must be logged in to cancel a reservation"}

    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        db.close()
        return {"error": "Reservation not found"}

    if reservation.username != username and user.role != "admin":
        db.close()
        return {"error": "You are not authorized to cancel this reservation"}

    if reservation.status != "reserved":
        db.close()
        return {"error": "Only reservations that haven't been issued yet can be cancelled"}

    book = db.query(Book).filter(Book.id == reservation.book_id).first()
    if not book:
        db.close()
        return {"error": "Book not found"}

    reservation.status = "cancelled"
    book.reserved_quantity -= 1
    book.available_quantity += 1

    db.commit()
    title = book.title
    db.close()
    return {"message": f"Reservation for '{title}' has been cancelled."}


@app.post("/reservations/{reservation_id}/issue")
def issue_reservation(reservation_id: int, username: str):
    db = SessionLocal()

    user = db.query(User).filter(User.username == username).first()
    if not user or user.role != "admin":
        db.close()
        return {"error": "Only admins can issue books"}

    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        db.close()
        return {"error": "Reservation not found"}

    if reservation.status != "reserved":
        db.close()
        return {"error": "This reservation is not in a reserved state"}

    book = db.query(Book).filter(Book.id == reservation.book_id).first()
    if not book:
        db.close()
        return {"error": "Book not found"}

    reservation.status = "issued"
    reservation.issued_on = date.today().isoformat()
    book.reserved_quantity -= 1
    book.issued_quantity += 1

    db.commit()
    student = reservation.username
    title = book.title
    db.close()
    return {"message": f"'{title}' has been issued to {student}."}


@app.post("/reservations/{reservation_id}/return")
def return_reservation(reservation_id: int, username: str):
    db = SessionLocal()

    user = db.query(User).filter(User.username == username).first()
    if not user or user.role != "admin":
        db.close()
        return {"error": "Only admins can return books"}

    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        db.close()
        return {"error": "Reservation not found"}

    if reservation.status != "issued":
        db.close()
        return {"error": "This reservation is not currently issued"}

    book = db.query(Book).filter(Book.id == reservation.book_id).first()
    if not book:
        db.close()
        return {"error": "Book not found"}

    reservation.status = "returned"
    book.issued_quantity -= 1
    book.available_quantity += 1

    db.commit()
    student = reservation.username
    title = book.title
    db.close()
    return {"message": f"'{title}' has been returned by {student}."}


@app.post("/register")
def register(new_user: NewUser):
    db = SessionLocal()
    existing = db.query(User).filter(User.username == new_user.username).first()
    if existing:
        db.close()
        return {"error": "Username already taken"}

    hashed_password = pwd_context.hash(new_user.password)
    user = User(username=new_user.username, password=hashed_password, role=new_user.role)
    db.add(user)
    db.commit()
    db.close()
    return {"message": f"User '{new_user.username}' registered successfully as {new_user.role}."}


@app.post("/login")
def login(login_user: LoginUser):
    db = SessionLocal()
    user = db.query(User).filter(User.username == login_user.username).first()

    if not user:
        db.close()
        return {"error": "Invalid username or password"}

    if not pwd_context.verify(login_user.password, user.password):
        db.close()
        return {"error": "Invalid username or password"}

    role = user.role
    db.close()
    return {"message": "Login successful", "role": role}