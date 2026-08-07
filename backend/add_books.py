from database import SessionLocal, Book

books_data = [
    ("Introduction to Algorithms", "Thomas H. Cormen", "CS/Technical", 5),
    ("Clean Code", "Robert C. Martin", "CS/Technical", 4),
    ("The Pragmatic Programmer", "Andrew Hunt", "CS/Technical", 4),
    ("Python Crash Course", "Eric Matthes", "CS/Technical", 6),
    ("Operating System Concepts", "Abraham Silberschatz", "CS/Technical", 4),
    ("Computer Networks", "Andrew S. Tanenbaum", "CS/Technical", 3),
    ("Database System Concepts", "Abraham Silberschatz", "CS/Technical", 4),
    ("Design Patterns", "Erich Gamma", "CS/Technical", 3),
    ("Cracking the Coding Interview", "Gayle Laakmann McDowell", "CS/Technical", 5),
    ("Artificial Intelligence: A Modern Approach", "Stuart Russell", "CS/Technical", 3),
    ("The Alchemist", "Paulo Coelho", "Fiction", 5),
    ("To Kill a Mockingbird", "Harper Lee", "Fiction", 3),
    ("1984", "George Orwell", "Fiction", 4),
    ("The Great Gatsby", "F. Scott Fitzgerald", "Fiction", 3),
    ("Harry Potter and the Sorcerer's Stone", "J.K. Rowling", "Fiction", 6),
    ("The Kite Runner", "Khaled Hosseini", "Fiction", 3),
    ("Life of Pi", "Yann Martel", "Fiction", 3),
    ("Five Point Someone", "Chetan Bhagat", "Fiction", 5),
    ("Atomic Habits", "James Clear", "Self-Help", 6),
    ("Think and Grow Rich", "Napoleon Hill", "Self-Help", 4),
    ("The 7 Habits of Highly Effective People", "Stephen R. Covey", "Self-Help", 3),
    ("Rich Dad Poor Dad", "Robert Kiyosaki", "Self-Help", 5),
    ("Ikigai", "Hector Garcia", "Self-Help", 4),
    ("Wings of Fire", "A.P.J. Abdul Kalam", "Biography", 5),
    ("Steve Jobs", "Walter Isaacson", "Biography", 3),
    ("Sapiens: A Brief History of Humankind", "Yuval Noah Harari", "History", 4),
    ("The Diary of a Young Girl", "Anne Frank", "Biography", 3),
    ("A Brief History of Time", "Stephen Hawking", "Science", 3),
    ("The Selfish Gene", "Richard Dawkins", "Science", 3),
    ("Fermat's Enigma", "Simon Singh", "Science", 3),
]

db = SessionLocal()

for title, author, genre, qty in books_data:
    existing = db.query(Book).filter(Book.title == title).first()
    if existing:
        print(f"Skipped (already exists): {title}")
        continue

    book = Book(
        title=title,
        author=author,
        genre=genre,
        available_quantity=qty,
        reserved_quantity=0,
        issued_quantity=0
    )
    db.add(book)
    print(f"Added: {title}")

db.commit()
db.close()
print("\nDone! All books added.")