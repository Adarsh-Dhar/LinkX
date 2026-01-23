
#!/bin/bash

# Simple Alpha-Consumer System Startup Script
# Starts: Node Server (Market) -> Python Agent API -> Next.js Frontend

set -e

# Start 48 mock data providers (Python Flask, ports 4000-4047)
echo "Starting 48 mock data providers (ports 4000-4047)..."
MOCK_PROVIDER_SCRIPT="/tmp/mock_provider_$$.py"
cat > "$MOCK_PROVIDER_SCRIPT" << 'EOF'
from flask import Flask, jsonify, request
import random
import sys
app = Flask(__name__)
@app.route('/data', methods=['GET'])
def data():
  value = round(random.uniform(0.01, 1.0), 4)
  port = int(sys.argv[1])
  # Sentiment nodes: ports 4026, 4027
  # Volatility nodes: ports 4044, 4045
  if port in [4026, 4027]:
    return jsonify({"data": {"sentiment": value}})
  elif port in [4044, 4045]:
    return jsonify({"data": {"volatility": value}})
  else:
    return jsonify({"data": {"value": value}})
if __name__ == '__main__':
  port = int(sys.argv[1])
  app.run(host='0.0.0.0', port=port)
EOF

for PORT in $(seq 4000 4047); do
  python3 "$MOCK_PROVIDER_SCRIPT" $PORT &
done
sleep 2

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Starting Market Analyst Server (Node.js)..."
cd "$SCRIPT_DIR/server"
if [ ! -d "node_modules" ]; then
  pnpm install
fi
pnpm start &
cd "$SCRIPT_DIR"
sleep 2

echo "Starting Agent API (FastAPI)..."
cd "$SCRIPT_DIR/agent"
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
cd "$SCRIPT_DIR"
uvicorn agent.api:app --host 0.0.0.0 --port 8000 &
sleep 3

echo "Starting Frontend (Next.js)..."
cd "$SCRIPT_DIR/frontend"
if [ ! -d "node_modules" ]; then
  pnpm install
fi
pnpm run dev &
cd "$SCRIPT_DIR"

echo "All services started."
echo "(To stop all mock providers: killall -9 python3)"
wait
