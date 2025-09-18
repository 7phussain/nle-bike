#!/bin/bash

# ElectroRide Pro - Pre-deployment Check
# Author: MiniMax Agent

echo "🔍 NLE Bike - Pre-deployment Check"
echo "========================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check counter
checks_passed=0
total_checks=0

check_file() {
    total_checks=$((total_checks + 1))
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅ $1${NC}"
        checks_passed=$((checks_passed + 1))
    else
        echo -e "${RED}❌ $1 (missing)${NC}"
    fi
}

check_directory() {
    total_checks=$((total_checks + 1))
    if [ -d "$1" ]; then
        echo -e "${GREEN}✅ $1/${NC}"
        checks_passed=$((checks_passed + 1))
    else
        echo -e "${RED}❌ $1/ (missing)${NC}"
    fi
}

echo "📁 Checking core files..."
check_file "index.html"
check_file "backend/api_server.py"
check_file "backend/inventory_manager.py"
check_file "backend/requirements.txt"
check_file "package.json"
check_file "README.md"

echo ""
echo "📂 Checking directories..."
check_directory "css"
check_directory "js"
check_directory "admin"
check_directory "backend"

echo ""
echo "🚀 Checking deployment files..."
check_file "Dockerfile"
check_file "docker-compose.yml"
check_file "Procfile"
check_file "vercel.json"
check_file "railway.toml"
check_file "deploy-production.sh"
check_file "DEPLOYMENT.md"

echo ""
echo "⚙️  Checking configuration files..."
check_file "nginx.conf"
check_file ".github/workflows/deploy.yml"
check_file ".platform/application.yml"

# Check Python requirements
echo ""
echo "🐍 Checking Python requirements..."
total_checks=$((total_checks + 1))
if python3 -c "import fastapi, uvicorn, requests, beautifulsoup4" 2>/dev/null; then
    echo -e "${GREEN}✅ Python dependencies available${NC}"
    checks_passed=$((checks_passed + 1))
else
    echo -e "${YELLOW}⚠️  Python dependencies need installation${NC}"
    echo "   Run: pip install -r backend/requirements.txt"
fi

# Check if git is initialized
echo ""
echo "📝 Checking Git repository..."
total_checks=$((total_checks + 1))
if [ -d ".git" ]; then
    echo -e "${GREEN}✅ Git repository initialized${NC}"
    checks_passed=$((checks_passed + 1))
else
    echo -e "${YELLOW}⚠️  Git repository not initialized${NC}"
    echo "   Run: git init && git add . && git commit -m 'Initial commit'"
fi

# Check environment setup
echo ""
echo "🌍 Checking environment..."
total_checks=$((total_checks + 1))
if [ -f ".env" ] || [ -f ".env.example" ]; then
    echo -e "${GREEN}✅ Environment configuration available${NC}"
    checks_passed=$((checks_passed + 1))
else
    echo -e "${YELLOW}⚠️  Environment configuration recommended${NC}"
fi

# Summary
echo ""
echo "📊 Deployment Readiness Summary"
echo "==============================="
echo -e "Checks passed: ${GREEN}$checks_passed${NC}/$total_checks"

percentage=$((checks_passed * 100 / total_checks))

if [ $percentage -ge 90 ]; then
    echo -e "${GREEN}🎉 Excellent! Your project is ready for deployment.${NC}"
    echo ""
    echo "🚀 Next steps:"
    echo "1. Run: chmod +x deploy.sh"
    echo "2. Run: ./deploy.sh"
    echo "3. Follow the deployment wizard"
elif [ $percentage -ge 70 ]; then
    echo -e "${YELLOW}⚠️  Good! Minor issues found, but deployment should work.${NC}"
    echo ""
    echo "📋 Recommended actions:"
    echo "1. Fix any missing files shown above"
    echo "2. Run: chmod +x deploy.sh && ./deploy.sh"
else
    echo -e "${RED}❌ Issues found. Please fix before deploying.${NC}"
    echo ""
    echo "🛠️  Required actions:"
    echo "1. Ensure all core files are present"
    echo "2. Install Python dependencies"
    echo "3. Initialize Git repository"
    echo "4. Re-run this check"
fi

echo ""
echo "📚 For detailed deployment instructions, read: DEPLOYMENT.md"
echo "🆘 Need help? Check the troubleshooting section in DEPLOYMENT.md"
