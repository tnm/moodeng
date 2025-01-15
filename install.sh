#!/bin/bash
set -e

echo "🦛 Installing Moo Deng Monitor..."

# Try to find Python 3.12
if command -v python3.12 &> /dev/null; then
    PYTHON="python3.12"
elif command -v python3 &> /dev/null && python3 -c 'import sys; exit(0 if sys.version_info.minor == 12 else 1)' &> /dev/null; then
    PYTHON="python3"
else
    echo "❌ Python 3.12 required but not found"
    echo "💡 Tip: Use pyenv to install Python 3.12:"
    echo "   brew install pyenv"
    echo "   pyenv install 3.12"
    echo "   pyenv global 3.12"
    exit 1
fi

echo "✨ Using $($PYTHON --version)"

# Version check that ensures compatibility with PyTorch
PYTHON_VERSION_CHECK=$($PYTHON -c '
import sys
v = sys.version_info
compatible = v.major == 3 and v.minor == 12
print(compatible)
print(f"{v.major}.{v.minor}")
')
COMPATIBLE=$(echo "$PYTHON_VERSION_CHECK" | head -n1)
VERSION=$(echo "$PYTHON_VERSION_CHECK" | tail -n1)

if [ "$COMPATIBLE" != "True" ]; then
    echo "❌ Python 3.12 required (you have $VERSION)"
    echo "💡 Tip: Use pyenv to install Python 3.12:"
    echo "   brew install pyenv"
    echo "   pyenv install 3.12"
    echo "   pyenv global 3.12"
    exit 1
fi

# Install uv
echo "📦 Installing uv package manager..."
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH for this session
export PATH="$HOME/.cargo/bin:$PATH"

# Create virtual environment
echo "🌱 Creating virtual environment..."
~/.cargo/bin/uv venv

# Install from current directory
echo "🔧 Installing moodeng and dependencies..."
~/.cargo/bin/uv pip install -e .

# Test the installation by activating venv first
echo "✨ Testing installation..."
source .venv/bin/activate
if python -m moodeng --version &> /dev/null; then
    echo "✅ Moo Deng Monitor installed successfully!"
    echo ""
    echo "🚀 To start monitoring:"
    echo "   source .venv/bin/activate"
    echo "   moodeng"
    echo ""
    echo "📖 For more options:"
    echo "   moodeng --help"
else
    echo "❌ Installation test failed. Please try again or report the issue."
    exit 1
fi

echo ""
echo "💡 Don't forget to activate the virtual environment:"
echo "   source .venv/bin/activate" 