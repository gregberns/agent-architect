#!/bin/bash

# Script to run compiled JavaScript applications from the exe directory
# Usage: ./run-chat.sh <filename>
# Example: ./run-chat.sh EvalMbpp

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if a parameter was provided
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ Error: No file name provided${NC}"
    echo -e "${YELLOW}Usage: $0 <filename>${NC}"
    echo -e "${YELLOW}Example: $0 EvalMbpp${NC}"
    echo -e "${YELLOW}Available files in exe directory:${NC}"
    # List available .js files in the exe directory
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    EXE_DIR="${PROJECT_ROOT}/_build/default/src/agentArchitect/src/exe"
    if [ -d "$EXE_DIR" ]; then
        find "$EXE_DIR" -name "*.js" -exec basename {} .js \; 2>/dev/null | sort || echo "  (No compiled JavaScript files found)"
    else
        echo "  (Build directory not found - run 'npm run build' first)"
    fi
    exit 1
fi

# Get the filename parameter
JS_FILENAME="$1"

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHAT_JS_PATH="${PROJECT_ROOT}/_build/default/src/agentArchitect/src/exe/${JS_FILENAME}.js"

echo -e "${GREEN}🚀 Agent Architect - Application Runner${NC}"
echo "Project root: ${PROJECT_ROOT}"
echo "Target file: ${JS_FILENAME}.js"

# Check if the compiled JavaScript file exists
if [ ! -f "$CHAT_JS_PATH" ]; then
    echo -e "${RED}❌ Error: Compiled JavaScript file not found at ${CHAT_JS_PATH}${NC}"
    echo -e "${YELLOW}💡 Tip: Run 'npm run build' first to compile the ReasonML code${NC}"
    echo -e "${YELLOW}Available files in exe directory:${NC}"
    EXE_DIR="${PROJECT_ROOT}/_build/default/src/agentArchitect/src/exe"
    if [ -d "$EXE_DIR" ]; then
        find "$EXE_DIR" -name "*.js" -exec basename {} .js \; 2>/dev/null | sort || echo "  (No compiled JavaScript files found)"
    else
        echo "  (Build directory not found)"
    fi
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Error: Node.js is not installed or not in PATH${NC}"
    echo -e "${YELLOW}💡 Tip: Install Node.js from https://nodejs.org/${NC}"
    exit 1
fi

# Check for environment variables
if [ -z "$GOOGLE_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  Warning: GOOGLE_API_KEY environment variable not set${NC}"
    echo -e "${YELLOW}   The chat app may not work without a valid API key${NC}"
    echo -e "${YELLOW}   Set it with: export GOOGLE_API_KEY=your_api_key_here${NC}"
fi

echo -e "${GREEN}📦 Running ${JS_FILENAME} application...${NC}"
echo "JavaScript file: ${CHAT_JS_PATH}"
echo ""

# Run the application with Node.js
cd "$PROJECT_ROOT"
node -r dotenv/config "$CHAT_JS_PATH"

echo ""
echo -e "${GREEN}✅ ${JS_FILENAME} application finished${NC}"
