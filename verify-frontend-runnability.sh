#!/bin/bash

echo "Verifying frontend application runnability..."

# Navigate to the frontend directory
if [ ! -d "frontend" ]; then
  echo "Error: 'frontend' directory not found. Please ensure the frontend scaffolding is in place." >&2
  exit 1
fi
cd frontend || exit 1

echo "Installing frontend dependencies..."
npm install
if [ $? -ne 0 ]; then
  echo "Error: npm install failed." >&2
  exit 1
fi

echo "Starting frontend development server in background (http://localhost:3000)..."
npm run dev &
DEV_SERVER_PID=$!

# Give the server some time to start up
echo "Waiting for server to start (10 seconds)..."
sleep 10

# Check if the server is running by making an HTTP request
echo "Attempting to connect to http://localhost:3000..."
curl --silent --fail http://localhost:3000 > /dev/null
if [ $? -eq 0 ]; then
  echo "Success: Frontend development server is running and accessible on http://localhost:3000."
  TEST_RESULT=0
else
  echo "Error: Frontend development server did not respond on http://localhost:3000." >&2
  TEST_RESULT=1
fi

# Clean up: kill the background process
echo "Stopping frontend development server (PID: $DEV_SERVER_PID)..."
kill $DEV_SERVER_PID
wait $DEV_SERVER_PID 2>/dev/null

exit $TEST_RESULT