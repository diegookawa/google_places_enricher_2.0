# Exports Poetry dependencies to requirements.txt for pip install

# Warning: poetry-plugin-export will not be installed by default in a future version of Poetry.
# In order to avoid a breaking change and make your automation forward-compatible, please install poetry-plugin-export explicitly. See https://python-poetry.org/docs/plugins/#using-plugins for details on how to install a plugin.
# To disable this warning run 'poetry config warnings.export false'.
# pipx inject poetry poetry-plugin-export
poetry export --format=requirements.txt --output=requirements.txt --without-hashes
Write-Host "requirements.txt generated at project root."
