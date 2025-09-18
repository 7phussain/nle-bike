# 🚀 NLE Bike Deployment Guide

## Deploy to: https://fv2waba4q5qf.space.minimax.io/

### 📋 **Pre-Deployment Checklist**

#### **Files Included in This Package:**
- ✅ `index.html` - Main homepage
- ✅ `css/` - All stylesheets (including mega-menu.css)
- ✅ `js/` - JavaScript files
- ✅ `admin/` - Admin dashboard
- ✅ `backend/` - Python API server
- ✅ `data/` - Database files
- ✅ `package.json` - Dependencies
- ✅ `Procfile` - Deployment configuration
- ✅ `vercel.json` - Vercel deployment config

---

## 🎯 **Deployment Methods**

### **Method 1: MiniMax Platform Deployment**

1. **Access MiniMax Dashboard**
   - Log into your MiniMax account
   - Navigate to project management
   - Select the domain: `fv2waba4q5qf.space.minimax.io`

2. **Upload Project Files**
   ```bash
   # Upload all files from this deployment-package folder
   # Including subdirectories: admin/, backend/, css/, js/, data/
   ```

3. **Configure Environment**
   - Set Python version: 3.9+
   - Install dependencies from requirements.txt
   - Configure environment variables

### **Method 2: Direct File Upload**

1. **Frontend Files (Required)**
   - Upload `index.html` to root
   - Upload `css/` folder
   - Upload `js/` folder  
   - Upload `admin/` folder

2. **Backend Files (Optional but Recommended)**
   - Upload `backend/` folder
   - Set up Python environment
   - Install dependencies: `pip install -r backend/requirements.txt`

---

## ⚙️ **Configuration Steps**

### **1. Environment Variables**
```bash
# Required for full functionality
STRIPE_SECRET_KEY=your_stripe_key
STRIPE_PUBLISHABLE_KEY=your_stripe_public_key
SMTP_HOST=your_smtp_host
SMTP_USER=your_email
SMTP_PASSWORD=your_password
```

### **2. Database Setup**
```bash
# The SQLite database is included
# No additional setup required
```

### **3. Start Services**
```bash
# If backend deployment is supported:
cd backend
python api_server.py

# Frontend is static and ready to serve
```

---

## 🌐 **Domain Configuration**

### **Current Status:**
- Domain: `https://fv2waba4q5qf.space.minimax.io/`
- Currently hosting: DailyByte project
- **Action needed:** Replace with NLE Bike files

### **DNS & SSL:**
- ✅ Domain already configured
- ✅ SSL certificate active
- ✅ HTTPS enabled

---

## 🔧 **Deployment Commands**

### **Quick Deploy (Frontend Only)**
```bash
# 1. Clear current site content
# 2. Upload index.html as main page
# 3. Upload css/, js/, admin/ folders
# 4. Test: https://fv2waba4q5qf.space.minimax.io/
```

### **Full Stack Deploy**
```bash
# 1. Deploy frontend (above)
# 2. Deploy backend API
# 3. Configure environment variables
# 4. Start Python services
# 5. Test full functionality
```

---

## 🧪 **Testing Checklist**

After deployment, verify:

- [ ] Homepage loads correctly
- [ ] Navigation menu works (mega menu)
- [ ] Mobile responsiveness
- [ ] Admin panel accessible: `/admin`
- [ ] API endpoints responding (if backend deployed)
- [ ] Database connectivity
- [ ] Payment system integration

---

## 🚨 **Troubleshooting**

### **Common Issues:**

1. **Site not loading**
   - Check if index.html is in root directory
   - Verify file permissions

2. **CSS/JS not loading**
   - Ensure correct file paths in HTML
   - Check MIME types for CSS/JS files

3. **Backend API errors**
   - Verify Python environment
   - Check environment variables
   - Review server logs

---

## 📞 **Support**

If you encounter deployment issues:
1. Check MiniMax platform documentation
2. Verify all files are uploaded correctly
3. Test each component individually

**Ready to deploy! Your NLE Bike project is fully prepared for production.** 🎉