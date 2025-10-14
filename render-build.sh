#!/usr/bin/env bash
echo "Installing Python 3.10..."
pyenv install 3.10.14 -s
pyenv global 3.10.14
python --version

echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt
