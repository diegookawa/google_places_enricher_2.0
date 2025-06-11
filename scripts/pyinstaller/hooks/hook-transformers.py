from PyInstaller.utils.hooks import collect_data_files, copy_metadata
datas = collect_data_files('transformers', include_py_files=True, includes=['**/*.py'])
datas += copy_metadata('transformers')

#hiddenimports = ['filelock']
