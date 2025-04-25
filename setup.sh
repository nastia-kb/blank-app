#!/bin/bash

python -m venv venv
source venv/bin/activate

pip install --upgrade pip setuptools wheel

# Try regular spaCy install first
pip install -r requirements.txt
pip install spacy

# Download Russian model
python -m spacy download ru_core_news_lg
