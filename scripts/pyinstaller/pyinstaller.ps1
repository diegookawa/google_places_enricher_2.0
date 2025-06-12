#$transformersPath = python -c "import transformers; print(transformers.__path__[0])"
#$sitePackages = python -c "import site; print(site.getsitepackages()[0])"
  #--paths "$sitePackages" `
pyi-makespec --name "Google Places Enricher 2.0" `
  --add-data "../../google_places_enricher_2_0/static:google_places_enricher_2_0/static" `
  --add-data "../../google_places_enricher_2_0/templates:google_places_enricher_2_0/templates" `
  --add-data "../../google_places_enricher_2_0/uploads:google_places_enricher_2_0/uploads" `
  --hidden-import=transformers `
  --hidden-import=transformers.models `
  --hidden-import=tokenizers `
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
  --additional-hooks-dir=./hooks `
  --windowed ../../google_places_enricher_2_0/main.py 
  # Change to --console when debugging
  
  #--add-data "$transformersPath/models;transformers/models" `

  # Optional: uncomment if used
  # --hidden-import=sentencepiece `
  # --hidden-import=protobuf `

pyinstaller "Google Places Enricher 2.0.spec"
