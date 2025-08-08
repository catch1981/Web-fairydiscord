import os
import io
import json
import importlib
import threading
from collections import deque
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, session, send_from_directory, flash

# --- Config ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Fairydust12!"  # You asked for this explicit password; change it anytime in the editor.
SECRET_KEY = os.environ.get("WF_SECRET_KEY", "change-this-secret-in-render-env")

CONFIG_PATH = "config.json"
BOT_MODULE_NAME = "bot_logic"

# --- Live log buffer ---
LOG_BUFFER = deque(maxlen=2000)  # stores recent log lines for the live console

def log_line(msg):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    LOG_BUFFER.append(f"{timestamp} | {msg}")

# --- Load config ---
def load_config():
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w") as f:
            json.dump({}, f)
    with open(CONFIG_PATH, "r") as f:
        try:
            data = json.load(f)
            return data
        except Exception:
            return {}

def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)

# --- Bot holder ---
class BotHolder:
    def __init__(self):
        self.bot = None
        self.module = None
        self.lock = threading.Lock()

    def start(self):
        with self.lock:
            self._ensure_loaded()
            if self.bot and self.bot.is_running():
                log_line("Bot already running.")
                return
            if self.bot:
                self.bot.start()
                log_line("Bot start requested.")
            else:
                log_line("Bot module not loaded.")

    def stop(self):
        with self.lock:
            if self.bot:
                self.bot.stop()
                log_line("Bot stop requested.")
            else:
                log_line("No bot instance to stop.")

    def restart(self):
        with self.lock:
            if self.bot and self.bot.is_running():
                self.bot.stop()
            self._reload_module()
            self._instantiate_bot()
            if self.bot:
                self.bot.start()
                log_line("Bot restart requested.")

    def _ensure_loaded(self):
        if self.module is None:
            self._reload_module()
            self._instantiate_bot()

    def _reload_module(self):
        try:
            if self.module is None:
                self.module = importlib.import_module(BOT_MODULE_NAME)
            else:
                self.module = importlib.reload(self.module)
            log_line("bot_logic module loaded/reloaded.")
        except Exception as e:
            log_line(f"Error loading bot module: {e}")

    def _instantiate_bot(self):
        try:
            cfg = load_config()
            self.bot = self.module.BotWorker(cfg, log_line)
            log_line("BotWorker instantiated.")
        except Exception as e:
            log_line(f"Error instantiating BotWorker: {e}")

    def is_running(self):
        with self.lock:
            return bool(self.bot and self.bot.is_running())

BOT = BotHolder()

# --- Flask app ---
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = SECRET_KEY

def is_authed():
    return session.get("authed") is True

@app.route("/")
def index():
    running = BOT.is_running()
    cfg = load_config()
    return render_template("status.html", running=running, cfg=cfg)

@app.route("/ping")
def ping():
    return "ok", 200

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        if u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
            session["authed"] = True
            return redirect(url_for("edit"))
        else:
            flash("Invalid credentials", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/edit", methods=["GET", "POST"])
def edit():
    if not is_authed():
        return redirect(url_for("login"))

    message = ""
    # Handle config updates
    if request.method == "POST":
        action = request.form.get("action", "")

        if action == "save_config":
            cfg = load_config()
            cfg["discord_bot_token"] = request.form.get("discord_bot_token", cfg.get("discord_bot_token", ""))
            cfg["server_id"] = request.form.get("server_id", cfg.get("server_id", ""))
            cfg["channel_id"] = request.form.get("channel_id", cfg.get("channel_id", ""))
            cfg["firebase_api_key"] = request.form.get("firebase_api_key", cfg.get("firebase_api_key", ""))
            cfg["elevenlabs_api_key"] = request.form.get("elevenlabs_api_key", cfg.get("elevenlabs_api_key", ""))
            # A generic JSON string for other envs
            other_env = request.form.get("other_env", "")
            try:
                cfg["other_env"] = json.loads(other_env) if other_env.strip() else {}
            except Exception:
                cfg["other_env"] = other_env  # leave as raw string if invalid JSON
            save_config(cfg)
            message = "Config saved."

        elif action == "save_code":
            code_text = request.form.get("code_text", "")
            if code_text:
                with open("bot_logic.py", "w", encoding="utf-8") as f:
                    f.write(code_text)
                BOT.restart()
                message = "Code saved and bot restarted."

        elif action == "upload_code":
            file = request.files.get("code_file")
            if file and file.filename.lower().endswith(".py"):
                # Replace bot_logic.py
                file.save("bot_logic.py")
                BOT.restart()
                message = f"Uploaded {file.filename} and bot restarted."

        elif action == "restart_bot":
            BOT.restart()
            message = "Bot restart requested."

        elif action == "stop_bot":
            BOT.stop()
            message = "Bot stop requested."

        elif action == "start_bot":
            BOT.start()
            message = "Bot start requested."

    # Load current code/config/logs
    try:
        with open("bot_logic.py", "r", encoding="utf-8") as f:
            current_code = f.read()
    except Exception:
        current_code = "# bot_logic.py missing or unreadable"

    cfg = load_config()
    log_text = "\n".join(list(LOG_BUFFER)[-500:])  # last 500 lines

    return render_template("editor.html",
                           current_code=current_code,
                           cfg=cfg,
                           log_text=log_text,
                           message=message,
                           running=BOT.is_running())

# --- Auto-start bot on boot ---
with app.app_context():
    try:
        BOT.start()
    except Exception as e:
        log_line(f"Auto-start failed: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
