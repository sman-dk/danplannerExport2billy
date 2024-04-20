#!/bin/bash
# Wrapper script for danplannerExport2billy.py
#
# For ease of use you can add the following line to e.g. .bashrc (adjust accordingly to the shell you use)
# alias dp2billy="~/github/danplannerExport2billy/dp2billy.sh"
#

source ~/github/danplannerExport2billy/venv/bin/activate
python3 ~/github/danplannerExport2billy/danplannerExport2billy.py -f $@
deactivate
