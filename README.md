# Flask To-Do Application - Enhanced with API & Tagging

This project upgrades a basic Flask To-Do app into a more robust and extensible application.

## Key Enhancements:

1.  **Comprehensive RESTful API**:
    * Full CRUD operations for To-Do items (`/api/v1/todos`) and Tags (`/api/v1/tags`).
    * Uses standard REST principles (HTTP methods, JSON format, proper status codes).
    * Enables programmatic access for integration with other applications (e.g., mobile apps).

2.  **Tag Management System**:
    * Implemented a many-to-many relationship for flexible task categorization.
    * Allows multiple tags per To-Do, with dynamic creation and filtering by tag.

3.  **Enhanced Web UI**:
    * Integrated tag input and display into the web interface.
    * Added tag filtering and a new "Edit Details" modal for streamlined updates.

## Technical Highlights:

* **Models**: SQLAlchemy models for `Todo` and `Tag` with an association table.
* **API Design**: Modularized with Flask Blueprints.
* **Validation**: Robust input validation for API and web forms.
* **Testing**: Extensive unit tests using `pytest` and `pytest-cov`, achieving **100% test coverage** on `app.py`'s functional code. Includes comprehensive positive and negative test cases for all CRUD operations.

## Setup & Running:

1.  **Clone**: `git clone https://github.com/YOUR_USERNAME/flask-todo.git` (replace `YOUR_USERNAME`)
2.  **CD**: `cd flask-todo`
3.  **Env**: `python -m venv venv` & `source venv/bin/activate` (or `.\venv\Scripts\activate` on Windows)
4.  **Install**: `pip install Flask Flask-SQLAlchemy pytest pytest-flask pytest-cov`
5.  **Run App**: `python app.py` (access at `http://127.0.0.1:5000/`)
6.  **Run Tests**: `pytest --cov=app --cov-report=term-missing` (should show 100% coverage)

---