#!/bin/bash
# Egile Agent Hub - Installation Script for Unix/Linux/MacOS
# ===========================================================

set -e  # Exit on error

echo ""
echo "========================================"
echo "Installing Egile Agent Hub"
echo "========================================"
echo ""

# Install egile-agent-core
echo "[1/4] Installing egile-agent-core..."
cd ../egile-agent-core || {
    echo "ERROR: Could not find egile-agent-core directory"
    echo "Make sure it exists at: ../egile-agent-core"
    exit 1
}
pip install -e .

# Install egile-mcp-prospectfinder
echo ""
echo "[2/4] Installing egile-mcp-prospectfinder..."
cd ../egile-mcp-prospectfinder || {
    echo "ERROR: Could not find egile-mcp-prospectfinder directory"
    echo "Make sure it exists at: ../egile-mcp-prospectfinder"
    exit 1
}
pip install -e .

# Install egile-agent-prospectfinder (optional)
cd ../egile-agent-prospectfinder 2>/dev/null && pip install -e . || echo "WARNING: Skipping egile-agent-prospectfinder"

# Install egile-mcp-x-post-creator
echo ""
echo "[3/4] Installing egile-mcp-x-post-creator..."
cd ../egile-mcp-x-post-creator || {
    echo "ERROR: Could not find egile-mcp-x-post-creator directory"
    echo "Make sure it exists at: ../egile-mcp-x-post-creator"
    exit 1
}
pip install -e .

# Install egile-agent-x-twitter (optional)
cd ../egile-agent-x-twitter 2>/dev/null && pip install -e . || echo "WARNING: Skipping egile-agent-x-twitter"

# Install egile-agent-hub
echo ""
echo "[4/4] Installing egile-agent-hub..."
cd ../egile-agent-hub
pip install -e ".[all]"

# Copy .env.example to .env if not exists
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo ""
    echo "========================================"
    echo "IMPORTANT: Configure your .env file!"
    echo "========================================"
    echo ""
    echo "Edit .env and set:"
    echo "  - At least one AI model API key (MISTRAL_API_KEY, XAI_API_KEY, or OPENAI_API_KEY)"
    echo "  - Google API credentials (if using ProspectFinder)"
    echo "  - X/Twitter API credentials (if using XTwitter)"
    echo ""
fi

# Create empty agents.yaml if not exists
if [ ! -f agents.yaml ]; then
    echo "Creating agents.yaml from agents.yaml.example..."
    cp agents.yaml.example agents.yaml
    echo ""
    echo "========================================"
    echo "CONFIGURE YOUR AGENTS!"
    echo "========================================"
    echo ""
    echo "Edit agents.yaml to define your agents and teams."
    echo "See agents.yaml.example for documentation."
    echo ""
fi

echo ""
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. Edit agents.yaml to define your agents"
echo "  3. Run: agent-hub"
echo ""
