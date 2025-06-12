# PyInstaller Packaging Workflow

This guide documents the repeatable workflow for building and debugging the Google Places Enricher 2.0 application using PyInstaller.

---

## 1. Build and Run Automatically

Open a terminal and run the PowerShell automation script from the `scripts/pyinstaller/` directory:

```powershell
cd scripts/pyinstaller
./pyinstaller-auto.ps1
```

This script will:
- Build the executable using the provided `.spec` file.
- Run the generated executable automatically.
- Print any errors encountered during build or execution.

---

## 3. Debug and Iterate

If you encounter errors (e.g., missing modules, metadata, or runtime issues):

- **Check the error message** for missing imports or data.
- **Add or update PyInstaller hooks** in `scripts/pyinstaller/hooks/` as needed.
  - Use `collect_data_files` or `copy_metadata` for missing data or metadata.
- **Add hidden imports or data files** by editing `pyinstaller.ps1`:
  - Use `--hidden-import` for dynamic imports.
  - Use `--add-data` for required data files.
- **Re-run the build script** to test changes.

---

## 4. Repeat

Continue iterating:
- Build → Run → Debug → Update hooks/arguments → Repeat

---

## Tips

- Custom hooks for problematic packages (e.g., `transformers`, `tqdm`) are in `scripts/pyinstaller/hooks/`.
- The `.spec` file (`Google Places Enricher 2.0.spec`) controls the build process.
- Use verbose mode (`--log-level=DEBUG`) for more detailed PyInstaller output.
- For persistent issues, consult [PyInstaller documentation](https://pyinstaller.org/en/stable/) or search for similar errors online.
