import streamlit as st
import requests
from datetime import date, datetime

st.set_page_config(page_title="Library Reservation System", page_icon="📚", layout="wide")

with open("frontend/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if "username" not in st.session_state:
    st.session_state.username = None
    st.session_state.role = None

BASE_URL = "https://library-reservation-system-2vxi.onrender.com"

BADGE_STYLE = (
    "display:inline-block; padding:4px 14px; border-radius:14px; "
    "font-size:12px; font-weight:700; letter-spacing:0.3px; "
    "box-shadow:0 2px 6px rgba(0,0,0,0.15); margin:2px 4px 2px 0;"
)


def badge(text, color):
    return f"<span style='background-color:{color}; color:white; {BADGE_STYLE}'>{text}</span>"


# ============================================================
# FULL-PAGE LOGIN / REGISTER SCREEN
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
                        f"{BASE_URL}/login",
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
                    reg_username = st.text_input("Choose a Username (College ID)")
                    reg_password = st.text_input("Choose a Password (Same College ID)", type="password")
                    reg_class = st.selectbox("Class", ["FY", "SY", "TY", "11th", "12th"])
                    reg_roll = st.text_input("Roll No")
                    reg_course = st.selectbox(
                        "Course", [
                            "BSc CS", "BSc IT", "BSc Data Science", "BSc Biotechnology",
                            "BSc Chemistry", "BSc Physics", "BSc Mathematics", "BSc Statistics","BCA", "BBA", "B.Com", "B.Com (Accounting & Finance)",
                            "BA", "BA (Economics)", "BA (Psychology)", "BA (English)","BMS", "BMM", "B.Ed", "LLB" , "Science", "Commerce", "Arts"
                            ]
                    )
                    reg_submitted = st.form_submit_button("Register", use_container_width=True)

                    if reg_submitted:
                        if not reg_username.isdigit() or not reg_password.isdigit():
                            st.error("Username and Password must be numbers only (your college ID).")
                        elif reg_username != reg_password:
                            st.error("Username and Password must be the same college ID number.")
                        elif not reg_roll.strip():
                            st.error("Please enter your Roll No.")
                        else:
                            res = requests.post(
                                f"{BASE_URL}/register",
                                json={
                                    "username": reg_username,
                                    "password": reg_password,
                                    "role": "student",
                                    "class_name": reg_class,
                                    "roll_no": reg_roll,
                                    "course": reg_course
                                }
                            )
                            data = res.json()
                            if "message" in data and "error" not in data:
                                st.success(data["message"] + " You can now log in.")
                            else:
                                st.error(data.get("error", "Registration failed"))

    st.stop()


# ============================================================
# MAIN APP
# ============================================================
st.title("📚 Library Book Reservation System")

# ---- Due-soon / overdue notification banner (students only) ----
if st.session_state.role == "student":
    res = requests.get(f"{BASE_URL}/my-reservations/{st.session_state.username}")
    my_active = res.json()
    for r in my_active:
        if r["status"] == "issued":
            issued_on = datetime.fromisoformat(r["issued_on"]).date()
            total_period = 7 + (r["extended_days"] or 0)
            left = total_period - (date.today() - issued_on).days
            if 0 < left <= 2:
                st.warning(f"⏰ Reminder: '{r['book_title']}' is due in {left} day{'s' if left != 1 else ''}. Please return it soon!")
            elif left <= 0:
                st.error(f"⚠️ '{r['book_title']}' is overdue by {abs(left)} day{'s' if abs(left) != 1 else ''}! A fine may apply.")
        if r["status"] == "returned" and r["fine_amount"] > 0 and not r["fine_paid"]:
            st.error(f"💳 You have an unpaid fine of Rs {r['fine_amount']} for '{r['book_title']}'. Pay it from Reading History in the sidebar.")

# ---- View switcher for admin (Books vs Analytics) ----
view = "Books"
if st.session_state.role == "admin":
    view = st.radio("View", ["Books", "Analytics"], horizontal=True)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.write(f"Logged in as **{st.session_state.username}** ({st.session_state.role})")
    if st.button("Logout"):
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()

    if st.session_state.role == "student":
        st.divider()
        st.subheader("My Profile")
        res = requests.get(f"{BASE_URL}/profile/{st.session_state.username}")
        profile = res.json()
        if "username" in profile:
            st.write(f"Class: **{profile['class_name']}** | Roll No: **{profile['roll_no']}**")
            st.write(f"Course: **{profile['course']}**")
            st.write(f"📖 Books read: **{profile['total_read']}**")
            st.write(f"📕 Currently borrowed: **{profile['currently_borrowed']}**")
            st.write(f"⭐ Favorite genre: **{profile['favorite_genre']}**")

        st.divider()
        st.subheader("My Reservations")
        res = requests.get(f"{BASE_URL}/my-reservations/{st.session_state.username}")
        my_reservations = res.json()

        active = [r for r in my_reservations if r["status"] in ("reserved", "issued")]
        history = [r for r in my_reservations if r["status"] == "returned"]

        if active:
            for r in active:
                st.write(f"📘 **{r['book_title']}**")
                if r["status"] == "reserved":
                    st.caption(f"Reserved on {r['reserved_on']} — waiting to be issued")
                elif r["status"] == "issued":
                    issued_on = datetime.fromisoformat(r["issued_on"]).date()
                    total_period = 7 + (r["extended_days"] or 0)
                    left = total_period - (date.today() - issued_on).days
                    if left > 0:
                        st.caption(f"Issued on {r['issued_on']} — due in {left} day{'s' if left != 1 else ''}")
                    else:
                        st.caption(f"Overdue by {abs(left)} day{'s' if abs(left) != 1 else ''}")
                    if not r["extended_days"]:
                        if st.button("Renew (+7 days)", key=f"renew_{r['reservation_id']}"):
                            rres = requests.post(
                                f"{BASE_URL}/reservations/{r['reservation_id']}/renew?username={st.session_state.username}"
                            )
                            rdata = rres.json()
                            if "message" in rdata:
                                st.toast(rdata["message"], icon="🔄")
                            else:
                                st.error(rdata.get("error"))
                            st.rerun()
        else:
            st.caption("No active reservations.")

        with st.expander("📜 Reading History"):
            if history:
                for r in history:
                    st.write(f"**{r['book_title']}** — returned {r['returned_on']}")
                    if r["fine_amount"] > 0:
                        if r["fine_paid"]:
                            st.caption(f"✅ Fine of Rs {r['fine_amount']} — Paid")
                        else:
                            st.caption(f"⚠️ Fine of Rs {r['fine_amount']} — Unpaid")
                            with st.expander(f"💳 Pay Rs {r['fine_amount']}"):
                                pay_method = st.radio(
                                    "Choose payment method",
                                    ["UPI", "Card", "Cash at Counter"],
                                    key=f"paymethod_{r['reservation_id']}",
                                    horizontal=True
                                )
                                if pay_method == "UPI":
                                    st.text_input("Enter UPI ID", placeholder="yourname@upi",
                                                  key=f"upi_{r['reservation_id']}")
                                elif pay_method == "Card":
                                    c1, c2 = st.columns(2)
                                    with c1:
                                        st.text_input("Card Number", placeholder="XXXX XXXX XXXX XXXX",
                                                      key=f"card_{r['reservation_id']}")
                                    with c2:
                                        st.text_input("CVV", placeholder="XXX", type="password",
                                                      key=f"cvv_{r['reservation_id']}")

                                if st.button(f"Confirm Payment — Rs {r['fine_amount']}",
                                             key=f"pay_{r['reservation_id']}"):
                                    if pay_method == "Cash at Counter":
                                        st.info("Please pay Rs " + str(r['fine_amount']) + " at the library counter. Ask the admin to mark it as paid.")
                                    else:
                                        with st.spinner(f"Processing payment via {pay_method}..."):
                                            import time
                                            time.sleep(1.2)
                                            pres = requests.post(
                                                f"{BASE_URL}/reservations/{r['reservation_id']}/pay-fine"
                                                f"?username={st.session_state.username}"
                                            )
                                            pdata = pres.json()
                                        if "message" in pdata:
                                            st.success(f"✅ Payment Successful via {pay_method}!")
                                            st.toast(pdata["message"], icon="💳")
                                        else:
                                            st.error(pdata.get("error"))
                                        st.rerun()
                    if r["rating"]:
                        st.caption(f"Your rating: {'⭐' * r['rating']}")
                    else:
                        rate_val = st.selectbox(
                            "Rate this book", [None, 1, 2, 3, 4, 5],
                            key=f"rate_{r['reservation_id']}"
                        )
                        if rate_val and st.button("Submit Rating", key=f"submit_rate_{r['reservation_id']}"):
                            rres = requests.post(
                                f"{BASE_URL}/reservations/{r['reservation_id']}/rate"
                                f"?username={st.session_state.username}&rating={rate_val}"
                            )
                            st.toast(rres.json().get("message", ""), icon="⭐")
                            st.rerun()
            else:
                st.caption("No books returned yet.")

        with st.expander("💛 My Wishlist"):
            res = requests.get(f"{BASE_URL}/wishlist/{st.session_state.username}")
            wishlist_items = res.json()
            if wishlist_items:
                for w in wishlist_items:
                    st.write(f"**{w['title']}** — {w['author']}")
                    st.caption(f"Available copies: {w['available_quantity']}")
                    if st.button("Remove", key=f"unwish_{w['wishlist_id']}"):
                        requests.post(
                            f"{BASE_URL}/wishlist/{w['wishlist_id']}/remove?username={st.session_state.username}"
                        )
                        st.rerun()
            else:
                st.caption("Your wishlist is empty.")

        with st.expander("📩 Request a New Book"):
            with st.form("book_request_form", clear_on_submit=True):
                req_title = st.text_input("Book Title")
                req_author = st.text_input("Author (optional)")
                if st.form_submit_button("Submit Request"):
                    requests.post(
                        f"{BASE_URL}/book-requests?username={st.session_state.username}",
                        json={"title": req_title, "author": req_author}
                    )
                    st.success("Request submitted!")

    if st.session_state.role == "admin":
        st.divider()
        st.subheader("Add a New Book")
        with st.form("add_book_form", clear_on_submit=True):
            new_title = st.text_input("Title")
            new_author = st.text_input("Author")
            new_genre = st.text_input("Genre")
            new_publication = st.text_input("Publication")
            new_quantity = st.number_input("Quantity", min_value=1, step=1, value=1)
            submitted = st.form_submit_button("Add Book")

            if submitted:
                res = requests.post(
                    f"{BASE_URL}/books?username={st.session_state.username}",
                    json={
                        "title": new_title,
                        "author": new_author,
                        "genre": new_genre,
                        "publication": new_publication,
                        "quantity": int(new_quantity)
                    }
                )
                data = res.json()
                if "book" in data:
                    st.success(data["message"])
                else:
                    st.error(data.get("error", "Failed to add book"))

        with st.expander("📩 Pending Book Requests"):
            res = requests.get(f"{BASE_URL}/book-requests?username={st.session_state.username}")
            pending = res.json()
            if isinstance(pending, list) and pending:
                for p in pending:
                    st.write(f"**{p['title']}** — requested by {p['username']}")
                    if st.button("Mark Fulfilled", key=f"fulfill_{p['id']}"):
                        requests.post(
                            f"{BASE_URL}/book-requests/{p['id']}/fulfill?username={st.session_state.username}"
                        )
                        st.rerun()
            else:
                st.caption("No pending requests.")

        with st.expander("📚 Issue / Return", expanded=True):
            circ = requests.get(
                f"{BASE_URL}/admin/circulation?username={st.session_state.username}"
            ).json()

            st.markdown("**🟡 To Issue**")
            to_issue = circ.get("to_issue", [])
            if to_issue:
                for item in to_issue:
                    st.write(f"📘 **{item['book_title']}** — {item['username']}")
                    st.caption(f"Reserved on {item['reserved_on']}")
                    if st.button("Issue", key=f"circ_issue_{item['reservation_id']}"):
                        ires = requests.post(
                            f"{BASE_URL}/reservations/{item['reservation_id']}/issue"
                            f"?username={st.session_state.username}"
                        )
                        idata = ires.json()
                        if "message" in idata:
                            st.toast(idata["message"], icon="📗")
                        else:
                            st.error(idata.get("error"))
                        st.rerun()
                    st.write("---")
            else:
                st.caption("Nothing waiting to be issued.")

            st.markdown("**🔴 To Return**")
            to_return = circ.get("to_return", [])
            if to_return:
                for item in to_return:
                    left = item["days_left"]
                    status_text = f"Due in {left} day{'s' if left != 1 else ''}" if left is not None and left > 0 \
                        else f"Overdue by {abs(left)} day{'s' if left is not None and abs(left) != 1 else ''}"
                    st.write(f"📕 **{item['book_title']}** — {item['username']}")
                    st.caption(f"Issued on {item['issued_on']} — {status_text}")

                    damaged_flag = st.checkbox("Damaged?", key=f"circ_damaged_{item['reservation_id']}")
                    if st.button("Return", key=f"circ_return_{item['reservation_id']}"):
                        rres = requests.post(
                            f"{BASE_URL}/reservations/{item['reservation_id']}/return"
                            f"?username={st.session_state.username}&damaged={str(damaged_flag).lower()}"
                        )
                        rdata = rres.json()
                        if "message" in rdata:
                            st.toast(rdata["message"], icon="📥")
                        else:
                            st.error(rdata.get("error"))
                        st.rerun()

                    if left is not None and left < 0:
                        if item.get("fine_already_applied"):
                            st.caption("✅ Fine already applied")
                        else:
                            if st.button("Apply Fine", key=f"circ_fine_{item['reservation_id']}"):
                                fres = requests.post(
                                    f"{BASE_URL}/reservations/{item['reservation_id']}/apply-fine"
                                    f"?username={st.session_state.username}"
                                )
                                fdata = fres.json()
                                if "message" in fdata:
                                    st.toast(fdata["message"], icon="💰")
                                else:
                                    st.error(fdata.get("error"))
                                st.rerun()
                    st.write("---")
            else:
                st.caption("Nothing waiting to be returned.")

        with st.expander("💰 Overdue & Fines"):
            overdue_sidebar = requests.get(
                f"{BASE_URL}/analytics/overdue?username={st.session_state.username}"
            ).json()
            if overdue_sidebar:
                for o in overdue_sidebar:
                    st.write(f"👤 **{o['student']}** — *{o['book_title']}*")
                    st.caption(f"{o['overdue_by']} day{'s' if o['overdue_by'] != 1 else ''} overdue")
                    if o.get("fine_already_applied"):
                        st.caption("✅ Fine already applied")
                    else:
                        if st.button("Apply Fine", key=f"sidebar_fine_{o['reservation_id']}"):
                            fres = requests.post(
                                f"{BASE_URL}/reservations/{o['reservation_id']}/apply-fine"
                                f"?username={st.session_state.username}"
                            )
                            fdata = fres.json()
                            if "message" in fdata:
                                st.toast(fdata["message"], icon="💰")
                            else:
                                st.error(fdata.get("error"))
                            st.rerun()
                    st.write("---")
            else:
                st.caption("No overdue books right now.")

# ============================================================
# ADMIN ANALYTICS VIEW
# ============================================================
if view == "Analytics":
    st.header("📊 Library Analytics")
    u = st.session_state.username

    col1, col2, col3 = st.columns(3)
    util = requests.get(f"{BASE_URL}/analytics/utilization?username={u}").json()
    fine = requests.get(f"{BASE_URL}/analytics/fine-collection?username={u}").json()
    avg_return = requests.get(f"{BASE_URL}/analytics/avg-return-time?username={u}").json()

    with col1:
        st.metric("Utilization", f"{util.get('utilization_percent', 0)}%",
                   help="Percentage of total copies currently issued")
    with col2:
        st.metric("Fine Collected", f"Rs {fine.get('total_fine_collected', 0)}")
    with col3:
        avg_days = avg_return.get("average_days")
        st.metric("Avg Return Time", f"{avg_days} days" if avg_days is not None else "N/A")

    st.subheader("Genre Popularity")
    genre_data = requests.get(f"{BASE_URL}/analytics/genre-popularity?username={u}").json()
    if genre_data:
        st.bar_chart(genre_data)
    else:
        st.caption("No reservation data yet.")

    st.subheader("Monthly Reservation Trend")
    monthly_data = requests.get(f"{BASE_URL}/analytics/monthly-trend?username={u}").json()
    if monthly_data:
        st.line_chart(monthly_data)
    else:
        st.caption("No reservation data yet.")

    col4, col5 = st.columns(2)
    with col4:
        st.subheader("Top 5 Students")
        top_students = requests.get(f"{BASE_URL}/analytics/top-students?username={u}").json()
        if top_students:
            for s in top_students:
                st.write(f"👤 **{s['student']}** — {s['count']} reservations")
        else:
            st.caption("No data yet.")

    with col5:
        st.subheader("Class / Course Breakdown")
        cc = requests.get(f"{BASE_URL}/analytics/class-course?username={u}").json()
        if cc.get("by_class"):
            st.write("**By Class:**")
            st.bar_chart(cc["by_class"])
        if cc.get("by_course"):
            st.write("**By Course:**")
            st.bar_chart(cc["by_course"])

    st.subheader("⚠️ Overdue Books & Fines")
    overdue = requests.get(f"{BASE_URL}/analytics/overdue?username={u}").json()
    if overdue:
        for o in overdue:
            ocol1, ocol2 = st.columns([4, 1])
            with ocol1:
                overdue_label = f"{o['overdue_by']} days overdue"
                st.markdown(
                    f"👤 **{o['student']}** — *{o['book_title']}* " + badge(overdue_label, "#8b0000"),
                    unsafe_allow_html=True
                )
            with ocol2:
                if o.get("fine_already_applied"):
                    st.caption("✅ Fine applied")
                else:
                    if st.button("Apply Fine", key=f"applyfine_{o['reservation_id']}"):
                        fres = requests.post(
                            f"{BASE_URL}/reservations/{o['reservation_id']}/apply-fine"
                            f"?username={u}"
                        )
                        fdata = fres.json()
                        if "message" in fdata:
                            st.toast(fdata["message"], icon="💰")
                        else:
                            st.error(fdata.get("error"))
                        st.rerun()
    else:
        st.caption("No overdue books right now.")

    st.subheader("📦 Never-Reserved Books")
    never = requests.get(f"{BASE_URL}/analytics/never-reserved?username={u}").json()
    if never:
        for n in never:
            st.write(f"- {n['title']} ({n['author']})")
    else:
        st.caption("Every book has been reserved at least once.")

# ============================================================
# BOOKS VIEW (default)
# ============================================================
else:
    response = requests.get(f"{BASE_URL}/books")
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
                pub_text = f" — {book['publication']}" if book.get("publication") else ""
                st.caption(f"{book['author']} — {book['genre']}{pub_text}")
                rating_data = requests.get(f"{BASE_URL}/books/{book['id']}/rating").json()
                if rating_data.get("average"):
                    st.caption(f"⭐ {rating_data['average']} ({rating_data['count']} ratings)")
            with col2:
                if st.session_state.role == "admin":
                    st.write(f"Available: **{book['available_quantity']}**")
                    st.write(f"Reserved: **{book['reserved_quantity']}**")
                    st.write(f"Issued: **{book['issued_quantity']}**")
                else:
                    st.markdown(
                        badge(f"{book['available_quantity']} of {total_quantity} available", "#28a745"),
                        unsafe_allow_html=True
                    )
            with col3:
                if book["available_quantity"] > 0:
                    if st.button("Reserve", key=f"reserve_{book['id']}"):
                        res = requests.post(
                            f"{BASE_URL}/books/{book['id']}/reserve?username={st.session_state.username}"
                        )
                        data = res.json()
                        if "message" in data:
                            st.toast(data["message"], icon="✅")
                        st.rerun()
                elif st.session_state.role == "student":
                    if st.button("Add to Wishlist", key=f"wish_{book['id']}"):
                        res = requests.post(
                            f"{BASE_URL}/wishlist?username={st.session_state.username}",
                            json={"book_id": book["id"]}
                        )
                        data = res.json()
                        st.toast(data.get("message", data.get("error", "")), icon="💛")
                        st.rerun()

            if st.session_state.role == "admin" and (book["reserved_quantity"] > 0 or book["issued_quantity"] > 0):
                st.divider()
                res = requests.get(f"{BASE_URL}/books/{book['id']}/reservations")
                book_reservations = res.json()

                for r in book_reservations:
                    rcol1, rcol2, rcol3 = st.columns([3, 1, 1])
                    with rcol1:
                        if r["status"] == "reserved":
                            st.write(f"👤 **{r['username']}** — reserved on {r['reserved_on']}")
                        elif r["status"] == "issued":
                            issued_on = datetime.fromisoformat(r["issued_on"]).date()
                            total_period = 7 + (r["extended_days"] or 0)
                            left = total_period - (date.today() - issued_on).days
                            if left > 0:
                                color = "#28a745" if left > 2 else "#e67e22"
                                label = f"Due in {left} day{'s' if left != 1 else ''}"
                            else:
                                color = "#8b0000"
                                label = f"Overdue by {abs(left)} day{'s' if abs(left) != 1 else ''}"
                            st.markdown(
                                f"👤 **{r['username']}** — issued on {r['issued_on']} " + badge(label, color),
                                unsafe_allow_html=True
                            )
                    with rcol2:
                        if r["status"] == "reserved":
                            if st.button("Issue", key=f"issue_{r['id']}"):
                                res = requests.post(
                                    f"{BASE_URL}/reservations/{r['id']}/issue?username={st.session_state.username}"
                                )
                                data = res.json()
                                if "message" in data:
                                    st.toast(data["message"], icon="📗")
                                st.rerun()
                        elif r["status"] == "issued":
                            damaged_flag = st.checkbox("Damaged?", key=f"damaged_{r['id']}")
                            if st.button("Return", key=f"return_{r['id']}"):
                                res = requests.post(
                                    f"{BASE_URL}/reservations/{r['id']}/return"
                                    f"?username={st.session_state.username}&damaged={str(damaged_flag).lower()}"
                                )
                                data = res.json()
                                if "message" in data:
                                    st.toast(data["message"], icon="📥")
                                st.rerun()
                    with rcol3:
                        if r["status"] == "issued":
                            issued_on = datetime.fromisoformat(r["issued_on"]).date()
                            total_period = 7 + (r["extended_days"] or 0)
                            left = total_period - (date.today() - issued_on).days
                            if left < 0 and not r.get("fine_amount"):
                                if st.button("Apply Fine", key=f"fine_{r['id']}"):
                                    fres = requests.post(
                                        f"{BASE_URL}/reservations/{r['id']}/apply-fine"
                                        f"?username={st.session_state.username}"
                                    )
                                    fdata = fres.json()
                                    if "message" in fdata:
                                        st.toast(fdata["message"], icon="💰")
                                    else:
                                        st.error(fdata.get("error"))
                                    st.rerun()
                            elif r.get("fine_amount"):
                                st.caption("✅ Fined")