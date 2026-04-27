#!/bin/bash
# Start script for Render.com
# Wait for the server to initialise
sleep 5
# Run the Flask app
# Render.com sets the PORT environment variable
python app.py
