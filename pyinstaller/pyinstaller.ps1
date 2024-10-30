pyi-makespec --name "Google Places Enricher 2.0" --add-data "../src/static:static" --add-data "../src/templates:templates" --windowed ../src/main.py

pyinstaller "Google Places Enricher 2.0.spec"