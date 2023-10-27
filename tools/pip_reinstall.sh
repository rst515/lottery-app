#!/bin/bash

pip install --upgrade pip
pip freeze | xargs pip uninstall -y
pip cache purge
pip install -r requirements.txt