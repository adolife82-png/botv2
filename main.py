import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Button
import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

TOKEN = os.getenv("TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))
SUPPORT_ROLE_ID = int(os.getenv("SUPPORT_ROLE_ID"))
VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID"))
WELCOME_CHANNEL_ID = 1478713946813890730  # Hoşgeldin Kanalı

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ==================================================
# SES KANALINA OTOMATİK GİRME
# ==================================================

async def connect_voice():
    await bot.wait_until_ready()

    channel = bot.get_channel(VOICE_CHANNEL_ID)

    if not channel:
        print("Ses kanalı bulunamadı.")
        return

    try:
        if not discord.utils.get(bot.voice_clients, guild=channel.guild):
            await channel.connect(self_mute=True)
            print("Ses kanalına bağlandı (mikrofon kapalı).")
    except Exception as e:
        print(f"Ses bağlantı hatası: {e}")

# ==================================================
#                   TICKET SİSTEMİ
# ==================================================

class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Sipariş", emoji="🛒", value="siparis"),
            discord.SelectOption(label="Destek", emoji="🛠️", value="destek"),
            discord.SelectOption(label="Proje İsteği", emoji="⭐", value="proje"),
            discord.SelectOption(label="Ücretsiz Proje", emoji="🎁", value="ucretsiz"),
            discord.SelectOption(label="Diğer", emoji="❓", value="diger"),
        ]

        super().__init__(
            placeholder="Bir kategori seç...",
            options=options,
            custom_id="ticket_select",
        )

    async def callback(self, interaction: discord.Interaction):

        guild = interaction.guild
        log_channel = bot.get_channel(LOG_CHANNEL_ID)

        category = discord.utils.get(guild.categories, name="TICKETS")
        if not category:
            category = await guild.create_category("TICKETS")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.get_role(SUPPORT_ROLE_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="📩 Ares Projects - Destek Merkezi",
            description=f"{interaction.user.mention} talebiniz oluşturuldu.",
            color=discord.Color.blue()
        )

        await channel.send(
            content=f"<@&{SUPPORT_ROLE_ID}>",
            embed=embed,
            view=CloseView()
        )

        await log_channel.send(f"📨 Yeni Ticket: {channel.mention} | Açan: {interaction.user}")

        await interaction.response.send_message(
            f"Ticket oluşturuldu: {channel.mention}",
            ephemeral=True
        )


class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


class CloseButton(Button):
    def __init__(self):
        super().__init__(
            label="🔒 Ticket Kapat",
            style=discord.ButtonStyle.danger,
            custom_id="close_ticket"
        )

    async def callback(self, interaction: discord.Interaction):
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        await log_channel.send(f"🔒 Ticket kapatıldı: {interaction.channel.name}")
        await interaction.channel.delete()


class CloseView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CloseButton())


@bot.tree.command(name="panel", description="Destek panelini oluşturur")
async def panel(interaction: discord.Interaction):

    embed = discord.Embed(
        title="📨 Ares Projects - Destek Merkezi",
        description=(
            "**Destek Merkezi Hakkında**\n"
            "Aşağıdan kategori seçerek ticket oluşturabilirsiniz.\n\n"
            "⚠ Gereksiz ticket açmayınız.\n\n"
            "Ares Projects © 2026"
        ),
        color=discord.Color.dark_blue()
    )

    await interaction.response.send_message(embed=embed, view=TicketView())


# ==================================================
# MODERASYON KOMUTLARI (BAN, KICK, CLEAR, MUTE, UNMUTE)
# ==================================================

@bot.tree.command(name="clear", description="Mesaj siler")
@app_commands.describe(miktar="Silinecek mesaj sayısı")
async def clear(interaction: discord.Interaction, miktar: int):

    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message("Yetkin yok.", ephemeral=True)

    await interaction.channel.purge(limit=miktar)
    await interaction.response.send_message(f"{miktar} mesaj silindi.", ephemeral=True)


@bot.tree.command(name="ban", description="Kullanıcıyı banlar")
async def ban(interaction: discord.Interaction, user: discord.Member, sebep: str = "Sebep belirtilmedi"):

    if not interaction.user.guild_permissions.ban_members:
        return await interaction.response.send_message("Yetkin yok.", ephemeral=True)

    await user.ban(reason=sebep)
    await interaction.response.send_message(f"{user} banlandı.")


@bot.tree.command(name="kick", description="Kullanıcıyı atar")
async def kick(interaction: discord.Interaction, user: discord.Member, sebep: str = "Sebep belirtilmedi"):

    if not interaction.user.guild_permissions.kick_members:
        return await interaction.response.send_message("Yetkin yok.", ephemeral=True)

    await user.kick(reason=sebep)
    await interaction.response.send_message(f"{user} atıldı.")


@bot.tree.command(name="mute", description="Kullanıcıyı süreli susturur")
@app_commands.describe(sure="Süre (örn: 10m, 1h, 2d)")
async def mute(interaction: discord.Interaction, user: discord.Member, sure: str):

    await interaction.response.defer()

    if not interaction.user.guild_permissions.moderate_members:
        return await interaction.followup.send("Yetkin yok.")

    time_units = {"m": 60, "h": 3600, "d": 86400}

    try:
        amount = int(sure[:-1])
        unit = sure[-1]
        seconds = amount * time_units[unit]
        duration = timedelta(seconds=seconds)
    except:
        return await interaction.followup.send("Format yanlış. Örnek: 10m, 1h, 2d")

    await user.timeout(duration)
    await interaction.followup.send(f"{user.mention} {sure} süreyle timeout aldı.")


@bot.tree.command(name="unmute", description="Timeout kaldırır")
async def unmute(interaction: discord.Interaction, user: discord.Member):

    await interaction.response.defer()

    if not interaction.user.guild_permissions.moderate_members:
        return await interaction.followup.send("Yetkin yok.")

    await user.timeout(None)
    await interaction.followup.send(f"{user.mention} timeout kaldırıldı.")


# ==================================================
# HOŞ GELDİN MESAJI (DM ve Kanal)
# ==================================================

@bot.event
async def on_member_join(member: discord.Member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)

    # Kanalda hoş geldin mesajı
    embed = discord.Embed(
        title=f"Hoş geldin, {member.name}!",
        description="Ares Projects ailesine katıldığın için mutluyuz.",
        color=discord.Color.green()
    )
    embed.add_field(name="Hizmetlerimiz", value="• Web sitesi yazılımı & geliştirme\n• E-ticaret sistemleri\n• Özel Discord bot geliştirme\n• Plugin & Plugin Paketleri")
    embed.add_field(name="Deneyim", value="10+ yıl tecrübe • 200+ sunucu • 3000+ sipariş", inline=False)

    await channel.send(embed=embed)

    # Kullanıcıya DM ile hoş geldin mesajı
    try:
        await member.send(
            f"Hoş geldin {member.name}!\nAres Projects ailesine katıldığın için mutluyuz. Hemen yukarıdaki kanalımızda sohbet başlatabilirsin. İyi sohbetler!"
        )
    except discord.Forbidden:
        print(f"{member.name} DM mesajı engellenmiş.")

# ==================================================

@bot.event
async def on_ready():
    await bot.tree.sync()
    bot.add_view(TicketView())
    bot.add_view(CloseView())
    bot.loop.create_task(connect_voice())
    print(f"{bot.user} aktif.")


bot.run(TOKEN)
