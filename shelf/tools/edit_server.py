#!/usr/bin/env python3
"""Start the shelf server so the in-page editor can save.

The everyday server runs as a LaunchAgent and macOS will not let a launchd job
WRITE inside ~/Documents, only read it — so saving from the editor fails against
it with "Operation not permitted". Started from a terminal instead, the same
server inherits that terminal's access and saving works.

    python3 shelf/tools/edit_server.py          # then open localhost:3412/shelf/?edit=1

To use the ordinary port 3411 for editing too, give Full Disk Access to the
Python that runs the LaunchAgent in System Settings > Privacy & Security.
"""
import os, runpy, sys

sys.argv = [sys.argv[0], sys.argv[1] if len(sys.argv) > 1 else "3412"]
runpy.run_path(os.path.expanduser("~/Library/Application Support/studiomacon-site/serve.py"),
               run_name="__main__")
