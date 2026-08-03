import streamlit as st
import requests
from datetime import date, datetime

st.set_page_config(page_title="Library Reservation System", page_icon="📚", layout="wide")

with open("frontend/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if "username" not in st.session_state:
    st.session_state.username = None
    st.session_state.role = None

LOAN_PERIOD_DAYS = 7

BADGE_STYLE = (
    "display:inline-block; padding:4px 14px; border-radius:14px; "
    "font-size:12px; font-weight:700; letter-spacing:0.3px; "
    "box-shadow:0 2px 6px rgba(0,0,0,0.15); margin:2px 4px 2px 0;"
)


def days_left_for(issued_on_str):
    issued_on = datetime.fromisoformat(issued_on_str).date()
    days_passed = (date.today() - issued_on).days
    return LOAN_PERIOD_DAYS - days_passed


# ============================================================
# FULL-PAGE LOGIN / REGISTER SCREEN
# Shown only when nobody is logged in. Nothing else renders.
# ============================================================
if not st.session_state.username:
    st.title("📚 Library Book Reservation System")
    st.markdown(
        "<p class='hero-subtitle'>Discover, reserve, and manage books — "
        "<span class='accent'>all in one place.</span></p>",
        unsafe_allow_html=True
    )
    st.write("")

    left, center, right = st.columns([1, 1.2, 1])
    with center:
        with st.container(border=True):
            auth_mode = st.radio(
                "Account", ["Login", "Register"], horizontal=True, label_visibility="collapsed"
            )
            st.write("")

            if auth_mode == "Login":
                st.subheader("Login to your account")
                login_username = st.text_input("Username", key="login_username")
                login_password = st.text_input("Password", type="password", key="login_password")
                if st.button("Login", use_container_width=True):
                    res = requests.post(
                        "http://127.0.0.1:8000/login",
                        json={"username": login_username, "password": login_password}
                    )
                    data = res.json()
                    if "role" in data:
                        st.session_state.username = login_username
                        st.session_state.role = data["role"]
                        st.rerun()
                    else:
                        st.error(data.get("error", "Login failed"))
            else:
                st.subheader("Create a new account")
                st.caption(
                    "⚠️ Use your **college ID number** as both your Username and Password "
                    "(e.g. 38731). Numbers only, no letters."
                )
                with st.form("register_form", clear_on_submit=True):
                    reg_username = st.text_input("Choose a Username")
                    reg_password = st.text_input("Choose a Password", type="password")
                    reg_submitted = st.form_submit_button("Register", use_container_width=True)

                    if reg_submitted:
                        if not reg_username.isdigit() or not reg_password.isdigit():
                            st.error("Username and Password must be numbers only (your college ID).")
                        elif reg_username != reg_password:
                            st.error("Username and Password must be the same college ID number.")
                        else:
                            res = requests.post(
                                "http://127.0.0.1:8000/register",
                                json={"username": reg_username, "password": reg_password, "role": "student"}
                            )
                            data = res.json()
                            if "message" in data and "error" not in data:
                                st.success(data["message"] + " You can now log in.")
                            else:
                                st.error(data.get("error", "Registration failed"))

    st.stop()  # stops the script here — nothing below this line runs while logged out


# ============================================================
# MAIN APP — only reached once a user is logged in
# ============================================================
st.title("📚 Library Book Reservation System")

with st.sidebar:
    st.write(f"Logged in as **{st.session_state.username}** ({st.session_state.role})")
    if st.button("Logout"):
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()

    st.divider()
    st.subheader("My Reservations")
    res = requests.get(f"http://127.0.0.1:8000/my-reservations/{st.session_state.username}")
    my_reservations = res.json()

    if my_reservations:
        for r in my_reservations:
            st.write(f"📘 **{r['book_title']}**")
            if r["status"] == "reserved":
                st.caption(f"Reserved on {r['reserved_on']} — waiting to be issued")
            elif r["status"] == "issued":
                left_days = days_left_for(r["issued_on"])
                if left_days > 0:
                    st.caption(f"Issued on {r['issued_on']} — due in {left_days} day{'s' if left_days != 1 else ''}")
                else:
                    st.caption(f"Issued on {r['issued_on']} — overdue by {abs(left_days)} day{'s' if abs(left_days) != 1 else ''}")
            else:
                st.caption("Returned")
    else:
        st.caption("You haven't reserved any books yet.")

    if st.session_state.role == "admin":
        st.divider()
        st.subheader("Add a New Book")
        with st.form("add_book_form", clear_on_submit=True):
            new_title = st.text_input("Title")
            new_author = st.text_input("Author")
            new_genre = st.text_input("Genre")
            new_quantity = st.number_input("Quantity", min_value=1, step=1, value=1)
            submitted = st.form_submit_button("Add Book")

            if submitted:
                res = requests.post(
                    f"http://127.0.0.1:8000/books?username={st.session_state.username}",
                    json={
                        "title": new_title,
                        "author": new_author,
                        "genre": new_genre,
                        "quantity": int(new_quantity)
                    }
                )
                data = res.json()
                if "book" in data:
                    st.success(data["message"])
                else:
                    st.error(data.get("error", "Failed to add book"))

response = requests.get("http://127.0.0.1:8000/books")
books = response.json()

search_col, genre_col = st.columns([2, 1])

with search_col:
    search_term = st.text_input("Search by title or author")

if search_term:
    filtered = []
    for book in books:
        if search_term.lower() in book["title"].lower() or search_term.lower() in book["author"].lower():
            filtered.append(book)
    books = filtered

with genre_col:
    genres = sorted(set(book["genre"] for book in books))
    selected_genre = st.selectbox("Filter by genre", ["All"] + genres)

if selected_genre != "All":
    books = [book for book in books if book["genre"] == selected_genre]

st.write("")

if not books:
    st.info("No books found matching your search.")

for book in books:
    total_quantity = book["available_quantity"] + book["reserved_quantity"] + book["issued_quantity"]

    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.markdown(f"### {book['title']}")
            st.caption(f"{book['author']} — {book['genre']}")
        with col2:
            if st.session_state.role == "admin":
                st.write(f"Available: **{book['available_quantity']}**")
                st.write(f"Reserved: **{book['reserved_quantity']}**")
                st.write(f"Issued: **{book['issued_quantity']}**")
            else:
                st.markdown(
                    f"<span style='background-color:#28a745; color:white; {BADGE_STYLE}'>"
                    f"{book['available_quantity']} of {total_quantity} available</span>",
                    unsafe_allow_html=True
                )
        with col3:
            if book["available_quantity"] > 0:
                if st.button("Reserve", key=f"reserve_{book['id']}"):
                    res = requests.post(
                        f"http://127.0.0.1:8000/books/{book['id']}/reserve?username={st.session_state.username}"
                    )
                    data = res.json()
                    if "message" in data:
                        st.toast(data["message"], icon="✅")
                    st.rerun()

        if st.session_state.role == "admin" and (book["reserved_quantity"] > 0 or book["issued_quantity"] > 0):
            st.divider()
            res = requests.get(f"http://127.0.0.1:8000/books/{book['id']}/reservations")
            book_reservations = res.json()

            for r in book_reservations:
                rcol1, rcol2 = st.columns([3, 1])
                with rcol1:
                    if r["status"] == "reserved":
                        st.write(f"👤 **{r['username']}** — reserved on {r['reserved_on']}")
                    elif r["status"] == "issued":
                        left_days = days_left_for(r["issued_on"])
                        if left_days > 0:
                            badge_color = "#28a745" if left_days > 2 else "#e67e22"
                            label = f"Due in {left_days} day{'s' if left_days != 1 else ''}"
                        else:
                            badge_color = "#8b0000"
                            label = f"Overdue by {abs(left_days)} day{'s' if abs(left_days) != 1 else ''}"
                        st.markdown(
                            f"👤 **{r['username']}** — issued on {r['issued_on']} "
                            f"<span style='background-color:{badge_color}; color:white; {BADGE_STYLE}'>{label}</span>",
                            unsafe_allow_html=True
                        )
                with rcol2:
                    if r["status"] == "reserved":
                        if st.button("Issue", key=f"issue_{r['id']}"):
                            res = requests.post(
                                f"http://127.0.0.1:8000/reservations/{r['id']}/issue?username={st.session_state.username}"
                            )
                            data = res.json()
                            if "message" in data:
                                st.toast(data["message"], icon="📗")
                            st.rerun()
                    elif r["status"] == "issued":
                        if st.button("Return", key=f"return_{r['id']}"):
                            res = requests.post(
                                f"http://127.0.0.1:8000/reservations/{r['id']}/return?username={st.session_state.username}"
                            )
                            data = res.json()
                            if "message" in data:
                                st.toast(data["message"], icon="📥")
                            st.rerun()