#!/bin/bash

# ElectroRide Pro - DigitalOcean App Platform Deployment
# Author: MiniMax Agent

echo "🚀 Deploying to DigitalOcean App Platform..."

# Install doctl CLI if not present
if ! command -v doctl &> /dev/null; then
    echo "Installing DigitalOcean CLI..."
    cd /tmp
    wget https://github.com/digitalocean/doctl/releases/download/v1.98.1/doctl-1.98.1-linux-amd64.tar.gz
    tar xf doctl-1.98.1-linux-amd64.tar.gz
    sudo mv doctl /usr/local/bin
    rm doctl-1.98.1-linux-amd64.tar.gz
fi

# Authenticate (you'll need to get your token from DigitalOcean)
echo "Please get your API token from: https://cloud.digitalocean.com/account/api/tokens"
read -p "Enter your DigitalOcean API token: " DO_TOKEN
doctl auth init --access-token $DO_TOKEN

# Create app spec
cat > .do/app.yaml <<EOF
name: electroride-pro
services:
- name: web
  source_dir: /
  github:
    repo: your-username/electroride-pro
    branch: main
    deploy_on_push: true
  run_command: python -m uvicorn backend.api_server:app --host 0.0.0.0 --port \$PORT
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  http_port: 8000
  env:
  - key: DATABASE_PATH
    value: /app/data/inventory.db
  - key: DEBUG
    value: "false"
- name: worker
  source_dir: /
  github:
    repo: your-username/electroride-pro
    branch: main
  run_command: python backend/inventory_manager.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  env:
  - key: DATABASE_PATH
    value: /app/data/inventory.db
databases:
- engine: PG
  name: electroride-db
  num_nodes: 1
  size: db-s-dev-database
  version: "13"
static_sites:
- name: frontend
  source_dir: /
  index_document: index.html
  error_document: index.html
  routes:
  - path: /admin
  - path: /static
EOF

# Deploy the app
echo "📦 Creating DigitalOcean App..."
doctl apps create .do/app.yaml

echo "✅ Deployment initiated! Check your DigitalOcean dashboard for progress."
echo "🌍 Your app will be available at: https://electroride-pro-[hash].ondigitalocean.app"
