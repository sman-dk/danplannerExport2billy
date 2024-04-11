#!/bin/bash
# Wrapper script for danplannerExport2billy.py
#
# For ease of use you can add the following line to e.g. .bashrc (adjust accordingly to the shell you use)
# alias dp2billy="~/github/danplannerExport2billy/dp2billy.sh"
#

cd ~/github/danplannerExport2billy
source venv/bin/activate
python3 danplannerExport2billy.py $@
deactivate
