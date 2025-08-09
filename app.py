import os, threading, logging
from flask import Flask

# ---------- Flask ----------
app = Flask(__name__)

@app.route("/")
def index():
    return "Welcome Fairy is alive."

@app.route("/health")
def health():
    return ("OK", 200)

# ---------- Discord bot (runs in a side thread) ----------
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# lazy-import so the web boot never dies if discord.py isn't ready yet
def _start_bot():
    import discord
    from discord.ext import commands

    intents = discord.Intents.default()
    intents.message_content = True  # make sure this is also enabled in the Dev Portal

    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        print(f"[discord] Logged in as {bot.user} (id: {bot.user.id})")

    @bot.command()
    async def ping(ctx):
        await ctx.send("pong 🫡")

    # run() blocks, so we run it here in this thread
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logging.exception("Discord bot crashed: %s", e)

# spawn the bot thread once, at import time
if DISCORD_TOKEN:
    t = threading.Thread(target=_start_bot, name="discord-bot", daemon=True)
    t.start()
else:
    print("[discord] No DISCORD_TOKEN set – bot will not start.")
async def ping(ctx): await ctx.send("pong")

def run_bot():
    if not TOKEN:
        print("❌ No DISCORD_TOKEN set in environment"); return
    bot.run(TOKEN)

# ---------- START BOTH ----------
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    run_bot()
