"""
Run this once to fill the library with 100 sample books.
From the project root, run:  python backend/seed_books.py
"""

from database import SessionLocal, Book

# (title, author, genre)
base_books = [
    ("Python Basic", "John Smith", "Programming"),
    ("Web Development 101", "Jane Doe", "Programming"),
    ("Data Structures", "Alan Turing", "Computer Science"),
    ("Clean Code", "Robert Martin", "Programming"),
    ("The Pragmatic Programmer", "Andrew Hunt", "Programming"),
    ("Eloquent JavaScript", "Marijn Haverbeke", "Programming"),
    ("Cracking the Coding Interview", "Gayle Laakmann McDowell", "Programming"),
    ("Design Patterns", "Erich Gamma", "Programming"),
    ("Refactoring", "Martin Fowler", "Programming"),
    ("The Mythical Man-Month", "Frederick Brooks", "Programming"),
    ("Introduction to Algorithms", "Thomas Cormen", "Computer Science"),
    ("Artificial Intelligence: A Modern Approach", "Stuart Russell", "Computer Science"),
    ("Compilers: Principles, Techniques, and Tools", "Alfred Aho", "Computer Science"),
    ("Introduction to Machine Learning", "Ethem Alpaydin", "Computer Science"),
    ("Computer Organization and Design", "David Patterson", "Computer Science"),
    ("Operating System Concepts", "Abraham Silberschatz", "Computer Science"),
    ("Computer Networks", "Andrew Tanenbaum", "Computer Science"),
    ("Database System Concepts", "Henry Korth", "Computer Science"),
    ("Head First Design Patterns", "Eric Freeman", "Programming"),
    ("You Don't Know JS", "Kyle Simpson", "Programming"),
    ("The Alchemist", "Paulo Coelho", "Fiction"),
    ("To Kill a Mockingbird", "Harper Lee", "Fiction"),
    ("1984", "George Orwell", "Fiction"),
    ("Animal Farm", "George Orwell", "Fiction"),
    ("The Kite Runner", "Khaled Hosseini", "Fiction"),
    ("Harry Potter and the Sorcerer's Stone", "J.K. Rowling", "Fiction"),
    ("The Great Gatsby", "F. Scott Fitzgerald", "Fiction"),
    ("The Catcher in the Rye", "J.D. Salinger", "Fiction"),
    ("Life of Pi", "Yann Martel", "Fiction"),
    ("Atomic Habits", "James Clear", "Self-help"),
    ("Deep Work", "Cal Newport", "Self-help"),
    ("Think and Grow Rich", "Napoleon Hill", "Self-help"),
    ("The 7 Habits of Highly Effective People", "Stephen Covey", "Self-help"),
    ("Rich Dad Poor Dad", "Robert Kiyosaki", "Self-help"),
    ("The Lean Startup", "Eric Ries", "Business"),
    ("Zero to One", "Peter Thiel", "Business"),
    ("Good to Great", "Jim Collins", "Business"),
    ("The Innovator's Dilemma", "Clayton Christensen", "Business"),
    ("Sapiens", "Yuval Noah Harari", "History"),
    ("A Brief History of Time", "Stephen Hawking", "Science"),
    ("The Selfish Gene", "Richard Dawkins", "Science"),
    ("Cosmos", "Carl Sagan", "Science"),
    ("Thinking, Fast and Slow", "Daniel Kahneman", "Psychology"),
    ("Man's Search for Meaning", "Viktor Frankl", "Psychology"),
    ("Wuthering Heights", "Emily Bronte", "Fiction"),
    ("Pride and Prejudice", "Jane Austen", "Fiction"),
    ("The Hobbit", "J.R.R. Tolkien", "Fiction"),
    ("Fahrenheit 451", "Ray Bradbury", "Fiction"),
    ("Brave New World", "Aldous Huxley", "Fiction"),
    ("The Da Vinci Code", "Dan Brown", "Fiction"),
]

publications = [
    "O'Reilly Media", "Pearson", "Wiley", "Penguin Books",
    "HarperCollins", "Oxford University Press", "McGraw Hill",
    "Cambridge University Press", "Random House", "Springer"
]

books_to_add = []

# Add every base book once, cycling through publications
for i, (title, author, genre) in enumerate(base_books):
    books_to_add.append({
        "title": title,
        "author": author,
        "genre": genre,
        "publication": publications[i % len(publications)],
        "quantity": 3 + (i % 4)
    })

# Duplicate the first 25 titles with a DIFFERENT publication,
# so some titles genuinely appear twice with different editions.
for i, (title, author, genre) in enumerate(base_books[:25]):
    alt_publication = publications[(i + 3) % len(publications)]
    if alt_publication != publications[i % len(publications)]:
        books_to_add.append({
            "title": title,
            "author": author,
            "genre": genre,
            "publication": alt_publication,
            "quantity": 2 + (i % 3)
        })

# Repeat a few more with slight variation to comfortably reach ~100 rows
extra_round = base_books[:25]
for i, (title, author, genre) in enumerate(extra_round):
    third_publication = publications[(i + 6) % len(publications)]
    books_to_add.append({
        "title": title,
        "author": author,
        "genre": genre,
        "publication": third_publication,
        "quantity": 2 + (i % 5)
    })

db = SessionLocal()
added = 0
for b in books_to_add:
    book = Book(
        title=b["title"],
        author=b["author"],
        genre=b["genre"],
        publication=b["publication"],
        available_quantity=b["quantity"],
        reserved_quantity=0,
        issued_quantity=0
    )
    db.add(book)
    added += 1

db.commit()
db.close()

print(f"Seeded {added} books into the database.")