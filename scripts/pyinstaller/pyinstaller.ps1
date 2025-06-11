$transformersPath = python -c "import transformers; print(transformers.__path__[0])"
$sitePackages = python -c "import site; print(site.getsitepackages()[0])"
pyi-makespec --name "Google Places Enricher 2.0" `
  --paths "$sitePackages" `
  --add-data "../../google_places_enricher_2_0/static:static" `
  --add-data "../../google_places_enricher_2_0/templates:templates" `
  --add-data "../../google_places_enricher_2_0/uploads:uploads" `
  --hidden-import=transformers `
  --hidden-import=transformers.models `
  --hidden-import=filelock `
  --hidden-import=safetensors `
  --hidden-import=yaml `
  --hidden-import=sentence_transformers `
  --hidden-import=tqdm `
  --additional-hooks-dir=./hooks `
  --console ../../google_places_enricher_2_0/main.py
  #--windowed ../../google_places_enricher_2_0/main.py
  #--add-data "$transformersPath/models;transformers/models" `

  #--add-data "../../src/config.json:config.json" `
  # --add-data "../../static/data:static/data" `
  # --add-data "../../requirements.txt:requirements.txt" `
  # --add-data "../../pyproject.toml:pyproject.toml" `
  # --add-data "../../src/.flaskenv:.flaskenv" `

pyinstaller "Google Places Enricher 2.0.spec"
