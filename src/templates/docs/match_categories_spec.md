# Match Categories: Download, Import, and Export Enriched Dataset (JSON Specification)

## Overview
This document specifies the requirements and JSON data structure for the features:
- Download matches
- Import matches
- Export enriched dataset

All data import/export must use JSON format as described below.

---

## JSON Data Structure

The JSON file for matches must have the following structure:

```json
{
  "categories": [
    "Category 1",
    "Category 2",
    "Category 3",
    "..."
  ],
  "phrases": [
    "Phrase 1",
    "Phrase 2",
    "Phrase 3",
    "..."
  ],
  "matches": [
    {
      "phrase_idx": 0,                // Index in the phrases array
      "category_idx": 2,              // Index in the categories array (selected match)
      "selected_score": 0.91,         // Score of the selected match (from match_options[matched_option_idx].score)
      "matched_option_idx": 0,        // Index in match_options array that was selected by the user
      "best_score": 0.91,             // Highest score among match_options (for display in the 'Best Score' column)
      "match_options": [
        { "category_idx": 2, "score": 0.91 },
        { "category_idx": 1, "score": 0.75 },
        { "category_idx": 0, "score": 0.60 }
      ]
    },
    // ... more match objects ...
  ]
}
```

---

## 1. Download Matches
- Add a "Download matches" button.
- When clicked, export the current matches as a JSON file using the structure above.
- The file should be named `matches_YYYYMMDD_HHMMSS.json` (e.g., `matches_20250424_153000.json`).
- The exported JSON must record the match the user selected for each phrase (using `matched_option_idx` and `category_idx`), which may not be the highest score.
- The `best_score` field must always be the highest score among `match_options` and is used for the 'Best Score' column in the UI.
- The `selected_score` field must be the score of the user's selected match (from `match_options[matched_option_idx].score`) and is used for the dropdown selection.

## 2. Import Matches
- Add an "Import matches" button and file input (accepting `.json`).
- When a file is selected, read and parse the JSON.
- Validate that the file contains `categories`, `phrases`, and `matches` arrays with the correct structure.
- If valid, update the UI and internal data structures to reflect the imported matches.
- When restoring, use the `matched_option_idx` and `category_idx` to restore the user's selected match for each phrase, not just the highest score.
- When restoring the selection, display the `selected_score` in the dropdown for the selected match.
- If the selected match is not present in the dropdown (e.g., due to "see more" functionality), add the value to the dropdown using the existing logic for adding options.
- The 'Best Score' column must always display the `best_score` value, but the dropdown and selection must use the `selected_score` and `matched_option_idx`.
- If invalid, show an error message.

## 3. Export Enriched Dataset
- Add an "Export enriched dataset" button.
- When clicked, collect all current matches and send them to the backend as JSON (using the structure above).
- The backend processes the matches and generates an enriched dataset (CSV or other format) by adding new columns to the original dataset (selected in the previous page).
- **How matching is done:**
    - The original dataset must have a column called `phrase` (or similar, e.g., `phrase_establishment`), which is the phrase calculated for each establishment before sending the phrases to the client for matching.
    - If the original dataset does not have a phrase column (e.g., `phrase`, `phrase_establishment`, or `matching_phrase`), the backend must generate this column itself using the same logic/code used to generate phrases for the matching process (e.g., using `create_estab_phrase`).
    - The backend should join the original dataset with the matches using this `phrase` column and the `phrases` array from the matches JSON.
    - For each row in the original dataset, find the corresponding `phrase` in the `phrases` array. Use the index (`phrase_idx`) to look up the match object in the `matches` array.
    - For each row, add:
        - All original columns from the input file.
        - `phrase_idx` (index in the `phrases` array).
        - `matched_phrase` (the phrase string from the `phrases` array).
        - `category_idx` (index in the `categories` array from the match object).
        - `matched_category` (the category string from the `categories` array).
        - `selected_score` (from the match object).
        - `best_score` (from the match object).
    - Do NOT include the full list of match options in the output.
- The backend returns a download link for the generated file.
- The frontend triggers the download or provides a link to the user.

### Notes
- The enriched dataset should make it easy to analyze which phrases and categories were matched, and how confident the match was.
- All original columns from the input file must be preserved in the output.
- Only the selected match and best score are included for each row; match options are not exported.
- If a row in the original dataset does not have a matching phrase, leave the enrichment columns blank or null.

---

## See More Functionality

The "see more" functionality in the UI is used to keep the dropdown for match selection concise and user-friendly. By default, only the top-ranked matches (e.g., Excellent and Good) are shown directly in the dropdown. If there are additional matches (e.g., Fair or Poor), a special option labeled "See more matches..." is added to the dropdown. When the user selects this option, a modal dialog opens displaying all possible matches for that phrase, including lower-ranked ones. The user can then select any match from the modal, and if the selected match is not already present in the dropdown, it is dynamically added to the dropdown using the existing logic. This ensures that any user selection, even from the extended list, is always available and restorable in the dropdown.

### Specification Addition
- When importing matches, if the user's selected match (from `category_idx` in the match object) is not present in the dropdown (because it was only available via "see more"), the system must add it to the dropdown using the same logic as when a user selects a match from the modal.
- The dropdown must always reflect the user's selection, regardless of whether it was originally visible or only available via "see more".
- The modal for "see more" must display all match options for the phrase, allowing the user to select any match, which will then be added to the dropdown if not already present.

---

## General UI/UX
- All three buttons should be clearly visible and grouped together.
- Provide user feedback for success/failure (e.g., alerts, error messages).
- Ensure all file operations (download/upload) work cross-browser and on Windows.

## Backend
- Implement an endpoint to accept matches as JSON and return the enriched dataset for download.
- Validate input data and handle errors gracefully.
- Ensure file paths and permissions are handled securely.

## Validation
- Test with various match table sizes and edge cases (empty, large, malformed JSON).
- Ensure that import/export preserves all relevant data and formatting.

---

**End of Specification**
