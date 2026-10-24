from passlib.context import CryptContext
from database import Base, engine, SessionLocal, Book, User, Reservation, Wishlist, BookRequest
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date
from collections import Counter

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

LOAN_PERIOD_DAYS = 7
OVERDUE_FINE = 100
DAMAGE_FINE = 100


class NewBook(BaseModel):
    title: str
    author: str
    genre: str
    publication: str = ""
    quantity: int


class NewUser(BaseModel):
    username: str
    password: str
    role: str
    class_name: str = ""
    roll_no: str = ""
    course: str = ""


class LoginUser(BaseModel):
    username: str
    password: str


class NewWishlistItem(BaseModel):
    book_id: int


class NewBookRequest(BaseModel):
    title: str
    author: str = ""


def days_left(reservation):
    if not reservation.issued_on:
        return None
    issued = date.fromisoformat(reservation.issued_on)
    total_period = LOAN_PERIOD_DAYS + (reservation.extended_days or 0)
    days_passed = (date.today() - issued).days
    return total_period - days_passed


# ---------------------------------------------------------------
# BOOKS
# ---------------------------------------------------------------

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
        publication=new_book.publication,
        available_quantity=new_book.quantity,
        reserved_quantity=0,
        issued_quantity=0
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    db.close()
    return {"message": f"Book '{book.title}' has been added with {book.available_quantity} copies.", "book": book}


# ---------------------------------------------------------------
# RESERVE / ISSUE / RETURN (with fine + damage)
# ---------------------------------------------------------------

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
            issued_on=None,
            returned_on=None,
            extended_days=0,
            fine_amount=0,
            fine_paid=0,
            damaged=0,
            rating=None
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
                "reservation_id": r.id,
                "book_id": book.id,
                "book_title": book.title,
                "author": book.author,
                "status": r.status,
                "reserved_on": r.reserved_on,
                "issued_on": r.issued_on,
                "returned_on": r.returned_on,
                "extended_days": r.extended_days,
                "fine_amount": r.fine_amount,
                "fine_paid": r.fine_paid,
                "damaged": r.damaged,
                "rating": r.rating
            })

    db.close()
    return results


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


@app.post("/reservations/{reservation_id}/renew")
def renew_reservation(reservation_id: int, username: str):
    db = SessionLocal()

    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        db.close()
        return {"error": "Reservation not found"}

    if reservation.username != username:
        db.close()
        return {"error": "You can only renew your own reservation"}

    if reservation.status != "issued":
        db.close()
        return {"error": "Only currently issued books can be renewed"}

    if reservation.extended_days and reservation.extended_days > 0:
        db.close()
        return {"error": "This book has already been renewed once"}

    reservation.extended_days = LOAN_PERIOD_DAYS
    db.commit()
    title_book = db.query(Book).filter(Book.id == reservation.book_id).first()
    title = title_book.title if title_book else "Book"
    db.close()
    return {"message": f"'{title}' has been renewed for {LOAN_PERIOD_DAYS} more days."}


@app.post("/reservations/{reservation_id}/return")
def return_reservation(reservation_id: int, username: str, damaged: bool = False):
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

    left = days_left(reservation)
    fine = 0
    if left is not None and left < 0:
        fine += OVERDUE_FINE
    if damaged:
        fine += DAMAGE_FINE

    # If a fine was already applied manually (via apply-fine) before return,
    # don't double-charge the overdue portion again.
    if reservation.fine_amount and reservation.fine_amount > 0:
        fine = max(fine, reservation.fine_amount) if not damaged else reservation.fine_amount + DAMAGE_FINE

    reservation.status = "returned"
    reservation.returned_on = date.today().isoformat()
    reservation.fine_amount = fine
    reservation.damaged = 1 if damaged else 0

    book.issued_quantity -= 1
    book.available_quantity += 1

    db.commit()
    student = reservation.username
    title = book.title
    db.close()

    if fine > 0:
        return {"message": f"'{title}' returned by {student}. Fine of Rs {fine} applies."}
    return {"message": f"'{title}' has been returned by {student}."}


@app.post("/reservations/{reservation_id}/apply-fine")
def apply_fine(reservation_id: int, username: str):
    db = SessionLocal()

    user = db.query(User).filter(User.username == username).first()
    if not user or user.role != "admin":
        db.close()
        return {"error": "Only admins can apply fines"}

    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        db.close()
        return {"error": "Reservation not found"}

    if reservation.status != "issued":
        db.close()
        return {"error": "Fine can only be applied to a currently issued book"}

    left = days_left(reservation)
    if left is None or left >= 0:
        db.close()
        return {"error": "This book is not overdue yet"}

    if reservation.fine_amount and reservation.fine_amount > 0:
        db.close()
        return {"error": "A fine has already been applied to this reservation"}

    reservation.fine_amount = OVERDUE_FINE
    db.commit()
    student = reservation.username
    db.close()
    return {"message": f"Fine of Rs {OVERDUE_FINE} applied to {student} for the overdue book."}


@app.post("/reservations/{reservation_id}/pay-fine")
def pay_fine(reservation_id: int, username: str):
    db = SessionLocal()

    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        db.close()
        return {"error": "Reservation not found"}

    if reservation.username != username:
        db.close()
        return {"error": "You can only pay your own fine"}

    if reservation.fine_amount <= 0:
        db.close()
        return {"error": "There is no fine to pay for this book"}

    if reservation.fine_paid:
        db.close()
        return {"error": "This fine has already been paid"}

    reservation.fine_paid = 1
    db.commit()
    amount = reservation.fine_amount
    db.close()
    return {"message": f"Payment of Rs {amount} received. Thank you!"}


@app.post("/reservations/{reservation_id}/rate")
def rate_reservation(reservation_id: int, username: str, rating: int):
    db = SessionLocal()

    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        db.close()
        return {"error": "Reservation not found"}

    if reservation.username != username:
        db.close()
        return {"error": "You can only rate your own returned books"}

    if reservation.status != "returned":
        db.close()
        return {"error": "You can only rate a book after returning it"}

    if rating < 1 or rating > 5:
        db.close()
        return {"error": "Rating must be between 1 and 5"}

    reservation.rating = rating
    db.commit()
    db.close()
    return {"message": "Thanks for rating this book!"}


@app.get("/books/{book_id}/rating")
def get_book_rating(book_id: int):
    db = SessionLocal()
    ratings = db.query(Reservation).filter(
        Reservation.book_id == book_id, Reservation.rating.isnot(None)
    ).all()
    db.close()
    if not ratings:
        return {"average": None, "count": 0}
    values = [r.rating for r in ratings]
    return {"average": round(sum(values) / len(values), 1), "count": len(values)}


# ---------------------------------------------------------------
# WISHLIST
# ---------------------------------------------------------------

@app.post("/wishlist")
def add_to_wishlist(item: NewWishlistItem, username: str):
    db = SessionLocal()
    existing = db.query(Wishlist).filter(
        Wishlist.book_id == item.book_id, Wishlist.username == username
    ).first()
    if existing:
        db.close()
        return {"error": "This book is already in your wishlist"}

    wish = Wishlist(book_id=item.book_id, username=username, added_on=date.today().isoformat())
    db.add(wish)
    db.commit()
    db.close()
    return {"message": "Added to your wishlist."}


@app.get("/wishlist/{username}")
def get_wishlist(username: str):
    db = SessionLocal()
    items = db.query(Wishlist).filter(Wishlist.username == username).all()
    results = []
    for w in items:
        book = db.query(Book).filter(Book.id == w.book_id).first()
        if book:
            results.append({
                "wishlist_id": w.id,
                "book_id": book.id,
                "title": book.title,
                "author": book.author,
                "available_quantity": book.available_quantity,
                "added_on": w.added_on
            })
    db.close()
    return results


@app.post("/wishlist/{wishlist_id}/remove")
def remove_from_wishlist(wishlist_id: int, username: str):
    db = SessionLocal()
    item = db.query(Wishlist).filter(Wishlist.id == wishlist_id, Wishlist.username == username).first()
    if not item:
        db.close()
        return {"error": "Wishlist item not found"}
    db.delete(item)
    db.commit()
    db.close()
    return {"message": "Removed from wishlist."}


# ---------------------------------------------------------------
# BOOK REQUESTS
# ---------------------------------------------------------------

@app.post("/book-requests")
def create_book_request(req: NewBookRequest, username: str):
    db = SessionLocal()
    new_req = BookRequest(
        username=username,
        title=req.title,
        author=req.author,
        requested_on=date.today().isoformat(),
        status="pending"
    )
    db.add(new_req)
    db.commit()
    db.close()
    return {"message": "Your book request has been submitted."}


@app.get("/book-requests")
def list_book_requests(username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user or user.role != "admin":
        db.close()
        return {"error": "Only admins can view book requests"}
    requests_list = db.query(BookRequest).filter(BookRequest.status == "pending").all()
    db.close()
    return requests_list


@app.post("/book-requests/{request_id}/fulfill")
def fulfill_book_request(request_id: int, username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user or user.role != "admin":
        db.close()
        return {"error": "Only admins can fulfill requests"}

    req = db.query(BookRequest).filter(BookRequest.id == request_id).first()
    if not req:
        db.close()
        return {"error": "Request not found"}

    req.status = "fulfilled"
    db.commit()
    db.close()
    return {"message": "Request marked as fulfilled."}


# ---------------------------------------------------------------
# ADMIN DASHBOARD — ISSUE / RETURN IN ONE PLACE
# ---------------------------------------------------------------

@app.get("/admin/circulation")
def get_circulation(username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user or user.role != "admin":
        db.close()
        return {"error": "Only admins can view this"}

    # Books waiting to be issued
    to_issue = db.query(Reservation).filter(Reservation.status == "reserved").all()
    to_issue_list = []
    for r in to_issue:
        book = db.query(Book).filter(Book.id == r.book_id).first()
        if book:
            to_issue_list.append({
                "reservation_id": r.id,
                "book_title": book.title,
                "author": book.author,
                "username": r.username,
                "reserved_on": r.reserved_on
            })

    # Books currently issued, waiting to be returned
    to_return = db.query(Reservation).filter(Reservation.status == "issued").all()
    to_return_list = []
    for r in to_return:
        book = db.query(Book).filter(Book.id == r.book_id).first()
        if book:
            left = days_left(r)
            to_return_list.append({
                "reservation_id": r.id,
                "book_title": book.title,
                "author": book.author,
                "username": r.username,
                "issued_on": r.issued_on,
                "days_left": left,
                "fine_already_applied": bool(r.fine_amount and r.fine_amount > 0)
            })

    db.close()
    return {
        "to_issue": to_issue_list,
        "to_return": to_return_list
    }


# ---------------------------------------------------------------
# ADMIN DASHBOARD — CONSOLIDATED PENDING REQUESTS
# ---------------------------------------------------------------

@app.get("/admin/pending-requests")
def get_pending_requests(username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user or user.role != "admin":
        db.close()
        return {"error": "Only admins can view pending requests"}

    # Books reserved by students, waiting to be issued by the admin
    pending_reservations = db.query(Reservation).filter(Reservation.status == "reserved").all()
    reservation_list = []
    for r in pending_reservations:
        book = db.query(Book).filter(Book.id == r.book_id).first()
        if book:
            reservation_list.append({
                "type": "reservation",
                "reservation_id": r.id,
                "book_id": book.id,
                "book_title": book.title,
                "author": book.author,
                "username": r.username,
                "reserved_on": r.reserved_on
            })

    # New-book requests from students, waiting to be fulfilled by the admin
    pending_book_requests = db.query(BookRequest).filter(BookRequest.status == "pending").all()
    request_list = []
    for req in pending_book_requests:
        request_list.append({
            "type": "book_request",
            "request_id": req.id,
            "title": req.title,
            "author": req.author,
            "username": req.username,
            "requested_on": req.requested_on
        })

    db.close()
    return {
        "pending_reservations": reservation_list,
        "pending_book_requests": request_list,
        "total_pending": len(reservation_list) + len(request_list)
    }


# ---------------------------------------------------------------
# PROFILE
# ---------------------------------------------------------------

@app.get("/profile/{username}")
def get_profile(username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user:
        db.close()
        return {"error": "User not found"}

    reservations = db.query(Reservation).filter(Reservation.username == username).all()
    total_read = len([r for r in reservations if r.status == "returned"])
    currently_borrowed = len([r for r in reservations if r.status == "issued"])

    genres = []
    for r in reservations:
        book = db.query(Book).filter(Book.id == r.book_id).first()
        if book:
            genres.append(book.genre)
    favorite_genre = Counter(genres).most_common(1)[0][0] if genres else "N/A"

    db.close()
    return {
        "username": username,
        "class_name": user.class_name,
        "roll_no": user.roll_no,
        "course": user.course,
        "total_read": total_read,
        "currently_borrowed": currently_borrowed,
        "favorite_genre": favorite_genre
    }


# ---------------------------------------------------------------
# ANALYTICS (admin only)
# ---------------------------------------------------------------

@app.get("/analytics/overdue")
def analytics_overdue(username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user or user.role != "admin":
        db.close()
        return {"error": "Only admins can view analytics"}

    issued = db.query(Reservation).filter(Reservation.status == "issued").all()
    results = []
    for r in issued:
        left = days_left(r)
        if left is not None and left < 0:
            book = db.query(Book).filter(Book.id == r.book_id).first()
            results.append({
                "reservation_id": r.id,
                "student": r.username,
                "book_title": book.title if book else "Unknown",
                "overdue_by": abs(left),
                "fine_already_applied": bool(r.fine_amount and r.fine_amount > 0)
            })
    db.close()
    return results


@app.get("/analytics/genre-popularity")
def analytics_genre_popularity(username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user or user.role != "admin":
        db.close()
        return {"error": "Only admins can view analytics"}

    reservations = db.query(Reservation).all()
    genre_counts = Counter()
    for r in reservations:
        book = db.query(Book).filter(Book.id == r.book_id).first()
        if book:
            genre_counts[book.genre] += 1
    db.close()
    return dict(genre_counts)


@app.get("/analytics/top-students")
def analytics_top_students(username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user or user.role != "admin":
        db.close()
        return {"error": "Only admins can view analytics"}

    reservations = db.query(Reservation).all()
    counts = Counter(r.username for r in reservations)
    db.close()
    return [{"student": s, "count": c} for s, c in counts.most_common(5)]


@app.get("/analytics/utilization")
def analytics_utilization(username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user or user.role != "admin":
        db.close()
        return {"error": "Only admins can view analytics"}

    books = db.query(Book).all()
    total = sum(b.available_quantity + b.reserved_quantity + b.issued_quantity for b in books)
    issued = sum(b.issued_quantity for b in books)
    db.close()
    percent = round((issued / total) * 100, 1) if total > 0 else 0
    return {"total_copies": total, "currently_issued": issued, "utilization_percent": percent}


@app.get("/analytics/never-reserved")
def analytics_never_reserved(username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user or user.role != "admin":
        db.close()
        return {"error": "Only admins can view analytics"}

    books = db.query(Book).all()
    reserved_book_ids = set(r.book_id for r in db.query(Reservation).all())
    results = [{"title": b.title, "author": b.author} for b in books if b.id not in reserved_book_ids]
    db.close()
    return results


@app.get("/analytics/monthly-trend")
def analytics_monthly_trend(username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user or user.role != "admin":
        db.close()
        return {"error": "Only admins can view analytics"}

    reservations = db.query(Reservation).all()
    month_counts = Counter(r.reserved_on[:7] for r in reservations if r.reserved_on)
    db.close()
    return dict(sorted(month_counts.items()))


@app.get("/analytics/fine-collection")
def analytics_fine_collection(username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user or user.role != "admin":
        db.close()
        return {"error": "Only admins can view analytics"}

    total_fine = db.query(Reservation).filter(Reservation.fine_amount > 0).all()
    total = sum(r.fine_amount for r in total_fine)
    db.close()
    return {"total_fine_collected": total, "fined_returns_count": len(total_fine)}


@app.get("/analytics/avg-return-time")
def analytics_avg_return_time(username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user or user.role != "admin":
        db.close()
        return {"error": "Only admins can view analytics"}

    returned = db.query(Reservation).filter(
        Reservation.status == "returned", Reservation.issued_on.isnot(None)
    ).all()
    db.close()
    if not returned:
        return {"average_days": None}
    total_days = 0
    for r in returned:
        issued = date.fromisoformat(r.issued_on)
        returned_date = date.fromisoformat(r.returned_on)
        total_days += (returned_date - issued).days
    return {"average_days": round(total_days / len(returned), 1)}


@app.get("/analytics/class-course")
def analytics_class_course(username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user or user.role != "admin":
        db.close()
        return {"error": "Only admins can view analytics"}

    reservations = db.query(Reservation).all()
    class_counts = Counter()
    course_counts = Counter()
    for r in reservations:
        student = db.query(User).filter(User.username == r.username).first()
        if student:
            if student.class_name:
                class_counts[student.class_name] += 1
            if student.course:
                course_counts[student.course] += 1
    db.close()
    return {"by_class": dict(class_counts), "by_course": dict(course_counts)}


# ---------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------

@app.post("/register")
def register(new_user: NewUser):
    db = SessionLocal()
    existing = db.query(User).filter(User.username == new_user.username).first()
    if existing:
        db.close()
        return {"error": "Username already taken"}

    hashed_password = pwd_context.hash(new_user.password)
    user = User(
        username=new_user.username,
        password=hashed_password,
        role=new_user.role,
        class_name=new_user.class_name,
        roll_no=new_user.roll_no,
        course=new_user.course
    )
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