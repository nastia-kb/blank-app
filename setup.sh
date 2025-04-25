#!/bin/bash

python -m venv venv
source venv/bin/activate

# Install base requirements
ACCEPT_EULA=Y  pip install --upgrade pip setuptools wheel
ACCEPT_EULA=Y  pip install -r requirements.txt

# Install spaCy from source
git clone https://github.com/explosion/spaCy
cd spaCy
ACCEPT_EULA=Y  pip install -r requirements.txt
ACCEPT_EULA=Y pip install --no-build-isolation --editable .

# Download Russian model
python -m spacy download ru_core_news_lg
