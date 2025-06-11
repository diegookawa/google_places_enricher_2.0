from PyInstaller.utils.hooks import collect_data_files, copy_metadata
datas = collect_data_files('packaging', include_py_files=True, includes=['**/*.py'])
datas += copy_metadata('packaging')
