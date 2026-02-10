#!/bin/bash
pip install -r requirements.txt --quiet
exec streamlit run app.py --server.port 5000 --server.address 0.0.0.0
