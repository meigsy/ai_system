set -e

pip3 install virtualenv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r ./src/requirements.txt
pip install pytest~