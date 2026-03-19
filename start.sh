#!/usr/bin/env bash
# ============================================================
# Gold & Crypto Backtest Dashboard — One-command launcher
# ============================================================
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  Gold & Crypto Backtest Dashboard${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 not found. Please install Python 3.11+."
  exit 1
fi

# Check Node/pnpm
if ! command -v pnpm &>/dev/null && ! command -v npm &>/dev/null; then
  echo "ERROR: pnpm/npm not found. Please install Node.js."
  exit 1
fi

PKG_MGR="pnpm"
command -v pnpm &>/dev/null || PKG_MGR="npm"

# Install backend deps if needed
echo -e "${CYAN}Checking backend dependencies...${NC}"
cd "$BACKEND"
python3 -c "import fastapi, uvicorn, yfinance, talib, vectorbt" 2>/dev/null || {
  echo "Installing backend dependencies..."
  pip install -r requirements.txt -q
}

# Install frontend deps if needed
echo -e "${CYAN}Checking frontend dependencies...${NC}"
cd "$FRONTEND"
if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies..."
  $PKG_MGR install
fi

# Start backend
echo ""
echo -e "${GREEN}Starting Backend API on http://localhost:8000${NC}"
cd "$BACKEND"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to be ready
echo -n "Waiting for backend..."
for i in {1..20}; do
  if curl -s http://localhost:8000/health &>/dev/null; then
    echo -e " ${GREEN}ready!${NC}"
    break
  fi
  sleep 1
  echo -n "."
done

# Start frontend
echo -e "${GREEN}Starting Frontend on http://localhost:5173${NC}"
cd "$FRONTEND"
$PKG_MGR run dev &
FRONTEND_PID=$!

echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${GREEN}Dashboard: http://localhost:5173${NC}"
echo -e "${GREEN}API Docs:  http://localhost:8000/docs${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo "Press Ctrl+C to stop both servers."
echo ""

# Cleanup on exit
trap "echo ''; echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
