#!/bin/bash

python -m venv venv
source venv/bin/activate

# Install base requirements
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Install spaCy from source
git clone https://github.com/explosion/spaCy
cd spaCy
pip install -r requirements.txt
pip install --no-build-isolation --editable .

# Download Russian model
python -m spacy download ru_core_news_lg
