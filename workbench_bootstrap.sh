#!/bin/bash

set -eu

tee "${SUPERVISOR_CONFD}/debug_server.conf" >/dev/null <<EOF
[program:debug_server]
directory=%(ENV_PROJECT_ROOT)s
command=python3 scripts/debug_server.py
autostart=true
autorestart=unexpected
stopasgroup=true
environment=
  PATH="%(ENV_PATH)s",
  PYTHONPATH="%(ENV_PYTHONPATH)s",
  DEBUG_SERVER_PORT="%(ENV_DEBUG_SERVER_PORT)s"
EOF
