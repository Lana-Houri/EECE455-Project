#!/bin/bash

# Azure App Service startup script for Streamlit
# This script ensures Streamlit runs correctly on Azure

# Install dependencies
pip install -r requirements.txt

# Run Streamlit
# --server.port: Use the port Azure provides
# --server.address: Bind to all interfaces
# --server.headless: Run in headless mode (no browser)
# --server.enableCORS: Enable CORS for Azure
# --server.enableXsrfProtection: Enable XSRF protection

streamlit run app.py \
    --server.port=8000 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false

