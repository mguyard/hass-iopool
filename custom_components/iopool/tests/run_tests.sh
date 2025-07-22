#!/bin/bash
cd /workspaces/home-assistant-dev/config
PYTHONPATH=/workspaces/home-assistant-dev python -m pytest custom_components/iopool/tests/ "$@"
