# app.py — minimal Render-friendly Discord bot + tiny web
import os, threading
from flask import Flask
import discord
from discord.ext import commands

# ---------- CONFIG ----------
TOKEN = os.getenv("DISCORD_TOKEN")  # set this in Render Environment
PORT = int(os.getenv("PORT", "10000"))

# ---------- WEB ----------
app = Flask(__name__)
@app.get("/")
def home(): return "Welcome Fairy is alive.", 200
@app.get("/healthz")
def healthz(): return "ok", 200
def run_web(): app.run(host="0.0.0.0", port=PORT)

# ---------- DISCORD ----------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (id: {bot.user.id})")
    await bot.change_presence(activity=discord.Game(name="type !ping"))

@bot.command()
async def ping(ctx): await ctx.send("pong")

def run_bot():
    if not TOKEN:
        print("❌ No DISCORD_TOKEN set in environment"); return
    bot.run(TOKEN)

# ---------- START BOTH ----------
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    run_bot()
