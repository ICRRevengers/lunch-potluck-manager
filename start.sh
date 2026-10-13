#!/bin/bash
set -e

DIR="/home/phu/workspace/repo/lunch-potluck-manager"
cd "$DIR"

# Kill existing instances if any
pkill -f "python3.*server.py" || true
pkill -f "cloudflared.*8080" || true
sleep 1

# Start python server
python3 server.py > server.log 2>&1 &
SERVER_PID=$!
echo "Python server started with PID $SERVER_PID"

# Wait for port 8080 to be ready
while ! nc -z 127.0.0.1 8080 && ! curl -s http://127.0.0.1:8080 > /dev/null 2>&1; do
    sleep 0.5
done
echo "Server is responding on port 8080!"

# Start cloudflared tunnel
rm -f tunnel.log
/home/phu/.local/bin/cloudflared tunnel --url http://127.0.0.1:8080 > tunnel.log 2>&1 &
TUNNEL_PID=$!
echo "Cloudflared tunnel started with PID $TUNNEL_PID"

# Wait for tunnel URL to appear in log
TUNNEL_URL=""
for i in {1..30}; do
    TUNNEL_URL=$(grep -o "https://[a-zA-Z0-9.-]*\.trycloudflare\.com" tunnel.log | head -n 1 || true)
    if [ -n "$TUNNEL_URL" ]; then
        break
    fi
    sleep 1
done

echo "TUNNEL_URL=$TUNNEL_URL"
echo "$TUNNEL_URL" > current_url.txt

# Keep script running to keep child processes alive
wait
