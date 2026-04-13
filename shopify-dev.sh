#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
frontend_dir="$script_dir/frontend"
backend_dir="$script_dir/backend"

frontend_port="${FRONTEND_PORT:-3000}"
backend_port="${BACKEND_PORT:-8000}"
ngrok_api_url="http://127.0.0.1:4040/api/tunnels"

reuse_existing="${REUSE_EXISTING_NGROK:-1}"

cleanup() {
  pkill -f "uvicorn src.endpoints.getData" 2>/dev/null || true
  pkill -f "bun run dev" 2>/dev/null || true
  pkill -f "ngrok http" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

check_existing_ngrok() {
  if curl -s "$ngrok_api_url" >/dev/null 2>&1; then
    existing_url=$(curl -s "$ngrok_api_url" | grep -oE '"public_url":"https://[^"]+' | head -1 | sed 's/"public_url":"//')
    if [ -n "$existing_url" ]; then
      echo "$existing_url"
      return 0
    fi
  fi
  return 1
}

start_ngrok() {
  ngrok http "$frontend_port" > /dev/null 2>&1 &
  
  for i in {1..15}; do
    if curl -s "$ngrok_api_url" >/dev/null 2>&1; then
      sleep 1
      break
    fi
    sleep 1
  done
  
  curl -s "$ngrok_api_url" | grep -oE '"public_url":"https://[^"]+' | head -1 | sed 's/"public_url":"//'
}

get_or_create_ngrok_url() {
  if [ "$reuse_existing" = "1" ]; then
    existing=$(check_existing_ngrok)
    if [ -n "$existing" ]; then
      echo "$existing"
      return 0
    fi
  fi
  start_ngrok
}

echo "Starting backend..."
cd "$backend_dir"
export PATH="$HOME/.local/bin:$PATH"
uv run python -m uvicorn src.endpoints.getData:app --reload --host 127.0.0.1 --port "$backend_port" &
BACKEND_PID=$!

echo "Waiting for backend..."
for i in {1..10}; do
  if curl -s -o /dev/null http://127.0.0.1:"$backend_port"/docs 2>/dev/null; then
    break
  fi
  sleep 1
done

echo "Starting ngrok..."
ngrok_url=$(get_or_create_ngrok_url)

echo "Starting frontend..."
cd "$frontend_dir"
export NUXT_DEV_TUNNEL_URL="$ngrok_url"
bun run dev --host 127.0.0.1 --port "$frontend_port" &
FRONTEND_PID=$!

echo "Waiting for frontend..."
for i in {1..15}; do
  if curl -s -o /dev/null http://127.0.0.1:"$frontend_port" 2>/dev/null; then
    break
  fi
  sleep 1
done

echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  Development server ready"
echo "══════════════════════════════════════════════════════════════"
echo ""
echo "  🌐 Ngrok URL:    $ngrok_url"
echo "  📱 Frontend:     http://127.0.0.1:$frontend_port"
echo "  ⚙️  Backend:      http://127.0.0.1:$backend_port"
echo "  📖 API Docs:     http://127.0.0.1:$backend_port/docs"
echo ""
echo "  Update your Shopify app config with:"
echo "    App URL:        $ngrok_url"
echo "    Callback URL:   $ngrok_url/auth/shopify/callback"
echo ""
echo "  Press Ctrl+C to stop all services"
echo "══════════════════════════════════════════════════════════════"
echo ""

wait