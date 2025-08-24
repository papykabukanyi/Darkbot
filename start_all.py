#!/usr/bin/env python3
"""Orchestrator to run the advanced scalping bot and Flask API"""
import os
import sys
import signal
import subprocess
import time

# Use the new advanced bot
BOT_CMD = [sys.executable, "advanced_scalping_bot.py"]

PROCESSES = {}

def start_bot():
    print(f"[orchestrator] Starting advanced scalping bot: {' '.join(BOT_CMD)}", flush=True)
    PROCESSES['bot'] = subprocess.Popen(BOT_CMD)

def start_api():
    port = os.getenv("PORT", "8080")
    gunicorn_cmd = [
        "gunicorn",
        "--bind", f"0.0.0.0:{port}",
        "app:app"
    ]
    print(f"[orchestrator] Starting API: {' '.join(gunicorn_cmd)}", flush=True)
    PROCESSES['api'] = subprocess.Popen(gunicorn_cmd)

SHUTDOWN = False

def handle_signal(signum, frame):
    global SHUTDOWN
    print(f"[orchestrator] Signal {signum} received, shutting down...", flush=True)
    SHUTDOWN = True
    for name, proc in PROCESSES.items():
        if proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass
    # Grace period
    deadline = time.time() + 10
    for name, proc in PROCESSES.items():
        if proc.poll() is None:
            try:
                proc.wait(timeout=max(0, deadline - time.time()))
            except Exception:
                proc.kill()
    sys.exit(0)

for s in (signal.SIGTERM, signal.SIGINT):
    signal.signal(s, handle_signal)

start_bot()
start_api()

# Supervise
while not SHUTDOWN:
    time.sleep(5)
    # If API dies -> exit (let platform restart container)
    if PROCESSES['api'].poll() is not None:
        print("[orchestrator] API process exited, shutting down", flush=True)
        handle_signal(signal.SIGTERM, None)
    # If bot dies -> restart it once
    if PROCESSES['bot'].poll() is not None:
        print("[orchestrator] Bot process exited, restarting...", flush=True)
        start_bot()
