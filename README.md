# Kanban Django

Kanban Django is a lightweight Kanban web app built with Django. Key features include:

- Multiple boards with configurable columns (Backlog, In Progress, Done, etc.).
- Drag-and-drop cards with title, description, priority, due date, and assignee fields.
- Overview lanes that filter cards across boards by board, column, assignee, priority, due dates, or sort order, with persisted settings stored in the database.

## Project Structure

- `board/` – Core Kanban app containing models, views, templates, static assets, and migrations.
- `kanban/` – Django project configuration, including settings and URL routing.
- `manage.py` – Django management entry point.
- `db.sqlite3` – Default SQLite database for local development.

## Setup

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Apply database migrations:
   ```bash
   python manage.py migrate
   ```
4. Start the development server:
   ```bash
   python manage.py runserver
   ```
5. Open the app in your browser at http://127.0.0.1:8000/

## Tests

Run the automated test suite with:
```bash
python manage.py test
```

## License

Released under the MIT License (see `LICENSE` if included).
