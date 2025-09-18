#!/bin/bash

# NLE Bike - Interactive Deployment Script
# Author: MiniMax Agent

echo "🚀 NLE Bike - Deployment Wizard"
echo "======================================"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "⚙️  Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial NLE Bike commit"
    echo "✅ Git repository initialized"
    echo ""
fi

echo "Choose your deployment platform:"
echo "1) 🟢 Heroku (Easiest - Recommended for beginners)"
echo "2) 🌊 DigitalOcean App Platform (Best value)"
echo "3) 🐳 Docker + Docker Hub (Most flexible)"
echo "4) ⚡ Railway (Modern platform)"
echo "5) 🌐 Vercel (Frontend-focused)"
echo "6) 🏢 Traditional VPS/Server (Full control)"
echo "7) 📖 Show detailed comparison"
echo ""

read -p "Enter your choice (1-7): " choice

case $choice in
    1)
        echo ""
        echo "🟢 Deploying to Heroku..."
        echo "========================"
        echo ""
        
        # Check if Heroku CLI is installed
        if ! command -v heroku &> /dev/null; then
            echo "❌ Heroku CLI not found."
            echo "📥 Please install it from: https://devcenter.heroku.com/articles/heroku-cli"
            echo "Or run: brew install heroku/brew/heroku (macOS)"
            exit 1
        fi
        
        echo "1. Login to Heroku (browser will open):"
        heroku login
        
        echo ""
        read -p "2. Enter your app name (e.g., nlebike-yourname): " app_name
        
        echo "3. Creating Heroku app..."
        heroku create $app_name
        
        echo "4. Setting environment variables..."
        heroku config:set DEBUG=false --app $app_name
        heroku config:set DATABASE_PATH=/app/data/inventory.db --app $app_name
        heroku config:set API_HOST=0.0.0.0 --app $app_name
        heroku config:set API_PORT=80 --app $app_name
        
        echo "5. Adding git remote..."
        git remote add heroku https://git.heroku.com/$app_name.git
        
        echo "6. Deploying to Heroku..."
        git push heroku main
        
        echo ""
        echo "🎉 Deployment complete!"
        echo "🌐 Your site: https://$app_name.herokuapp.com"
        echo "👥 Admin panel: https://$app_name.herokuapp.com/admin/"
        echo "📚 API docs: https://$app_name.herokuapp.com/docs"
        ;;
        
    2)
        echo ""
        echo "🌊 Deploying to DigitalOcean..."
        echo "==============================="
        echo ""
        
        if [ -f "deploy-digitalocean.sh" ]; then
            chmod +x deploy-digitalocean.sh
            ./deploy-digitalocean.sh
        else
            echo "❌ DigitalOcean deployment script not found."
            echo "📝 Please check the deploy-digitalocean.sh file exists."
        fi
        ;;
        
    3)
        echo ""
        echo "🐳 Docker Deployment..."
        echo "======================="
        echo ""
        
        # Check if Docker is installed
        if ! command -v docker &> /dev/null; then
            echo "❌ Docker not found."
            echo "📥 Please install Docker from: https://docker.com/get-started"
            exit 1
        fi
        
        read -p "Enter your Docker Hub username: " docker_username
        
        echo "1. Building Docker image..."
        docker build -t $docker_username/nlebike:latest .
        
        echo "2. Login to Docker Hub..."
        docker login
        
        echo "3. Pushing to Docker Hub..."
        docker push $docker_username/nlebike:latest
        
        echo "4. Starting local deployment..."
        docker-compose up -d
        
        echo ""
        echo "🎉 Deployment complete!"
        echo "🌐 Local site: http://localhost"
        echo "👥 Admin panel: http://localhost/admin/"
        echo "🐳 Docker image: $docker_username/nlebike:latest"
        ;;
        
    4)
        echo ""
        echo "⚡ Railway Deployment..."
        echo "======================"
        echo ""
        echo "1. Go to https://railway.app"
        echo "2. Sign up with GitHub"
        echo "3. Click 'Deploy from GitHub'"
        echo "4. Select this repository"
        echo "5. Railway will auto-deploy!"
        echo ""
        echo "💡 Your railway.toml configuration is ready!"
        ;;
        
    5)
        echo ""
        echo "🌐 Vercel Deployment..."
        echo "====================="
        echo ""
        
        if ! command -v vercel &> /dev/null; then
            echo "Installing Vercel CLI..."
            npm install -g vercel
        fi
        
        echo "Deploying to Vercel..."
        vercel --prod
        ;;
        
    6)
        echo ""
        echo "🏢 VPS/Server Deployment..."
        echo "=========================="
        echo ""
        
        if [ -f "deploy-production.sh" ]; then
            echo "⚠️  This will install and configure services on your server."
            read -p "Are you sure? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                chmod +x deploy-production.sh
                sudo ./deploy-production.sh
            fi
        else
            echo "❌ Production deployment script not found."
        fi
        ;;
        
    7)
        echo ""
        cat DEPLOYMENT.md
        ;;
        
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "📚 For detailed documentation, read: DEPLOYMENT.md"
echo "🆘 Need help? Check the troubleshooting section"
echo ""
echo "🎉 Happy dropshipping with NLE Bike! 🚀"
