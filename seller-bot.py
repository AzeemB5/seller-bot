import discord
import random
import string
import os
from discord.ext import commands
from flask import Flask
from threading import Thread

# ---------- Keep Alive ----------
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

# ---------- Bot Setup ----------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.dm_messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- ID Generator ----------
def generate_id(prefix: str, length: int = 8) -> str:
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return f"{prefix}{suffix}"

# ---------- In-Memory ID Store ----------
user_id_codes = {}  # Format: {user_id: "IDCODE"}

# ---------- Role Assignment Logic ----------
async def assign_role_and_dm(ctx, user_id: int, role_name: str, prefix: str):
    guild = ctx.guild
    member = guild.get_member(user_id)

    if not member:
        try:
            member = await guild.fetch_member(user_id)
        except discord.NotFound:
            await ctx.send("❌ Member not found in this server.")
            return
        except discord.Forbidden:
            await ctx.send("⚠️ Missing permissions to fetch member.")
            return

    # Create role if missing
    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        try:
            role = await guild.create_role(name=role_name)
            await ctx.send(f"🛠️ Created role `{role_name}`")
        except discord.Forbidden:
            await ctx.send("⚠️ Missing permissions to create roles.")
            return

    # Assign role
    try:
        await member.add_roles(role)
        await ctx.send(f"✅ Assigned `{role_name}` role to {member.display_name}")
    except discord.Forbidden:
        await ctx.send("⚠️ Could not assign role. Check bot permissions.")
        return

    # Generate ID and DM
    id_code = generate_id(prefix)
    user_id_codes[user_id] = id_code  # Store for lookup

    try:
        await member.send(
            f"🎉 You’ve been accepted as a **{role_name}**!\n"
            f"🔐 Your ID Portal Code: `{id_code}`"
        )
        await ctx.send(f"📨 DM sent to {member.display_name}")
    except discord.Forbidden:
        await ctx.send(f"🚫 Could not DM {member.display_name}. DMs may be disabled.")

# ---------- Accept Commands ----------
@bot.command()
@commands.has_permissions(administrator=True)
async def acceptseller(ctx, user_id: int):
    await assign_role_and_dm(ctx, user_id, "Seller", "SE")

@bot.command()
@commands.has_permissions(administrator=True)
async def acceptauthenticator(ctx, user_id: int):
    await assign_role_and_dm(ctx, user_id, "Authenticator", "AU")

@bot.command()
@commands.has_permissions(administrator=True)
async def acceptstaff(ctx, user_id: int):
    await assign_role_and_dm(ctx, user_id, "Staff", "ST")

# ---------- Admin-Only ID Lookup ----------
@bot.command()
@commands.has_permissions(administrator=True)
async def getid(ctx, user_id: int):
    id_code = user_id_codes.get(user_id)
    if id_code:
        await ctx.send(f"🔍 ID for user `{user_id}`: `{id_code}`")
    else:
        await ctx.send(f"❌ No ID code found for user `{user_id}`.")

# ---------- Keep Alive ----------
keep_alive()

# ---------- Run Bot ----------
bot.run(os.getenv("DISCORD_TOKEN"))
