#!/usr/bin/env bash
set -e

if [[ $(hash python3) == false || $(hash virtualenv) == false || $(hash pip3) == false ]]; then
    echo >&2 "missing requirements: python3, virtualenv, pip3"
    exit
fi

if [[ $(type deactivate) == true ]]; then
    echo "disable current venv"
    deactivate
fi

if [ ! -d venv ]; then
    echo "create new venv"
    virtualenv venv
fi

echo "activate venv"
source venv/bin/activate

if [ -f requirements.txt ]; then
    echo "install requirements"
    pip3 install -r requirements.txt
fi
