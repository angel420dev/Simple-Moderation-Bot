import discord
from discord.ext import commands
from discord import Embed
import random
import asyncio
import os
import logging
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    print("ERROR: DISCORD_TOKEN is not set. Check your .env file.")
    exit()


async def on_ready():
    await bot.change_presence(activity=discord.Game(name="Watching You"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ModerationBot")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

log_channel_id = None

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
@commands.has_permissions(manage_guild=True)
async def log(ctx):
    global log_channel_id
    log_channel_id = ctx.channel.id
    await ctx.send(f" Logging channel set to {ctx.channel.mention}")


async def log_event(description):
    await bot.wait_until_ready()
    if log_channel_id:
        channel = bot.get_channel(log_channel_id)
        if channel:
            embed = Embed(description=description, color=discord.Color.blue())
            await channel.send(embed=embed)

@bot.event
async def on_guild_channel_create(channel):
    await log_event(f" Channel created: {channel.mention} (`{channel.name}`)")

@bot.event
async def on_guild_channel_delete(channel):
    await log_event(f" Channel deleted: `{channel.name}`")

@bot.event
async def on_guild_role_create(role):
    await log_event(f" Role created: `{role.name}`")

@bot.event
async def on_guild_role_delete(role):
    await log_event(f" Role deleted: `{role.name}`")

@bot.event
async def on_guild_role_update(before, after):
    changes = []
    if before.name != after.name:
        changes.append(f" Name changed: `{before.name}` → `{after.name}`")
    if before.color != after.color:
        changes.append(f" Color changed: `{before.color}` → `{after.color}`")
    if before.hoist != after.hoist:
        changes.append(" Role is now **hoisted**" if after.hoist else " Role is **no longer hoisted**")
    if changes:
        await log_event(f" Role updated: `{before.name}`\n" + "\n".join(changes))

@bot.event
async def on_member_update(before, after):
    if before.roles != after.roles:
        removed_roles = [r.name for r in before.roles if r not in after.roles]
        added_roles = [r.name for r in after.roles if r not in before.roles]
        if added_roles:
            await log_event(f" `{before.name}` was given: {', '.join(added_roles)}")
        if removed_roles:
            await log_event(f" `{before.name}` lost: {', '.join(removed_roles)}")


@bot.event
async def on_member_join(member):
    await log_event(f" `{member}` joined the server.")

@bot.event
async def on_member_remove(member):
    await log_event(f" `{member}` left the server.")

@bot.event
async def on_member_ban(guild, user):
    await log_event(f" `{user}` was **banned**.")

@bot.event
async def on_member_unban(guild, user):
    await log_event(f" `{user}` was **unbanned**.")

@bot.event
async def on_member_kick(guild, user):
    await log_event(f" `{user}` was **kicked**.")

@bot.event
async def on_message_edit(before, after):
    if before.content != after.content:
        await log_event(f" Message edited in {before.channel.mention}\n**Before:** {before.content}\n**After:** {after.content}")

@bot.event
async def on_message_delete(message):
    await log_event(f" Message deleted in {message.channel.mention}\n**Content:** {message.content}")

@bot.event
async def on_guild_update(before, after):
    changes = []
    if before.name != after.name:
        changes.append(f" Server name changed: `{before.name}` → `{after.name}`")
    if before.icon != after.icon:
        changes.append(" Server icon was changed.")
    if changes:
        await log_event("\n".join(changes))


@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, user: discord.Member, *, reason="No reason provided"):
    await user.ban(reason=reason)
    await log_event(f" `{user}` was **banned** by `{ctx.author}` for: {reason}")
    await ctx.send(f"Banned {user}.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, user: discord.Member, *, reason="No reason provided"):
    await user.kick(reason=reason)
    await log_event(f" `{user}` was **kicked** by `{ctx.author}` for: {reason}")
    await ctx.send(f"Kicked {user}.")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, user: discord.Member, seconds: int, *, reason="No reason provided"):
    try:
        await user.timeout(duration=discord.utils.utcnow() + discord.timedelta(seconds=seconds), reason=reason)
        await log_event(f" `{user}` was **timed out** for {seconds} seconds by `{ctx.author}` for: {reason}")
        await ctx.send(f"Timed out {user} for {seconds} seconds.")
    except AttributeError:
        await ctx.send("This version of discord.py does not support timeouts!")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 100):
    await ctx.channel.purge(limit=amount)
    await log_event(f" `{ctx.author}` cleared {amount} messages in {ctx.channel.mention}.")
    await ctx.send(f"Cleared {amount} messages.", delete_after=3)


@bot.command()
async def coinflip(ctx):
    await ctx.send(f"The coin landed on: {random.choice(['Heads', 'Tails'])}")

@bot.command()
async def trivia(ctx):
    questions = [
        {"question": "What's the capital of France?", "answer": "Paris"},
        {"question": "What is 2 + 2?", "answer": "4"},
        {"question": "Who wrote 'Hamlet'?", "answer": "Shakespeare"}
    ]
    question = random.choice(questions)
    await ctx.send(question["question"])

    def check(m): return m.author == ctx.author and m.channel == ctx.channel
    try:
        answer = await bot.wait_for('message', check=check, timeout=15.0)
        if answer.content.lower() == question["answer"].lower():
            await ctx.send("Correct!")
        else:
            await ctx.send(f"Wrong! The correct answer was: {question['answer']}")
    except asyncio.TimeoutError:
        await ctx.send(f"Time's up! The correct answer was: {question['answer']}")


@bot.command()
async def help_command(ctx):
    embed = Embed(title="Bot Commands", description="Available commands:", color=discord.Color.blue())
    embed.add_field(name="!log", value="Set this channel as the logging channel.", inline=False)
    embed.add_field(name="!ban [user] [reason]", value="Ban a user.", inline=False)
    embed.add_field(name="!kick [user] [reason]", value="Kick a user.", inline=False)
    embed.add_field(name="!timeout [user] [seconds]", value="Timeout a user.", inline=False)
    embed.add_field(name="!clear [amount]", value="Clear messages.", inline=False)
    embed.add_field(name="!coinflip", value="Flip a coin.", inline=False)
    embed.add_field(name="!trivia", value="Play trivia.", inline=False)
    await ctx.send(embed=embed)

bot.run(TOKEN)






