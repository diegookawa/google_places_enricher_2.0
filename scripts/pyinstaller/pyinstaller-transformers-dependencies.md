# Including All `transformers` Dependencies with PyInstaller

This guide explains how to reliably bundle the HuggingFace `transformers` library and all its dependencies with PyInstaller, avoiding runtime errors due to missing modules or metadata.

---

## 1. List All Dependencies

First, get all direct and transitive dependencies for your installed `transformers` version:

- **Direct dependencies:**  
  ```sh
  pip show transformers
  ```
  Look for the `Requires:` line.

- **Full dependency tree:**  
  ```sh
  pip install pipdeptree
  pipdeptree --packages transformers
  ```

Example output (June 2025, transformers==4.52.4):

```
transformers==4.52.4
├── filelock
├── huggingface-hub
│   ├── filelock
│   ├── fsspec
│   ├── packaging
│   ├── PyYAML
│   ├── requests
│   │   ├── charset-normalizer
│   │   ├── idna
│   │   ├── urllib3
│   │   └── certifi
│   ├── tqdm
│   │   └── colorama
│   └── typing_extensions
├── numpy
├── packaging
├── PyYAML
├── regex
├── requests
│   ├── charset-normalizer
│   ├── idna
│   ├── urllib3
│   └── certifi
├── tokenizers
│   └── huggingface-hub
├── safetensors
└── tqdm
    └── colorama
```

---

## 2. Update PyInstaller Hook

Edit `scripts/pyinstaller/hooks/hook-transformers.py` to collect data files and metadata for all dependencies:

```python
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

datas = []
datas += collect_data_files('transformers', include_py_files=True, includes=['**/*.py'])
datas += copy_metadata('transformers')
datas += collect_data_files('filelock', include_py_files=True, includes=['**/*.py'])
datas += copy_metadata('filelock')
datas += collect_data_files('safetensors', include_py_files=True, includes=['**/*.py'])
datas += copy_metadata('safetensors')
datas += collect_data_files('yaml', include_py_files=True, includes=['**/*.py'])
datas += copy_metadata('pyyaml')
datas += collect_data_files('tqdm', include_py_files=True, includes=['**/*.py'])
datas += copy_metadata('tqdm')
datas += copy_metadata('setuptools')
datas += copy_metadata('regex')
datas += collect_data_files('requests', include_py_files=True, includes=['**/*.py'])
datas += copy_metadata('requests')
datas += collect_data_files('packaging', include_py_files=True, includes=['**/*.py'])
datas += copy_metadata('packaging')
datas += collect_data_files('tokenizers', include_py_files=True, includes=['**/*.py'])
datas += copy_metadata('tokenizers')
datas += collect_data_files('huggingface_hub', include_py_files=True, includes=['**/*.py'])
datas += copy_metadata('huggingface_hub')
datas += collect_data_files('fsspec', include_py_files=True, includes=['**/*.py'])
datas += copy_metadata('fsspec')
datas += collect_data_files('charset_normalizer', include_py_files=True, includes=['**/*.py'])
datas += copy_metadata('charset_normalizer')
datas += collect_data_files('idna', include_py_files=True, includes=['**/*.py'])
datas += copy_metadata('idna')
datas += collect_data_files('urllib3', include_py_files=True, includes=['**/*.py'])
datas += copy_metadata('urllib3')
datas += collect_data_files('certifi', include_py_files=True, includes=['**/*.py'])
datas += copy_metadata('certifi')
datas += collect_data_files('colorama', include_py_files=True, includes=['**/*.py'])
datas += copy_metadata('colorama')
datas += collect_data_files('typing_extensions', include_py_files=True, includes=['**/*.py'])
datas += copy_metadata('typing_extensions')
datas += collect_data_files('numpy', include_py_files=True, includes=['**/*.py'])
datas += copy_metadata('numpy')
# Optional: sentencepiece, protobuf if used by your models
# datas += collect_data_files('sentencepiece', include_py_files=True, includes=['**/*.py'])
# datas += copy_metadata('sentencepiece')
# datas += collect_data_files('protobuf', include_py_files=True, includes=['**/*.py'])
# datas += copy_metadata('protobuf')
```

---

## 3. Add All Hidden Imports

In your PyInstaller build script (e.g., `scripts/pyinstaller/pyinstaller.ps1`), add all dependencies as `--hidden-import`:

```powershell
--hidden-import=transformers `
--hidden-import=tokenizers `
--hidden-import=transformers.models `
--hidden-import=filelock `
--hidden-import=safetensors `
--hidden-import=yaml `
--hidden-import=sentence_transformers `
--hidden-import=tqdm `
--hidden-import=huggingface_hub `
--hidden-import=fsspec `
--hidden-import=charset_normalizer `
--hidden-import=idna `
--hidden-import=urllib3 `
--hidden-import=certifi `
--hidden-import=colorama `
--hidden-import=typing_extensions `
--hidden-import=numpy `
# Optional: uncomment if used
# --hidden-import=sentencepiece `
# --hidden-import=protobuf `
```

- Some packages (like `pyyaml`) have a different import name than their package name. 

---

## 4. Build and Test

Run your PyInstaller build. If you still get missing module or metadata errors, check for additional dependencies in your environment and add them to both the hook and hidden-imports.

---

## 5. What We Did in This Project

- Used `pipdeptree` to get the full dependency tree for `transformers`.
- Updated the PyInstaller hook to collect data and metadata for all direct and transitive dependencies.
- Added all dependencies as `--hidden-import` in the build script.
- Noted optional dependencies (`sentencepiece`, `protobuf`) for some models.
- This approach avoids the slow loop of "build, error, fix, repeat" and ensures all required packages are bundled for production.

---

## 6. Tips

- Always check your actual environment for the most accurate dependency list.
- Some dependencies may only be needed for specific models or features.
- If you use additional HuggingFace features, check their docs for further requirements.
