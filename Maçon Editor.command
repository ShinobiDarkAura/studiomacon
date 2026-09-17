#!/bin/bash
# Double-click this to open the Maçon editor. It runs only on this Mac.
cd "$(dirname "$0")" || exit 1
PORT=3470
# if something is already serving, just open the editor
if ! curl -s -o /dev/null "http://127.0.0.1:$PORT/pdp/index.html"; then
  python3 pdp/serve.py "$PORT" &
  for i in $(seq 1 20); do
    curl -s -o /dev/null "http://127.0.0.1:$PORT/pdp/index.html" && break
    sleep 0.5
  done
fi
open "http://127.0.0.1:$PORT/pdp/_editor/index.html"
echo
echo "The editor is open in your browser."
echo "Leave this window open while you work. Close it when you are done."
echo
wait
