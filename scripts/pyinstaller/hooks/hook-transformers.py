# Centralized PyInstaller hook for transformers and all its key dependencies.
# This collects data files and metadata for:
#   - transformers
#   - filelock
#   - safetensors
#   - yaml/pyyaml
#   - tqdm (and setuptools metadata)
#   - regex (metadata only)
#   - requests
#   - packaging
#   - tokenizers
#   - huggingface_hub
#   - fsspec
#   - charset_normalizer
#   - idna
#   - urllib3
#   - certifi
#   - colorama
#   - typing_extensions
#   - numpy
#
#
# This replaces the need for separate hook files for each dependency.
# If you add new dependencies to transformers, add them here.

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

# Dependencies from pipdeptree for transformers:

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



# Optionally, document hidden imports for reference or activation if needed:
# hiddenimports = [
#     'filelock', 'safetensors', 'yaml', 'tqdm', 'regex', 'requests', 'packaging'
# ]
