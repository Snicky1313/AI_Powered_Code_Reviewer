#!/bin/bash
# Complete setup script for AI Code Reviewer with virtual environment

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   AI Code Reviewer - Complete Setup Script                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Check Python version
echo "📋 Step 1: Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "❌ Error: Python not found. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "   ✓ Found Python $PYTHON_VERSION"
echo ""

# Step 2: Create virtual environment
echo "📦 Step 2: Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "   ℹ Virtual environment already exists"
else
    $PYTHON_CMD -m venv .venv
    echo "   ✓ Virtual environment created"
fi
echo ""

# Step 3: Activate virtual environment
echo "🔧 Step 3: Activating virtual environment..."
source .venv/bin/activate
echo "   ✓ Virtual environment activated"
echo ""

# Step 4: Upgrade pip
echo "⬆️  Step 4: Upgrading pip..."
pip install --upgrade pip --quiet
echo "   ✓ pip upgraded"
echo ""

# Step 5: Install dependencies
echo "📚 Step 5: Installing dependencies..."
echo "   This may take a few minutes..."
pip install -r requirements.txt --quiet
echo "   ✓ All dependencies installed"
echo ""

# Step 6: Check for .env file
echo "🔐 Step 6: Configuring environment variables..."
if [ -f ".env" ]; then
    echo "   ✓ .env file already exists"
else
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "   ✓ Created .env file from template"
        echo ""
        echo "   ⚠️  IMPORTANT: You need to add your OpenAI API key!"
        echo ""
        echo "   Edit .env and replace 'your-openai-api-key-here' with your actual key."
        echo "   Get your API key from: https://platform.openai.com/api-keys"
        echo ""
        read -p "   Press Enter after you've added your API key to .env... " -r
    else
        echo "   ⚠️  Warning: .env.example not found"
        echo ""
        echo "   Please create a .env file manually with:"
        echo "   OPENAI_API_KEY=your-api-key-here"
        echo ""
        exit 1
    fi
fi
echo ""

# Step 7: Load environment variables
echo "🔄 Step 7: Loading environment variables..."
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
    echo "   ✓ Environment variables loaded"
else
    echo "   ⚠️  Warning: .env file not found"
fi
echo ""

# Step 8: Verify setup
echo "✅ Step 8: Verifying setup..."

# Check OpenAI library
if $PYTHON_CMD -c "import openai" 2>/dev/null; then
    OPENAI_VERSION=$($PYTHON_CMD -c "import openai; print(openai.__version__)")
    echo "   ✓ OpenAI library installed (version $OPENAI_VERSION)"
else
    echo "   ❌ OpenAI library not installed"
    exit 1
fi

# Check Flask
if $PYTHON_CMD -c "import flask" 2>/dev/null; then
    echo "   ✓ Flask installed"
else
    echo "   ❌ Flask not installed"
    exit 1
fi

# Check FastAPI
if $PYTHON_CMD -c "import fastapi" 2>/dev/null; then
    echo "   ✓ FastAPI installed"
else
    echo "   ❌ FastAPI not installed"
    exit 1
fi

# Check API key
if [ -n "$OPENAI_API_KEY" ] && [ "$OPENAI_API_KEY" != "your-openai-api-key-here" ]; then
    echo "   ✓ OpenAI API key configured"
    API_KEY_SET=true
else
    echo "   ⚠️  OpenAI API key not configured"
    API_KEY_SET=false
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   ✅ Setup Complete!                                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Step 9: Show next steps
echo "📝 Next Steps:"
echo ""
echo "1️⃣  Activate the virtual environment (in new terminals):"
echo "   source .venv/bin/activate"
echo ""
echo "2️⃣  Start the LLM Feedback Service:"
echo "   ./start_llm_service.sh"
echo ""
echo "3️⃣  Run tests:"
echo "   python test_llm_service.py"
echo ""
echo "4️⃣  Start the API Gateway (in another terminal):"
echo "   python main.py"
echo ""

if [ "$API_KEY_SET" = false ]; then
    echo "⚠️  REMINDER: Don't forget to set your OpenAI API key in .env"
    echo ""
fi

echo "💡 Tip: To deactivate the virtual environment later, just type: deactivate"
echo ""
echo "📚 For more information, see SETUP_GUIDE.md"
echo ""

