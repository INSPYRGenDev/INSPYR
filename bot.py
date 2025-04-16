import discord
from discord.ext import commands
import os
import random
import json
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# XP and Level system
xp_data = {}

def save_xp():
    with open("xp.json", "w") as f:
        json.dump(xp_data, f)

def load_xp():
    global xp_data
    if os.path.exists("xp.json"):
        with open("xp.json", "r") as f:
            xp_data = json.load(f)

def add_xp(user_id, amount):
    user_id = str(user_id)
    if user_id not in xp_data:
        xp_data[user_id] = {"xp": 0, "level": 1}
    xp_data[user_id]["xp"] += amount
    new_level = int(xp_data[user_id]["xp"] ** 0.5)
    if new_level > xp_data[user_id]["level"]:
        xp_data[user_id]["level"] = new_level
        return new_level
    return None

load_xp()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"Sync failed: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    new_level = add_xp(message.author.id, random.randint(5, 15))
    if new_level:
        await message.channel.send(f"🎉 {message.author.mention} leveled up to {new_level}!")
        save_xp()

    await bot.process_commands(message)

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello, {ctx.author.name}!")

@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")

@bot.command()
async def guess(ctx):
    number = random.randint(1, 10)
    await ctx.send("Guess a number between 1 and 10!")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        guess = await bot.wait_for("message", check=check, timeout=10)
        if int(guess.content) == number:
            await ctx.send("Correct!")
        else:
            await ctx.send(f"Nope, it was {number}!")
    except:
        await ctx.send("Took too long!")

@bot.command()
async def hangman(ctx):
    word = random.choice(["python", "discord", "hangman"])
    guessed = ["_"] * len(word)
    attempts = 6
    await ctx.send(f"Word: {' '.join(guessed)} — Attempts left: {attempts}")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and len(m.content) == 1

    while "_" in guessed and attempts > 0:
        try:
            guess = await bot.wait_for("message", check=check, timeout=30)
            letter = guess.content.lower()
            if letter in word:
                for i, l in enumerate(word):
                    if l == letter:
                        guessed[i] = letter
            else:
                attempts -= 1
            await ctx.send(f"{' '.join(guessed)} — Attempts left: {attempts}")
        except:
            break

    if "_" not in guessed:
        await ctx.send("You guessed it!")
    else:
        await ctx.send(f"Game over! The word was: {word}")

@bot.command()
async def poll(ctx, *, question):
    await ctx.send(f"📊 {question}", view=PollView())

class PollView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(label="👍", style=discord.ButtonStyle.green, custom_id="vote_up"))
        self.add_item(discord.ui.Button(label="👎", style=discord.ButtonStyle.red, custom_id="vote_down"))

@bot.command()
async def leaderboard(ctx):
    sorted_users = sorted(xp_data.items(), key=lambda x: x[1]["xp"], reverse=True)[:5]
    embed = discord.Embed(title="🏆 XP Leaderboard", color=discord.Color.gold())
    for i, (user_id, data) in enumerate(sorted_users, 1):
        embed.add_field(name=f"#{i}", value=f"<@{user_id}> - Level {data['level']}, XP {data['xp']}", inline=False)
    await ctx.send(embed=embed)

bot.run(TOKEN)