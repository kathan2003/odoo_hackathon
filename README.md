# TransitOps — Clickable CRUD Version

This build keeps the existing TransitOps UI alignment and adds working database actions.

## Working actions

- Vehicles: add, edit, delete, search, status filter, CSV export
- Drivers: add, edit, delete, search, status filter, CSV export
- Trips: add, edit, delete, search, status filter, CSV export
- Maintenance: add, edit, delete, search, status filter, CSV export
- Fuel: add, edit, delete, search, vehicle filter, CSV export
- Expenses: add, edit, delete, search, category filter, CSV export
- Dashboard: live cards, live charts, recent-trip links, export
- Reports: live database analytics and PDF export
- Navbar: global search, notifications, profile and settings

Fuel and maintenance records automatically create/update linked expense records. Deleting them removes the linked expense.

## Easiest Windows run

Double-click `RUN_TRANSITOPS.bat`.

The first run automatically:

1. Creates a virtual environment
2. Installs packages
3. Creates `.env`
4. Creates the SQLite database
5. Inserts demonstration data
6. Starts the Flask application

Open: http://127.0.0.1:5000

## Manual run

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

No `flask init-db` or `seed-demo` command is required for the first run.

## Switch to MySQL later

Create the database:

```sql
CREATE DATABASE transitops CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Then edit `.env`:

```env
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/transitops
AUTO_CREATE_TABLES=true
AUTO_SEED=true
```

Delete or rename the local `transitops.db` only if you no longer need the SQLite test data.
