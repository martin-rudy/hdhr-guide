#!/usr/bin/env python3
"""
HDHomeRun XMLTV Guide Server
- Fetches DeviceAuth from the HDHomeRun tuner
- Downloads XMLTV guide from Silicondust API
- Re-fetches every 12 hours (DeviceAuth lasts 16-24 hrs)
- Serves /xmlguide.xmltv on port 9000
"""

import http.server
import socketserver
import threading
import urllib.request
import json
import time
import os
import random
import gzip

HDHR_URL = os.environ.get("HDHR_URL", "")
PORT = int(os.environ.get("PORT", "9000"))
# Refresh interval in hours (DeviceAuth valid 16-24 hrs, default 12)
REFRESH_SECONDS = int(float(os.environ.get("REFRESH_HOURS", "12")) * 3600)

GUIDE_XML = b""

def get_device_auth():
    """Query HDHomeRun for a fresh DeviceAuth."""
    try:
        req = urllib.request.Request(HDHR_URL)
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        auth = data.get("DeviceAuth", "")
        device_id = data.get("DeviceID", "")
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Got DeviceAuth from {device_id}")
        return auth
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ERROR getting DeviceAuth: {e}")
        return None

def fetch_guide():
    """Fetch the XMLTV guide from Silicondust API."""
    global GUIDE_XML
    auth = get_device_auth()
    if not auth:
        return

    url = f"https://api.hdhomerun.com/api/xmltv?DeviceAuth={auth}"
    try:
        req = urllib.request.Request(url, headers={
            "Accept-Encoding": "gzip",
            "User-Agent": "HDHR-Guide/1.0"
        })
        resp = urllib.request.urlopen(req, timeout=60)
        data = resp.read()

        # Handle gzip encoding
        if resp.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)

        GUIDE_XML = data
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Guide updated ({len(data)} bytes)")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ERROR fetching guide: {e}")


class GuideHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/xmlguide.xmltv":
            if not GUIDE_XML:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b"Guide not yet loaded. Try again in a moment.")
                return
            self.send_response(200)
            self.send_header("Content-type", "text/xml")
            self.send_header("Content-Length", str(len(GUIDE_XML)))
            self.end_headers()
            self.wfile.write(GUIDE_XML)
        elif self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 - try /xmlguide.xmltv or /health")

def guide_updater():
    """Background thread that refreshes the guide with random jitter."""
    first_run = True
    while True:
        if not first_run:
            fetch_guide()
        first_run = False
        # Schedule next refresh with random jitter (per API docs)
        sleep_time = REFRESH_SECONDS + random.randint(-1800, 1800)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Next refresh in {sleep_time // 60} minutes")
        time.sleep(sleep_time)

if __name__ == "__main__":
    print(f"HDHomeRun Guide Server starting...")
    print(f"  HDHR URL: {HDHR_URL}")
    print(f"  Port: {PORT}")
    print(f"  Refresh: every {REFRESH_SECONDS // 60} minutes")

    # Fetch guide immediately on startup (no jitter)
    print("Fetching initial guide data...")
    fetch_guide()

    # Start background guide updater (with jitter on subsequent refreshes)
    updater = threading.Thread(target=guide_updater, daemon=True)
    updater.start()

    # Start HTTP server
    with socketserver.TCPServer(("", PORT), GuideHandler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()
