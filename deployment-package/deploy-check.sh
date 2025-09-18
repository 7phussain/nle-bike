#!/bin/bash

# NLE Bike Quick Deployment Script
echo "🚀 NLE Bike Deployment Package Ready!"
echo "======================================"

echo "📁 Package Contents:"
find . -type f -name "*.html" | sort
echo ""
echo "📂 Directories:"
find . -type d | grep -v __pycache__ | sort
echo ""

echo "📋 Deployment Checklist:"
echo "□ Upload index.html to root"
echo "□ Upload css/ folder"  
echo "□ Upload js/ folder"
echo "□ Upload admin/ folder"
echo "□ Upload backend/ folder (optional)"
echo "□ Configure environment variables"
echo "□ Test deployment"

echo ""
echo "🌐 Target Domain: https://fv2waba4q5qf.space.minimax.io/"
echo "📖 See DEPLOYMENT_GUIDE.md for detailed instructions"
