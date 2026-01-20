"""
Part 4: REST API with Flask
===========================
Build a JSON API for database operations (used by frontend apps, mobile apps, etc.)

What You'll Learn:
- REST API concepts (GET, POST, PUT, DELETE)
- JSON responses with jsonify
- API error handling
- Status codes
- Testing APIs with curl or Postman

Prerequisites: Complete part-3 (SQLAlchemy)
"""

"""
Part 4: REST API with Flask - COMPLETE SOLUTION
================================================
All exercises completed with Author model, relationships, pagination, and sorting
"""

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///api_demo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# =============================================================================
# MODELS - EXERCISE 1: Author Model with Relationship
# =============================================================================

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)
    city = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship: One author has many books
    books = db.relationship('Book', backref='author_ref', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'bio': self.bio,
            'city': self.city,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'books_count': len(self.books)
        }


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=True)
    year = db.Column(db.Integer)
    isbn = db.Column(db.String(20), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author_id': self.author_id,
            'author_name': self.author_ref.name if self.author_ref else None,
            'year': self.year,
            'isbn': self.isbn,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# =============================================================================
# BOOK API ROUTES (Updated with author relationship)
# =============================================================================

@app.route('/api/books', methods=['GET'])
def get_books():
    books = Book.query.all()
    return jsonify({
        'success': True,
        'count': len(books),
        'books': [book.to_dict() for book in books]
    })


@app.route('/api/books/<int:id>', methods=['GET'])
def get_book(id):
    book = Book.query.get(id)
    if not book:
        return jsonify({'success': False, 'error': 'Book not found'}), 404
    return jsonify({'success': True, 'book': book.to_dict()})


@app.route('/api/books', methods=['POST'])
def create_book():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    if not data.get('title'):
        return jsonify({'success': False, 'error': 'Title is required'}), 400

    # Check author exists if provided
    if data.get('author_id'):
        author = Author.query.get(data['author_id'])
        if not author:
            return jsonify({'success': False, 'error': 'Author not found'}), 404

    # Check for duplicate ISBN
    if data.get('isbn'):
        existing = Book.query.filter_by(isbn=data['isbn']).first()
        if existing:
            return jsonify({'success': False, 'error': 'ISBN already exists'}), 400

    new_book = Book(
        title=data['title'],
        author_id=data.get('author_id'),
        year=data.get('year'),
        isbn=data.get('isbn')
    )
    db.session.add(new_book)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Book created successfully',
        'book': new_book.to_dict()
    }), 201


@app.route('/api/books/<int:id>', methods=['PUT'])
def update_book(id):
    book = Book.query.get(id)
    if not book:
        return jsonify({'success': False, 'error': 'Book not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    if 'title' in data:
        book.title = data['title']
    if 'author_id' in data:
        if data['author_id']:
            author = Author.query.get(data['author_id'])
            if not author:
                return jsonify({'success': False, 'error': 'Author not found'}), 404
        book.author_id = data['author_id']
    if 'year' in data:
        book.year = data['year']
    if 'isbn' in data:
        book.isbn = data['isbn']

    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Book updated successfully',
        'book': book.to_dict()
    })


@app.route('/api/books/<int:id>', methods=['DELETE'])
def delete_book(id):
    book = Book.query.get(id)
    if not book:
        return jsonify({'success': False, 'error': 'Book not found'}), 404

    db.session.delete(book)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Book deleted successfully'})


@app.route('/api/books/search', methods=['GET'])
def search_books():
    query = Book.query

    title = request.args.get('q')
    if title:
        query = query.filter(Book.title.ilike(f'%{title}%'))

    author = request.args.get('author')
    if author:
        query = query.join(Author).filter(Author.name.ilike(f'%{author}%'))

    year = request.args.get('year')
    if year:
        query = query.filter_by(year=int(year))

    books = query.all()
    return jsonify({
        'success': True,
        'count': len(books),
        'books': [book.to_dict() for book in books]
    })


# =============================================================================
# EXERCISE 1: AUTHOR CRUD API ROUTES
# =============================================================================

@app.route('/api/authors', methods=['GET'])
def get_authors():
    authors = Author.query.all()
    return jsonify({
        'success': True,
        'count': len(authors),
        'authors': [author.to_dict() for author in authors]
    })


@app.route('/api/authors/<int:id>', methods=['GET'])
def get_author(id):
    author = Author.query.get(id)
    if not author:
        return jsonify({'success': False, 'error': 'Author not found'}), 404
    
    author_data = author.to_dict()
    author_data['books'] = [book.to_dict() for book in author.books]
    
    return jsonify({'success': True, 'author': author_data})


@app.route('/api/authors', methods=['POST'])
def create_author():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    if not data.get('name'):
        return jsonify({'success': False, 'error': 'Name is required'}), 400

    new_author = Author(
        name=data['name'],
        bio=data.get('bio'),
        city=data.get('city')
    )
    db.session.add(new_author)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Author created successfully',
        'author': new_author.to_dict()
    }), 201


@app.route('/api/authors/<int:id>', methods=['PUT'])
def update_author(id):
    author = Author.query.get(id)
    if not author:
        return jsonify({'success': False, 'error': 'Author not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    if 'name' in data:
        author.name = data['name']
    if 'bio' in data:
        author.bio = data['bio']
    if 'city' in data:
        author.city = data['city']

    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Author updated successfully',
        'author': author.to_dict()
    })


@app.route('/api/authors/<int:id>', methods=['DELETE'])
def delete_author(id):
    author = Author.query.get(id)
    if not author:
        return jsonify({'success': False, 'error': 'Author not found'}), 404

    db.session.delete(author)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Author deleted successfully'})


# =============================================================================
# EXERCISE 3: PAGINATION
# =============================================================================

@app.route('/api/books-with-pagination', methods=['GET'])
def get_books_paginated():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Limit per_page to prevent abuse
    per_page = min(per_page, 100)
    
    pagination = Book.query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'page': page,
        'per_page': per_page,
        'total': pagination.total,
        'total_pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
        'books': [book.to_dict() for book in pagination.items]
    })


# =============================================================================
# EXERCISE 4: SORTING
# =============================================================================

@app.route('/api/books-with-sorting', methods=['GET'])
def get_books_sorted():
    sort_by = request.args.get('sort', 'id')  # Default sort by id
    order = request.args.get('order', 'asc')  # asc or desc
    
    # Validate sort field
    valid_fields = ['id', 'title', 'year', 'created_at']
    if sort_by not in valid_fields:
        return jsonify({
            'success': False,
            'error': f'Invalid sort field. Valid fields: {", ".join(valid_fields)}'
        }), 400
    
    # Build query with sorting
    query = Book.query
    sort_column = getattr(Book, sort_by)
    
    if order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    books = query.all()
    
    return jsonify({
        'success': True,
        'count': len(books),
        'sorted_by': sort_by,
        'order': order,
        'books': [book.to_dict() for book in books]
    })


# =============================================================================
# COMBINED: PAGINATION + SORTING + FILTERING
# =============================================================================

@app.route('/api/books-advanced', methods=['GET'])
def get_books_advanced():
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    per_page = min(per_page, 100)
    
    # Sorting
    sort_by = request.args.get('sort', 'id')
    order = request.args.get('order', 'asc')
    
    # Filtering
    query = Book.query
    
    title = request.args.get('q')
    if title:
        query = query.filter(Book.title.ilike(f'%{title}%'))
    
    year = request.args.get('year')
    if year:
        query = query.filter_by(year=int(year))
    
    # Apply sorting
    valid_fields = ['id', 'title', 'year', 'created_at']
    if sort_by in valid_fields:
        sort_column = getattr(Book, sort_by)
        if order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
    
    # Apply pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'page': page,
        'per_page': per_page,
        'total': pagination.total,
        'total_pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
        'sorted_by': sort_by,
        'order': order,
        'books': [book.to_dict() for book in pagination.items]
    })


# =============================================================================
# HOME PAGE
# =============================================================================

@app.route('/')
def index():
    return '''
    <html>
    <head>
        <title>Part 4 - REST API Complete</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a2e; color: #eee; }
            h1 { color: #e94560; }
            h2 { color: #0f3460; border-bottom: 2px solid #e94560; padding-bottom: 10px; }
            .endpoint { background: #16213e; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #e94560; }
            .method { display: inline-block; padding: 4px 8px; border-radius: 4px; font-weight: bold; margin-right: 10px; color: white; }
            .get { background: #27ae60; }
            .post { background: #f39c12; }
            .put { background: #3498db; }
            .delete { background: #e74c3c; }
            code { background: #0f3460; padding: 2px 6px; border-radius: 3px; }
            pre { background: #0f3460; padding: 15px; border-radius: 8px; overflow-x: auto; }
            a { color: #e94560; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <h1>Part 4: REST API Demo - COMPLETE</h1>
        <p>All exercises completed! Use curl, Postman, or the <a href="/frontend.html">Frontend Demo</a> to test.</p>

        <h2>📚 Book API Endpoints</h2>
        <div class="endpoint">
            <span class="method get">GET</span>
            <code>/api/books</code> - Get all books
            <br><a href="/api/books" target="_blank">Try it →</a>
        </div>
        <div class="endpoint">
            <span class="method get">GET</span>
            <code>/api/books/&lt;id&gt;</code> - Get single book
        </div>
        <div class="endpoint">
            <span class="method post">POST</span>
            <code>/api/books</code> - Create new book
        </div>
        <div class="endpoint">
            <span class="method put">PUT</span>
            <code>/api/books/&lt;id&gt;</code> - Update book
        </div>
        <div class="endpoint">
            <span class="method delete">DELETE</span>
            <code>/api/books/&lt;id&gt;</code> - Delete book
        </div>
        <div class="endpoint">
            <span class="method get">GET</span>
            <code>/api/books/search?q=&lt;title&gt;</code> - Search books
        </div>

        <h2>👤 Author API Endpoints (Exercise 1)</h2>
        <div class="endpoint">
            <span class="method get">GET</span>
            <code>/api/authors</code> - Get all authors
            <br><a href="/api/authors" target="_blank">Try it →</a>
        </div>
        <div class="endpoint">
            <span class="method get">GET</span>
            <code>/api/authors/&lt;id&gt;</code> - Get single author with books
        </div>
        <div class="endpoint">
            <span class="method post">POST</span>
            <code>/api/authors</code> - Create new author
        </div>
        <div class="endpoint">
            <span class="method put">PUT</span>
            <code>/api/authors/&lt;id&gt;</code> - Update author
        </div>
        <div class="endpoint">
            <span class="method delete">DELETE</span>
            <code>/api/authors/&lt;id&gt;</code> - Delete author
        </div>

        <h2>📄 Pagination (Exercise 3)</h2>
        <div class="endpoint">
            <span class="method get">GET</span>
            <code>/api/books-with-pagination?page=1&per_page=5</code>
            <br><a href="/api/books-with-pagination?page=1&per_page=5" target="_blank">Try it →</a>
        </div>

        <h2>🔢 Sorting (Exercise 4)</h2>
        <div class="endpoint">
            <span class="method get">GET</span>
            <code>/api/books-with-sorting?sort=title&order=desc</code>
            <br><a href="/api/books-with-sorting?sort=title&order=asc" target="_blank">Try it →</a>
        </div>

        <h2>🚀 Advanced (Pagination + Sorting + Filtering)</h2>
        <div class="endpoint">
            <span class="method get">GET</span>
            <code>/api/books-advanced?page=1&per_page=5&sort=year&order=desc&q=python</code>
            <br><a href="/api/books-advanced?page=1&per_page=5&sort=year&order=desc" target="_blank">Try it →</a>
        </div>

        <h2>Example curl Commands:</h2>
        <pre>
# Create an author
curl -X POST http://localhost:5000/api/authors \\
  -H "Content-Type: application/json" \\
  -d '{"name": "Eric Matthes", "bio": "Python educator", "city": "Alaska"}'

# Create a book with author
curl -X POST http://localhost:5000/api/books \\
  -H "Content-Type: application/json" \\
  -d '{"title": "Python Crash Course", "author_id": 1, "year": 2019}'

# Get books with pagination
curl "http://localhost:5000/api/books-with-pagination?page=1&per_page=5"

# Get sorted books
curl "http://localhost:5000/api/books-with-sorting?sort=year&order=desc"
        </pre>
    </body>
    </html>
    '''


# =============================================================================
# INITIALIZE DATABASE
# =============================================================================

def init_db():
    with app.app_context():
        db.create_all()

        if Author.query.count() == 0:
            # Create sample authors
            authors = [
                Author(name='Eric Matthes', bio='Python educator and author', city='Alaska'),
                Author(name='Miguel Grinberg', bio='Software developer and Flask expert', city='Portland'),
                Author(name='Robert C. Martin', bio='Software craftsman and author', city='Chicago'),
            ]
            db.session.add_all(authors)
            db.session.commit()
            print('Sample authors added!')

            # Create sample books with author relationships
            books = [
                Book(title='Python Crash Course', author_id=1, year=2019, isbn='978-1593279288'),
                Book(title='Flask Web Development', author_id=2, year=2018, isbn='978-1491991732'),
                Book(title='Clean Code', author_id=3, year=2008, isbn='978-0132350884'),
                Book(title='Python Testing', author_id=1, year=2020, isbn='978-1593279509'),
            ]
            db.session.add_all(books)
            db.session.commit()
            print('Sample books added!')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)

# =============================================================================
# REST API CONCEPTS:
# =============================================================================
#
# HTTP Method | CRUD      | Typical Use
# ------------|-----------|---------------------------
# GET         | Read      | Retrieve data
# POST        | Create    | Create new resource
# PUT         | Update    | Update entire resource
# PATCH       | Update    | Update partial resource
# DELETE      | Delete    | Remove resource
#
# =============================================================================
# HTTP STATUS CODES:
# =============================================================================
#
# Code | Meaning
# -----|------------------
# 200  | OK (Success)
# 201  | Created
# 400  | Bad Request (client error)
# 404  | Not Found
# 500  | Internal Server Error
#
# =============================================================================
# KEY FUNCTIONS:
# =============================================================================
#
# jsonify()           - Convert Python dict to JSON response
# request.get_json()  - Get JSON data from request body
# request.args.get()  - Get query parameters (?key=value)
#
# =============================================================================


# =============================================================================
# EXERCISE:
# =============================================================================
#
# 1. Create new class say "Author" with fields id, name, bio, city with its table. 
# Write all CRUD api routes for it similar to Book class.
# Additionally try to link Book and Author class such that each book has one author and one author can have multiple books.

# 1. Create 2 simple frontend using JavaScript fetch()
# This is a bigger exercise. Create a frontend in HTML and JS that uses all api routes and displays data dynamically, along with create/edit/delete functionality.
# Since the API is through n through accessible on the computer/server, you don't need to use render_template from flask, instead, 
# you can directly use ipaddress:portnumber/apiroute from any where. So your HTML JS code can be anywhere on computer (not necessarily in flask)  

# 3. Add pagination: `/api/books?page=1&per_page=10` 
# Hint - the sqlalchemy provides paginate method. 
# OPTIONAL - For ease of understanding, create a new api say /api/books-with-pagination which takes page number and number of books per page

# 4. Add sorting: `/api/books?sort=title&order=desc`
# OPTIONAL - For ease of understanding, create a new api say /api/books-with-sorting
#
# =============================================================================