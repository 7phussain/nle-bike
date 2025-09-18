# ElectroRide Pro - Heroku Deployment
# Author: MiniMax Agent

web: python -m uvicorn backend.api_server:app --host 0.0.0.0 --port $PORT
worker: python backend/inventory_manager.py
