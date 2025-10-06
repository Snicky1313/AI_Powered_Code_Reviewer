# 🚀 Quick Start Guide

## For Absolute Beginners - Start Here!

### Step 1: Run the Automated Setup Script

```bash
./setup_and_test.sh
```

This single command will:
- ✅ Create a virtual environment
- ✅ Install all dependencies
- ✅ Create your `.env` configuration file
- ✅ Guide you through API key setup
- ✅ Verify everything works

**That's it!** The script will walk you through everything.

---

## What About the Virtual Environment and .env File?

### ✅ Virtual Environment - YES!

**Do you need it?** **YES, highly recommended!**

**Why?**
- Keeps project dependencies separate from your system
- Prevents version conflicts
- Makes the project easy to clean up
- Industry best practice

**The setup script creates it automatically for you!**

---

### ✅ .env File - YES!

**Do you have one?** **YES, we created `.env.example` for you!**

**Here's how it works:**

1. **`.env.example`** - Template file (safe to commit to git)
   ```
   ✅ This file exists now
   ✅ Contains all variable names
   ✅ Has placeholder values
   ```

2. **`.env`** - Your actual config file (you create it)
   ```
   📝 You create this from the template
   🔒 Contains your real API keys
   ⚠️  NEVER commit this to git!
   ```

**The setup script will create `.env` from the template automatically!**

---

## Manual Setup (If You Prefer)

### Step 1: Create Virtual Environment

```bash
# Create it
python3 -m venv .venv

# Activate it (Linux/Mac)
source .venv/bin/activate

# You'll see (.venv) in your prompt now
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Create Your .env File

```bash
# Copy the template
cp .env.example .env

# Edit it with your favorite editor
nano .env
# or
vim .env
# or open it in VS Code
```

### Step 4: Add Your OpenAI API Key

Edit the `.env` file and replace the placeholder:

```bash
# Change this line:
OPENAI_API_KEY=your-openai-api-key-here

# To your actual key:
OPENAI_API_KEY=sk-proj-abc123xyz789...
```

### Step 5: Test Everything

```bash
# Start the LLM service
./start_llm_service.sh

# In another terminal, activate venv and run tests
source .venv/bin/activate
python test_llm_service.py
```

---

## 🔑 Getting Your OpenAI API Key

1. Go to: https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click **"Create new secret key"**
4. Give it a name (e.g., "AI Code Reviewer")
5. Copy the key (it starts with `sk-...`)
6. Paste it into your `.env` file

**⚠️ Important:** The key is only shown once! Save it immediately.

---

## ⚙️ What's in the .env File?

Here's what the template contains:

```bash
# Required for LLM Feedback Service
OPENAI_API_KEY=your-openai-api-key-here

# Optional: Database settings (for logging service)
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=code_reviewer_logs
DATABASE_USER=logging_service_user
DATABASE_PASSWORD=your-secure-password-here

# Optional: Service ports (use defaults if not sure)
API_GATEWAY_PORT=8000
STYLE_ANALYZER_PORT=5002
LLM_FEEDBACK_PORT=5003
```

**Only `OPENAI_API_KEY` is required for Task 1.7!** The rest are optional.

---

## 🧪 Testing After Setup

### Check if everything is working:

```bash
# Activate virtual environment
source .venv/bin/activate

# Check Python is from venv
which python
# Should show: /home/yogo/AI_Code_Reviewer-main/.venv/bin/python

# Check OpenAI library
python -c "import openai; print('✓ OpenAI library:', openai.__version__)"

# Check API key is loaded
python -c "import os; print('✓ API Key configured:', bool(os.getenv('OPENAI_API_KEY')))"

# Run the full test suite
python test_llm_service.py
```

---

## 📁 Files You'll See

After setup, you'll have:

```
AI_Code_Reviewer-main/
├── .venv/                    ← Virtual environment (created by setup)
├── .env                      ← Your config file (you create this)
├── .env.example              ← Template (we created this) ✅
├── setup_and_test.sh         ← Automated setup (we created this) ✅
├── SETUP_GUIDE.md            ← Detailed guide (we created this) ✅
├── analyzers/
│   └── llm_feedback.py       ← LLM service (we created this) ✅
└── test_llm_service.py       ← Tests (we created this) ✅
```

---

## ❓ FAQ

### Q: Do I need to activate the virtual environment every time?

**A:** Yes, every time you open a new terminal. Just run:
```bash
source .venv/bin/activate
```

### Q: How do I know if the virtual environment is active?

**A:** You'll see `(.venv)` at the start of your command prompt:
```bash
(.venv) yogo@x:~/AI_Code_Reviewer-main$
```

### Q: Can I skip the virtual environment?

**A:** Not recommended! You might have dependency conflicts with your system Python packages.

### Q: Where do I get the OpenAI API key?

**A:** https://platform.openai.com/api-keys

### Q: Is the API key free?

**A:** OpenAI has a free tier with limited usage. Check their pricing: https://openai.com/pricing

### Q: What if I don't want to use .env file?

**A:** You can export the variable directly:
```bash
export OPENAI_API_KEY='your-key-here'
```
But you'll need to do this every time you open a new terminal.

### Q: Can I see the .env file in git?

**A:** No, `.env` should be in `.gitignore` (never commit secrets!). Only `.env.example` is in git.

---

## 🎯 Summary

**Easiest Way:**
```bash
./setup_and_test.sh
# Follow the prompts, add your API key when asked
```

**Manual Way:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env  # Add your API key
python test_llm_service.py
```

---

## 📚 More Information

- **Detailed Setup**: See `SETUP_GUIDE.md`
- **Task 1.7 Docs**: See `TASK_1_7_IMPLEMENTATION.md`
- **Quick Reference**: See `TASK_1_7_SUMMARY.md`
- **Main README**: See `README.md`

---

## 🆘 Need Help?

If something isn't working:

1. Check `SETUP_GUIDE.md` troubleshooting section
2. Verify virtual environment is activated
3. Verify API key is set correctly in `.env`
4. Try running `./setup_and_test.sh` again

---

**You're all set!** 🎉 Start the service and test it:

```bash
./start_llm_service.sh
```

