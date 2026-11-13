# ErrandMate

A Tkinter + SQLite errand-running platform prototype.

## Run

```bash
python main.py
```

The app creates `ErrandMate.db` automatically in the project folder.

## Current structure

```text
ErrandMate/
├── main.py
├── config.py
├── database.py
├── security.py
├── validators.py
├── ui/
│   ├── __init__.py
│   ├── widgets.py
│   ├── scroll.py
│   ├── cards.py
│   └── nav.py
└── pages/
    ├── __init__.py
    ├── auth_pages.py
    ├── task_pages.py
    └── profile_page.py
```

## UI update notes

This version includes a more modern visual pass:

- cleaner light background and deep slate navigation
- updated indigo-based design system
- Segoe UI typography across the app
- improved login and registration screens
- cleaner reusable card, button, banner, and empty-state components
- more polished task cards with clearer chips and metadata
- improved dashboard/header surfaces
- improved profile card and statistic blocks
- refined spacing and visual hierarchy
