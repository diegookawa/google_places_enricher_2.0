# PyInstaller Inclusion Checklist

## Instructions

For each file or folder in the checklist:
1. Open the file and review its contents.
2. Check for:
   - Python imports (modules used)
   - Data files accessed (CSV, JSON, etc.)
   - Templates and static files (for Flask)
   - Any files dynamically loaded or written
3. Mark the file as reviewed in this checklist.
4. For code files, add a note on how you checked if it is required by the executable (e.g., imported, loaded with open(), referenced in Flask, etc.).

## Project Files and Folders

- src/app.py
- [x] src/flows.py  
  - Reviewed: Provides core data processing and API interaction logic. Imports `shapely`, `pyproj`, `requests`, and project modules (`utils`, `config`). Reads/writes CSV files in `./static/data/output/` and `./static/data/input/`. Required by the executable for backend data flows.
- [x] src/utils.py  
  - Reviewed: Provides utility functions for file reading, API requests, data processing, and phrase/similarity generation. Imports `config`, `requests`, `json`, `pandas`, `re`, `sentence_transformers`. Reads/writes files in `./static/data/output/` and `./static/data/input/`. Required by the executable for backend processing.
- [x] src/config.py  
  - Reviewed: Provides configuration management functions. Imports `os`, `json`. Reads from and writes to `config.json`. Required by the executable for runtime configuration.
- [x] src/main.py  
  - Reviewed: Main entry point. Imports `app` from `app.py`, sets up logging, handles exceptions, manages ports, launches Flask app and PyWebView window. Uses `logs/` for log files. Required by the executable to start the application.
- [x] src/conftest.py  
  - Reviewed: Pytest configuration file. Imports `pytest`, `sys`, `pathlib`. Disables real HTTP requests during tests. Not required by the executable, only for testing.
- [x] src/__init__.py  
  - Reviewed: Empty file. Serves as a package marker so Python recognizes `src` as a package. Not required for logic, but necessary for package structure.
- [x] src/static/  
  - Reviewed: Contains CSS and image files referenced in Flask templates and code (e.g., via `url_for('static', ...)`). Required for web interface styling and serving static assets. Must be included in the executable.
- [x] src/templates/  
  - Reviewed: Contains HTML templates referenced in Flask routes via `render_template` (e.g., `main_page.html`, `coordinates_definition.html`, etc.). Required for the web interface. Must be included in the executable.
- [x] src/uploads/  
  - Reviewed: Used as the upload directory for CSV files in the Flask app (`UPLOAD_FOLDER = 'uploads/'`). Required for file upload functionality. Must be included in the executable.
- [x] static/data/  
  - Reviewed: Contains input and output CSV files used throughout the codebase for data processing (read/write operations in Flask routes, utility functions, and templates). Required for application functionality. Must be included in the executable.
- [x] requirements.txt  
  - Reviewed: Lists all Python dependencies required by the executable (Flask, pandas, requests, shapely, pyproj, sentence-transformers, etc.). Essential for installing dependencies during packaging. Must be included.
- [x] pyproject.toml  
  - Reviewed: Defines the build system and dependencies for the project (runtime and dev, e.g., Flask, requests, shapely, pyproj, pandas, sentence-transformers, pyinstaller). Essential for building and packaging the executable. Must be included.
- poetry.lock

---

Check each file/folder for:
- Python imports (modules used)
- Data files accessed (CSV, JSON, etc.)
- Templates and static files (for Flask)
- Any files dynamically loaded or written

Mark files as reviewed as you go.
