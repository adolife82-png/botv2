import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID"))
WELCOME_CHANNEL_ID = 1478713946813890730

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ------------------------------------------------
# BOT HAZIR OLUNCA SES KANALINA GİRER
# ------------------------------------------------

@bot.event
async def on_ready():

    print(f"{bot.user} aktif.")

    channel = bot.get_channel(VOICE_CHANNEL_ID)

    if channel is None:
        print("Ses kanalı bulunamadı.")
        return

    try:

        if not channel.guild.voice_client:
            vc = await channel.connect()
            await channel.guild.change_voice_state(channel=channel, self_mute=True)
            print("Bot ses kanalına girdi.")

    except Exception as e:
        print("Ses hatası:", e)

    await bot.tree.sync()

# ------------------------------------------------
# CLEAR
# ------------------------------------------------

@bot.tree.command(name="clear", description="Mesaj siler")
async def clear(interaction: discord.Interaction, amount: int):

    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("Yetkin yok.", ephemeral=True)
        return

    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"{amount} mesaj silindi.", ephemeral=True)

# ------------------------------------------------
# BAN
# ------------------------------------------------

@bot.tree.command(name="ban", description="Kullanıcı banlar")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "Sebep yok"):

    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("Yetkin yok.", ephemeral=True)
        return

    await user.ban(reason=reason)
    await interaction.response.send_message(f"{user} banlandı.")

# ------------------------------------------------
# UNBAN
# ------------------------------------------------

@bot.tree.command(name="unban", description="Ban kaldırır")
async def unban(interaction: discord.Interaction, user_id: str):

    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("Yetkin yok.", ephemeral=True)
        return

    user = await bot.fetch_user(int(user_id))
    await interaction.guild.unban(user)

    await interaction.response.send_message("Ban kaldırıldı.")

# ------------------------------------------------
# KICK
# ------------------------------------------------

@bot.tree.command(name="kick", description="Kullanıcı atar")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "Sebep yok"):

    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("Yetkin yok.", ephemeral=True)
        return

    await user.kick(reason=reason)
    await interaction.response.send_message(f"{user} atıldı.")

# ------------------------------------------------
# MUTE
# ------------------------------------------------

@bot.tree.command(name="mute", description="Süreli mute")
async def mute(interaction: discord.Interaction, user: discord.Member, süre: str):

    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("Yetkin yok.", ephemeral=True)
        return

    units = {"m":60, "h":3600, "d":86400}

    try:

        number = int(süre[:-1])
        unit = süre[-1]

        seconds = number * units[unit]

    except:
        await interaction.response.send_message("Örnek kullanım: 10m / 1h / 1d")
        return

    await user.timeout(timedelta(seconds=seconds))

    await interaction.response.send_message(
        f"{user.mention} {süre} süreyle mute aldı."
    )

# ------------------------------------------------
# UNMUTE
# ------------------------------------------------

@bot.tree.command(name="unmute", description="Mute kaldırır")
async def unmute(interaction: discord.Interaction, user: discord.Member):

    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("Yetkin yok.", ephemeral=True)
        return

    await user.timeout(None)

    await interaction.response.send_message(
        f"{user.mention} unmute edildi."
    )

# ------------------------------------------------
# HOŞ GELDİN
# ------------------------------------------------

@bot.event
async def on_member_join(member):

    channel = bot.get_channel(WELCOME_CHANNEL_ID)

    embed = discord.Embed(
        title=f"👋 Hoş geldin {member.name}",
        description="**Ares Projects** ailesine katıldığın için mutluyuz!",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="🌐 Hizmetlerimiz",
        value="""
• Web sitesi yazılımı
• E-ticaret sistemleri
• Discord bot geliştirme
• Plugin paketleri
""",
        inline=False
    )

    embed.add_field(
        name="🚀 Deneyim",
        value="10+ yıl tecrübe • 200+ sunucu • 3000+ sipariş",
        inline=False
    )

    await channel.send(f"{member.mention} aramıza katıldı!", embed=embed)

    try:
        await member.send(
            f"👋 Hoş geldin **{member.name}**!\nAres Projects sunucusuna katıldığın için teşekkürler."
        )
    except:
        pass

bot.run(TOKEN)
