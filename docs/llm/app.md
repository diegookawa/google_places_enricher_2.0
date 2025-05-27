# Test Suite Specification for `src/app.py` (Flask Application)

## 1. General Principles

- Use `pytest` and Flask's test client.
- Isolate file I/O using temporary directories and monkeypatching.
- Mock external dependencies (e.g., `request_google_places`, `calculate_coordinates`).
- Cover both success and failure/error scenarios for each route.
- Validate both HTTP status codes and response content.

## 2. Route-by-Route Specification

### `/view_data` (GET)
- **Success:** Returns HTML with establishment data if CSV exists and is well-formed.
- **File Not Found:** Returns error message if CSV is missing.
- **Malformed CSV:** Returns error if required columns are missing or CSV is unreadable.

### `/update_coordinates_csv` (POST)
- **Success:** Accepts JSON with coordinates, writes CSV, returns success JSON.
- **Missing/Invalid Data:** Returns error if coordinates are missing or malformed.
- **File Write Error:** Simulate file system errors.

### `/get_categories` (GET)
- **Success:** Returns categories from CSV as JSON.
- **File Not Found:** Returns error JSON.
- **Malformed CSV:** Returns error JSON.

### `/update_categories_and_process_data` (POST)
- **Success:** Accepts categories, writes CSV, calls `request_google_places`, returns success.
- **No Categories:** Returns 400 error.
- **request_google_places Failure:** Returns error if API call fails or returns unexpected result.
- **File Write Error:** Simulate file system errors.

### `/calculate_coordinates` (POST)
- **Success:** Mocks `calculate_coordinates`, checks JSON response.
- **Missing/Invalid Data:** Returns error for missing fields.

### `/get_coordinates` (GET)
- **Success:** Returns coordinates as JSON from CSV.
- **File Not Found/Malformed:** Returns error or empty result.

### `/` (GET, POST)
- **GET:** Renders main page.
- **POST:** Sets API key, redirects.

### `/coordinates_definition`, `/components_result`, `/coordinates_result`, `/enrich_data`, `/match_categories`
- **GET:** Renders respective templates.

### `/upload_csv` (POST)
- **Success:** Accepts CSV, writes to input, returns categories.
- **No File:** Returns error.
- **Malformed CSV:** Returns error.

### `/categories` (GET, POST)
- **GET:** Renders template.
- **POST Success:** Accepts CSV, returns categories.
- **POST No File/Invalid Format:** Returns error.
- **POST Invalid File Content or Write Error:** Parameterized tests cover both invalid file content and file write errors.

### `/get_enrichment_categories` (GET)
- **Success:** Returns enrichment categories from CSV.
- **File Not Found/Malformed:** Returns error.

### `/enrichment_categories` (POST)
- **Success:** Accepts categories, writes CSV, returns success.
- **Invalid Structure:** Returns error for wrong data format.
- **File Write Error:** Simulate file system errors.

### `/get_available_datasets` (GET)
- **Success:** Lists available CSV datasets.
- **File System Error:** Returns error.

### `/upload_dataset` (POST)
- **Success:** Accepts valid dataset, writes file, returns success.
- **Missing Columns:** Returns error and removes file.
- **No File/Invalid Format:** Returns error.
- **Invalid File Content or Write Error:** Parameterized tests cover both invalid file content and file write errors.

### `/get_categories_to_match` (GET)
- **Success:** Returns matching categories and phrases.
- **Missing Files/Malformed:** Returns error.

### `/export_enriched_dataset` (POST)
- **Success:** Accepts enrichment data, writes new CSV, returns download URL.
- **Missing Files/Malformed:** Returns error.

## 3. Mocking & Isolation

- Use `tmp_path` for all file operations.
- Patch `CONFIG_PATH` in the config module to use a temporary config file for test isolation.
- Mock utility functions (`request_google_places`, `calculate_coordinates`, etc.) as needed.

## 4. Edge Cases

- Test for missing, malformed, or empty files.
- Test for invalid/missing request data.
- Test for file system errors (permission denied, disk full, etc.).
- Test for unexpected exceptions.

## 5. Coverage

- Ensure all routes, branches, and error paths are covered.
- Validate both content and side effects (e.g., files written, files deleted).

## 6. Additional Robustness Areas

- **Security:** Test for directory traversal, unsafe file names, and allowed file types.
- **HTTP Method Restrictions:** Ensure endpoints reject unsupported methods.
- **Configuration Management:** Test reading/writing of config values via `get_config_value`/`set_config_value` and persistence in `config.json`. In tests, patch `CONFIG_PATH` to use a temporary config file for isolation.
- **Concurrency:** Simulate simultaneous uploads/writes.
