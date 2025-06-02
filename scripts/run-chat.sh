#!/bin/bash

# Script to run the LangChain Chat application
# Executes the compiled JavaScript output from the ReasonML Chat.re module

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# CHAT_JS_PATH="${PROJECT_ROOT}/_build/default/src/agentArchitect/src/exe/Chat_Interf.js"
CHAT_JS_PATH="${PROJECT_ROOT}/_build/default/src/agentArchitect/src/exe/EvalMbpp.js"

echo -e "${GREEN}🚀 Agent Architect - Chat Application Runner${NC}"
echo "Project root: ${PROJECT_ROOT}"

# Check if the compiled JavaScript file exists
if [ ! -f "$CHAT_JS_PATH" ]; then
    echo -e "${RED}❌ Error: Compiled Chat.js not found at ${CHAT_JS_PATH}${NC}"
    echo -e "${YELLOW}💡 Tip: Run 'npm run build' first to compile the ReasonML code${NC}"
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

echo -e "${GREEN}📦 Running Chat application...${NC}"
echo "JavaScript file: ${CHAT_JS_PATH}"
echo ""

# Run the Chat application with Node.js
cd "$PROJECT_ROOT"
node -r dotenv/config "$CHAT_JS_PATH"

echo ""
echo -e "${GREEN}✅ Chat application finished${NC}"
