"""
Welcome Fairy - Bot Logic
This file is live-editable from the /edit page or by uploading a new .py file.

Contract:
- Must expose a class BotWorker with methods: __init__(config, logger), start(), stop(), is_running().
- Work should run in a background thread created inside start().
- Use `self.logger(msg)` to emit lines to the live console on the editor page.
"""

import threading
import time

class BotWorker:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger  # call with strings to emit to live console
        self._thread = None
        self._stop = threading.Event()

    def _run(self):
        self.logger("Welcome Fairy bot thread started.")
        # Example heartbeat loop. Replace with your Discord/Firebase/etc logic.
        i = 0
        while not self._stop.is_set():
            i += 1
            self.logger(f"[heartbeat] Welcome Fairy alive — tick {i}")
            time.sleep(5)

        self.logger("Welcome Fairy bot thread stopping...")

    def start(self):
        if self._thread and self._thread.is_alive():
            self.logger("Bot already running; start() ignored.")
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._thread = None

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()
