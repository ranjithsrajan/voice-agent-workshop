#!/bin/bash
# ─────────────────────────────────────────────────
#  Voice Agent Workshop — Start All Components
# ─────────────────────────────────────────────────
# Starts:
#   1. Ops-UI Backend   (FastAPI on :8000)
#   2. Outbound Agent   (LiveKit agent)
#   3. Ops-UI Frontend  (Vite on :5173)
#
# Usage:  ./start.sh          — start all
#         ./start.sh stop     — kill all background processes
# ─────────────────────────────────────────────────

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$ROOT_DIR/venv/bin/python3"
LOG_DIR="$ROOT_DIR/.logs"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

mkdir -p "$LOG_DIR"

# ── Stop mode ──
if [ "$1" = "stop" ]; then
    echo -e "${YELLOW}Stopping all components...${NC}"
    [ -f "$LOG_DIR/backend.pid" ]  && kill "$(cat "$LOG_DIR/backend.pid")"  2>/dev/null && echo -e "  ${RED}■${NC} Backend stopped"
    [ -f "$LOG_DIR/agent.pid" ]    && kill "$(cat "$LOG_DIR/agent.pid")"    2>/dev/null && echo -e "  ${RED}■${NC} Agent stopped"
    [ -f "$LOG_DIR/frontend.pid" ] && kill "$(cat "$LOG_DIR/frontend.pid")" 2>/dev/null && echo -e "  ${RED}■${NC} Frontend stopped"
    rm -f "$LOG_DIR"/*.pid
    echo -e "${GREEN}All stopped.${NC}"
    exit 0
fi

# ── Pre-flight checks ──
echo -e "${BLUE}━━━ Voice Agent Workshop ━━━${NC}"
echo ""

if [ ! -f "$VENV_PYTHON" ]; then
    echo -e "${RED}✗ Python venv not found at $VENV_PYTHON${NC}"
    echo "  Run:  python3 -m venv venv && venv/bin/pip install -r requirements.txt"
    exit 1
fi

if [ ! -f "$ROOT_DIR/.env.local" ]; then
    echo -e "${RED}✗ .env.local not found${NC}"
    echo "  Copy .env.example to .env.local and fill in your keys."
    exit 1
fi

if ! command -v lk &>/dev/null; then
    echo -e "${YELLOW}⚠ 'lk' CLI not found — agent calls may not dispatch properly${NC}"
fi

if ! command -v node &>/dev/null; then
    echo -e "${RED}✗ Node.js not found${NC}"
    exit 1
fi

# ── Kill any existing processes on our ports ──
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:5173 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 0.5

# ── 1. Ops-UI Backend (FastAPI) ──
echo -e "${GREEN}▶ Starting Ops-UI Backend${NC}  (port 8000)"
cd "$ROOT_DIR/ops-ui"
"$VENV_PYTHON" server.py > "$LOG_DIR/backend.log" 2>&1 &
echo $! > "$LOG_DIR/backend.pid"

# ── 2. Outbound Agent ──
echo -e "${GREEN}▶ Starting Outbound Agent${NC}  (LiveKit agent)"
cd "$ROOT_DIR"
"$VENV_PYTHON" obAgent.py dev > "$LOG_DIR/agent.log" 2>&1 &
echo $! > "$LOG_DIR/agent.pid"

# ── 3. Ops-UI Frontend (Vite) ──
echo -e "${GREEN}▶ Starting Ops-UI Frontend${NC} (port 5173)"
cd "$ROOT_DIR/ops-ui"
npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
echo $! > "$LOG_DIR/frontend.pid"

# ── Wait for services ──
echo ""
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 3

# Check backend
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Backend       → http://localhost:8000"
else
    echo -e "  ${YELLOW}⏳${NC} Backend       → http://localhost:8000  (may still be starting)"
fi

# Check agent
if kill -0 "$(cat "$LOG_DIR/agent.pid" 2>/dev/null)" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Agent         → running (PID $(cat "$LOG_DIR/agent.pid"))"
else
    echo -e "  ${RED}✗${NC} Agent         → failed to start — check $LOG_DIR/agent.log"
fi

# Check frontend
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Frontend      → http://localhost:5173"
else
    echo -e "  ${YELLOW}⏳${NC} Frontend      → http://localhost:5173  (may still be starting)"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "Logs:  ${YELLOW}$LOG_DIR/${NC}"
echo -e "Stop:  ${YELLOW}./start.sh stop${NC}"
echo ""
echo -e "Tail logs:"
echo -e "  tail -f $LOG_DIR/backend.log"
echo -e "  tail -f $LOG_DIR/agent.log"
echo -e "  tail -f $LOG_DIR/frontend.log"
echo ""
echo -e "${GREEN}All components launched!${NC} Open ${BLUE}http://localhost:5173${NC}"

# Keep script alive to show logs interleaved
wait
