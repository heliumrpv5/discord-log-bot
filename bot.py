import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Preprost lažni strežnik za Render, da ne javi Timeout napake
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_server():
    server = HTTPServer(('0.0.0.0', 10000), SimpleHandler)
    server.serve_forever()

# Zažene strežnik v ozadju, da Render "vidi" odprt port
threading.Thread(target=run_server, daemon=True).start()

import discord
from discord.ext import commands

# Nastavitev vseh pravic (Intents) za popolno sledenje
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.guilds = True
intents.voice_states = True
intents.bans = True
intents.invites = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ⚠️ TUKAJ VPIŠI ID SVOJEGA LOG KANALA (zamenjaj te številke)
LOG_CHANNEL_ID = 1533912804636102746  

@bot.event
async def on_ready():
    print(f"Prijavljen kot {bot.user} (ID: {bot.user.id})")
    print("Log bot deluje in beleži dogodke!")

# Pomožna funkcija za pošiljanje v log kanal
async def send_log(guild, embed):
    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)


# --- 1. SPOROČILA (Urejanje, Brisanje) ---

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    embed = discord.Embed(title="🗑️ Sporočilo izbrisano", color=discord.Color.red(), timestamp=discord.utils.utcnow())
    embed.add_field(name="Avtor", value=f"{message.author} ({message.author.id})", inline=True)
    embed.add_field(name="Kanal", value=message.channel.mention, inline=True)
    embed.add_field(name="Vsebina", value=message.content or "[Prazno / Priloga]", inline=False)
    await send_log(message.guild, embed)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot or before.content == after.content: return
    embed = discord.Embed(title="✏️ Sporočilo urejeno", color=discord.Color.orange(), timestamp=discord.utils.utcnow())
    embed.add_field(name="Avtor", value=f"{before.author} ({before.author.id})", inline=False)
    embed.add_field(name="Prejšnje", value=before.content or "[Prazno]", inline=False)
    embed.add_field(name="Novo", value=after.content or "[Prazno]", inline=False)
    await send_log(before.guild, embed)


# --- 2. ČLANI (Pridružitve, Odhodi, Vzdevki, Vloge) ---

@bot.event
async def on_member_join(member):
    embed = discord.Embed(title="📥 Član se je pridružil", color=discord.Color.green(), timestamp=discord.utils.utcnow())
    embed.description = f"{member.mention} ({member.name})"
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Ustvarjen račun", value=member.created_at.strftime("%d.%m.%Y ob %H:%M"), inline=False)
    await send_log(member.guild, embed)

@bot.event
async def on_member_remove(member):
    embed = discord.Embed(title="📤 Član je zapustil strežnik", color=discord.Color.dark_red(), timestamp=discord.utils.utcnow())
    embed.description = f"{member} ({member.id})"
    await send_log(member.guild, embed)

@bot.event
async def on_member_update(before, after):
    if before.nick != after.nick:
        embed = discord.Embed(title="👤 Sprememba vzdevka", color=discord.Color.blue(), timestamp=discord.utils.utcnow())
        embed.description = f"Uporabnik: {after.mention}"
        embed.add_field(name="Prejšnji vzdevek", value=before.nick or "Brez", inline=True)
        embed.add_field(name="Novi vzdevek", value=after.nick or "Brez", inline=True)
        await send_log(after.guild, embed)
        
    if before.roles != after.roles:
        added_roles = [r.name for r in after.roles if r not in before.roles]
        removed_roles = [r.name for r in before.roles if r not in after.roles]
        if added_roles or removed_roles:
            embed = discord.Embed(title="🎭 Sprememba vlog", color=discord.Color.purple(), timestamp=discord.utils.utcnow())
            embed.description = f"Uporabnik: {after.mention}"
            if added_roles: embed.add_field(name="Dodane vloge", value=", ".join(added_roles), inline=False)
            if removed_roles: embed.add_field(name="Odvzete vloge", value=", ".join(removed_roles), inline=False)
            await send_log(after.guild, embed)


# --- 3. GLASOVNI KANALI ---

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel != after.channel:
        embed = discord.Embed(title="🔊 Glasovna aktivnost", color=discord.Color.gold(), timestamp=discord.utils.utcnow())
        embed.description = f"Uporabnik: {member.mention}"
        
        if before.channel is None:
            embed.add_field(name="Dogodek", value=f"Pridružil se v kanal **{after.channel.name}**", inline=False)
        elif after.channel is None:
            embed.add_field(name="Dogodek", value=f"Zapustil kanal **{before.channel.name}**", inline=False)
        else:
            embed.add_field(name="Dogodek", value=f"Preklopil iz **{before.channel.name}** v **{after.channel.name}**", inline=False)
            
        await send_log(member.guild, embed)


# --- 4. KAZNI (Bani) ---

@bot.event
async def on_member_ban(guild, user):
    embed = discord.Embed(title="🔨 Uporabnik je bil BANAN", color=discord.Color.dark_magenta(), timestamp=discord.utils.utcnow())
    embed.description = f"Uporabnik: {user} ({user.id})"
    await send_log(guild, embed)

@bot.event
async def on_member_unban(guild, user):
    embed = discord.Embed(title="🕊️ Uporabniku je bil odstranjen ban", color=discord.Color.teal(), timestamp=discord.utils.utcnow())
    embed.description = f"Uporabnik: {user} ({user.id})"
    await send_log(guild, embed)


# --- 5. KANALI ---

@bot.event
async def on_guild_channel_create(channel):
    embed = discord.Embed(title="📁 Kanal ustvarjen", color=discord.Color.green(), timestamp=discord.utils.utcnow())
    embed.description = f"Ime: **{channel.name}** (Tip: {channel.type})"
    await send_log(channel.guild, embed)

@bot.event
async def on_guild_channel_delete(channel):
    embed = discord.Embed(title="🗑️ Kanal izbrisan", color=discord.Color.red(), timestamp=discord.utils.utcnow())
    embed.description = f"Ime: **{channel.name}**"
    await send_log(channel.guild, embed)

import os

TOKEN = os.getenv("DISCORD_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))

bot.run(TOKEN)
