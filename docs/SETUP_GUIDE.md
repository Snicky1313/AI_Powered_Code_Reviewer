# Setup Guide - Virtual Environment and Configuration

## 🐍 Virtual Environment Setup

### Why Use a Virtual Environment?
- Isolates project dependencies
- Prevents conflicts with system Python packages
- Makes the project portable and reproducible
- Required for clean testing

---

## 📦 Step-by-Step Setup

### Step 1: Create Virtual Environment

**On Linux/Mac:**
```bash
cd /home/yogo/AI_Code_Reviewer-main

# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate
```

**On Windows:**
```bash
cd C:\path\to\AI_Code_Reviewer-main

# Create virtual environment
python -m venv .venv

# Activate it (PowerShell)
.venv\Scripts\Activate.ps1

# Or (Command Prompt)
.venv\Scripts\activate.bat
```

### Step 2: Install Dependencies

Once activated (you'll see `(.venv)` in your prompt):

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Create your `.env` file (see next section)

### Step 4: Verify Installation

```bash
# Check Python version
python --version

# Check installed packages
pip list

# Test the services
python test_llm_service.py
```

---

## 🔐 Environment Variables Configuration

### Create .env File

```bash
# Copy the example file
cp .env.example .env

# Edit with your actual values
nano .env
# or
vim .env
# or open in your editor
```

### .env File Contents

Add your actual API keys and configuration:

```bash
# ============================================
# OpenAI Configuration (REQUIRED for Task 1.7)
# ============================================
# Get your key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-actual-api-key-here

# ============================================
# Database Configuration (for Logging Service)
# ============================================
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=code_reviewer_logs
DATABASE_USER=logging_service_user
DATABASE_PASSWORD=your-secure-password-here

# ============================================
# Application Configuration
# ============================================
LOG_LEVEL=INFO
ENVIRONMENT=development

# ============================================
# Service Ports
# ============================================
API_GATEWAY_PORT=8000
PRODUCER_PORT=8001
STYLE_ANALYZER_PORT=5002
LLM_FEEDBACK_PORT=5003
```

### Load Environment Variables

**Option 1: Export manually (temporary - current session only)**
```bash
export OPENAI_API_KEY='your-api-key-here'
```

**Option 2: Use python-dotenv (recommended)**

The services are already configured to use python-dotenv if available:

```bash
# Install python-dotenv (already in requirements.txt)
pip install python-dotenv

# It will automatically load from .env file
```

**Option 3: Source from .env file (Linux/Mac)**
```bash
# Create a script to load variables
set -a
source .env
set +a
```

---

## 🧪 Testing with Virtual Environment

### Run Tests

```bash
# Make sure virtual environment is activated
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\Activate.ps1  # Windows

# Set your API key (if not using .env file)
export OPENAI_API_KEY='your-key'  # Linux/Mac
# or
$env:OPENAI_API_KEY='your-key'  # Windows PowerShell

# Run tests
python test_llm_service.py
```

### Run Individual Services

```bash
# Terminal 1: API Gateway
python main.py

# Terminal 2: LLM Feedback Service
python ai_code_reviewer.analyzers.llm_feedback.py

# Terminal 3: Style Analyzer
python ai_code_reviewer.analyzers.staticA.py
```

---

## 🔄 Deactivating Virtual Environment

When you're done:

```bash
deactivate
```

---

## 📝 .gitignore Configuration

Make sure these are in your `.gitignore`:

```
# Virtual Environment
.venv/
venv/
env/
ENV/

# Environment Variables
.env
.env.local

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg-info/
dist/
build/
```

---

## ✅ Verification Checklist

Run these commands to verify everything is set up correctly:

```bash
# 1. Check virtual environment is activated
which python  # Should show path in .venv
# or
where python  # Windows

# 2. Check Python version
python --version  # Should be 3.8+

# 3. Check packages are installed
pip list | grep -E "(openai|flask|fastapi)"

# 4. Check environment variables
python -c "import os; print('API Key set:', bool(os.getenv('OPENAI_API_KEY')))"

# 5. Test import
python -c "import openai; print('OpenAI library version:', openai.__version__)"

# 6. Run health checks
python -c "import requests; print(requests.get('http://localhost:5003/health').json())"
```

---

## 🚀 Quick Start Script

Here's a complete setup script:

```bash
#!/bin/bash
# setup_and_test.sh - Complete setup and test script

echo "Setting up AI Code Reviewer..."

# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your OPENAI_API_KEY"
    echo "   Get your key from: https://platform.openai.com/api-keys"
    echo ""
    read -p "Press Enter after you've added your API key to .env..."
fi

# Load environment variables
set -a
source .env
set +a

# Verify setup
echo ""
echo "Verifying setup..."
python -c "import os; assert os.getenv('OPENAI_API_KEY'), 'API key not set!'; print('✓ API key configured')"
python -c "import openai; print('✓ OpenAI library installed')"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Start LLM service: ./start_llm_service.sh"
echo "2. Run tests: python test_llm_service.py"
```

---

## 💡 Tips

### For Development
- Always activate the virtual environment before working
- Use `pip freeze > requirements.txt` to save new dependencies
- Keep your `.env` file secret (never commit it to git)

### For Production
- Use environment variables instead of .env file
- Consider using secrets management (AWS Secrets Manager, etc.)
- Set up proper logging and monitoring

### For Testing
- Create a `.env.test` file with test credentials
- Use mock API keys for unit tests
- Consider using `pytest` for more advanced testing

---

## 🐛 Troubleshooting

### "python not found"
```bash
# Try python3 instead
python3 -m venv .venv
```

### "pip not found"
```bash
# Install pip
sudo apt-get install python3-pip  # Linux
# or
python -m ensurepip  # Windows
```

### "Permission denied"
```bash
# Make scripts executable
chmod +x start_llm_service.sh
chmod +x setup_and_test.sh
```

### ".env not loaded"
```bash
# Install python-dotenv
pip install python-dotenv

# Or export manually
export OPENAI_API_KEY='your-key'
```

### "Module not found"
```bash
# Make sure venv is activated
source .venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt
```

---

## 📚 Additional Resources

- **Virtual Environments**: https://docs.python.org/3/library/venv.html
- **pip Documentation**: https://pip.pypa.io/
- **python-dotenv**: https://github.com/theskumar/python-dotenv
- **OpenAI API**: https://platform.openai.com/docs

---

**Need Help?** Check the main README.md or TASK_1_7_IMPLEMENTATION.md for more details.

