# PyInstaller Workflow for Ensuring All Transformers Dependencies Are Included

## Problem

When using PyInstaller with complex libraries like `transformers`, runtime errors can occur due to missing package metadata or dynamically imported dependencies. The naive approach is to build, run, and fix errors one-by-one, but this is slow and manual.

## Improved Workflow

### 1. List All Direct Dependencies

Use pip to list all direct dependencies of transformers:

```sh
pip show transformers
```

Look for the `Requires:` line. For example:
```
Requires: filelock, huggingface-hub, numpy, packaging, pyyaml, regex, requests, safetensors, tqdm
```

### 2. List All Transitive Dependencies (Untested)

For a full tree (including sub-dependencies):

```sh
pip install pipdeptree
pipdeptree --packages transformers
```

### 3. Create PyInstaller Hooks for Each Dependency

For each dependency (e.g., `filelock`, `safetensors`, `pyyaml`, `tqdm`, `regex`, `requests`, `packaging`, etc):

- Create a hook file in `scripts/pyinstaller/hooks/` named `hook-<importable_module>.py`
- The importable module is usually the PyPI package name, but sometimes differs (e.g., `pyyaml` is imported as `yaml`).

Example for `filelock`:
```python
from PyInstaller.utils.hooks import collect_data_files, copy_metadata
datas = collect_data_files('filelock', include_py_files=True, includes=['**/*.py'])
datas += copy_metadata('filelock')
```

Example for `pyyaml` (imported as `yaml`):
```python
from PyInstaller.utils.hooks import collect_data_files, copy_metadata
datas = collect_data_files('yaml', include_py_files=True, includes=['**/*.py'])
datas += copy_metadata('pyyaml')
```

### 4. Add Each Importable Module to PyInstaller Hidden Imports

In your PyInstaller command or spec, add:
```
--hidden-import=<importable_module>
```
For example:
```
--hidden-import=filelock --hidden-import=safetensors --hidden-import=yaml --hidden-import=tqdm --hidden-import=regex --hidden-import=requests --hidden-import=packaging
```

### 5. Build and Test

Run your PyInstaller build. If you still get missing metadata errors, repeat steps 3-4 for any additional packages reported.

### 6. Notes

- Some dependencies may only be required for certain features or models.
- Some packages (like `pyyaml`) have a different import name than their PyPI name.
- You can combine multiple hooks into one, or keep them separate for clarity.
- This process avoids the slow loop of "build, error, fix, repeat" for most common cases.

---

## Example: transformers dependencies (as of June 2025)

- filelock
- safetensors
- pyyaml (import as yaml)
- tqdm
- regex
- requests
- packaging
- huggingface_hub
- numpy

Check your actual environment with `pip show transformers` and `pipdeptree` for the most accurate list.
