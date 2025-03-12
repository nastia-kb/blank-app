#!/bin/bash

pip install --upgrade pip setuptools wheel
git clone https://github.com/explosion/spaCy
cd spaCy
pip install -r requirements.txt
pip install --no-build-isolation --editable .
python -m spacy download ru_core_news_lg
