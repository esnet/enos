#! /bin/sh
#
# Helper script for multi-point VPN mininet configuration and startup.
# Invoke this as root to start things up and get a mininet
# command-line prompt.
#
export PYTHONPATH=${PWD}
python mininet/run.py ${*}

