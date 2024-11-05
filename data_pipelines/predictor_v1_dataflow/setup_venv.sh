#!/bin/bash
set -e

pip3 install --user virtualenv
python3 -m venv venv
source venv/bin/activate
pip3 install --upgrade pip
pip3 install -r requirements.txt
pip3 install tox pytest google-api-python-client
