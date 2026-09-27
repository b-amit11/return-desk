#!/bin/zsh
cd "$(dirname "$0")"
if [[ -x .venv/bin/python ]]; then
  .venv/bin/python -m streamlit run app.py --server.port 8504
elif [[ -x ../../work/ola-venv/bin/python ]]; then
  ../../work/ola-venv/bin/python -m streamlit run app.py --server.port 8504
else
  echo "Create the Python environment using README.md first."
  read
fi
