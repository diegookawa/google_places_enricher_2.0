# Google Places Enricher 2.0

A new version of the existing Google Places Enricher using Flask to build a user interface.

## Setup Instructions

### 1. Prerequisites
- Python 3.11+ must be installed.
- [Anaconda](https://www.anaconda.com/products/distribution) or [Miniconda](https://docs.anaconda.com/free/miniconda/) recommended, but you may also use Python venv or Poetry.

### 2. Clone the Repository
```sh
git clone https://github.com/diegookawa/google_places_enricher_2.0
cd google_places_enricher_2.0
```

### 3. Environment Setup (Choose One Method)

#### A. Using Anaconda/Miniconda (Recommended)
```sh
conda create -n google-places-enricher python=3.11 -y
conda activate google-places-enricher
```
Install dependencies:
```sh
pip install -r requirements.txt
```
Or, if you have poetry installed:
```sh
poetry install
```

#### B. Using Poetry for Environment Management
Install Poetry:
```sh
curl -sSL https://install.python-poetry.org | python3 -
```
Configure Poetry to use a specific Python version:
```sh
poetry env use python3.11
```
(Optional) Create the virtualenv in the project directory:
```sh
poetry config settings.virtualenvs.in-project true
```
Install dependencies:
```sh
poetry install
```

#### C. Using Python Virtual Environments (venv)
```sh
python -m venv google-places-enricher-env
# On Unix/macOS:
source google-places-enricher-env/bin/activate
# On Windows:
google-places-enricher-env\Scripts\activate
```
Install dependencies as above.

__References:__
- [Conda User Guide: Getting Started](https://docs.conda.io/projects/conda/en/stable/user-guide/getting-started.html)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Python venv Documentation](https://docs.python.org/3/library/venv.html)



## Usage Instructions
1. With your python environment activated, run:
   ```sh
   python src/app.py --port 5000
   ```
   The app will be available at [http://127.0.0.1:5000](http://127.0.0.1:5000).

