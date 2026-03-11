import discord
from discord.ext import commands
from discord.ui import View, Select, Button
from datetime import timedelta
import os

TOKEN = os.getenv("TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))
SUPPORT_ROLE_ID = int(os.getenv("SUPPORT_ROLE_ID"))
VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID"))

WELCOME_CHANNEL_ID = 1478713946813890730

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ======================
# READY
# ======================

@bot.event
async def on_ready():

    print(f"{bot.user} aktif")

    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} slash komut senkronize edildi")
    except Exception as e:
        print(e)

    bot.loop.create_task(join_voice())

# ======================
# SES KANALINA GİRME
# ======================

async def join_voice():

    await bot.wait_until_ready()

    channel = bot.get_channel(VOICE_CHANNEL_ID)

    if channel:

        try:

            if not channel.guild.voice_client:
                vc = await channel.connect()
                await channel.guild.change_voice_state(channel=channel, self_mute=True)
                print("Ses kanalına bağlandı")

        except Exception as e:
            print("Ses hatası:", e)

# ======================
# HOŞ GELDİN
# ======================

@bot.event
async def on_member_join(member):

    channel = bot.get_channel(WELCOME_CHANNEL_ID)

    embed = discord.Embed(
        title=f"👋 Hoş geldin {member.name}",
        description="**Ares Projects ailesine katıldığın için mutluyuz!**",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="🌐 Hizmetlerimiz",
        value="""
• Web sitesi geliştirme
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

# ======================
# TICKET SELECT
# ======================

class TicketSelect(Select):

    def __init__(self):

        options = [
            discord.SelectOption(label="Sipariş", emoji="🛒", value="siparis"),
            discord.SelectOption(label="Destek", emoji="🛠️", value="destek"),
            discord.SelectOption(label="Proje", emoji="⭐", value="proje"),
            discord.SelectOption(label="Ücretsiz Proje", emoji="🎁", value="free"),
            discord.SelectOption(label="Diğer", emoji="❓", value="other"),
        ]

        super().__init__(
            placeholder="Bir kategori seç",
            options=options,
            custom_id="ticket_select"
        )

    async def callback(self, interaction: discord.Interaction):

        guild = interaction.guild
        user = interaction.user

        # açık ticket kontrol
        for channel in guild.text_channels:
            if channel.name == f"ticket-{user.name}":
                return await interaction.response.send_message(
                    f"Zaten açık bir ticketın var: {channel.mention}",
                    ephemeral=True
                )

        category = discord.utils.get(guild.categories, name="TICKETS")

        if not category:
            category = await guild.create_category("TICKETS")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.get_role(SUPPORT_ROLE_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="📩 Ares Projects Destek",
            description=f"{user.mention} ticket oluşturuldu.",
            color=discord.Color.green()
        )

        await channel.send(
            content=f"<@&{SUPPORT_ROLE_ID}>",
            embed=embed,
            view=CloseView()
        )

        log = bot.get_channel(LOG_CHANNEL_ID)

        if log:
            await log.send(f"🎫 Ticket açıldı: {channel.mention}")

        await interaction.response.send_message(
            f"Ticket oluşturuldu: {channel.mention}",
            ephemeral=True
        )

class TicketView(View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

# ======================
# TICKET KAPAT
# ======================

class CloseButton(Button):

    def __init__(self):

        super().__init__(
            label="Ticket Kapat",
            style=discord.ButtonStyle.red
        )

    async def callback(self, interaction: discord.Interaction):

        log = bot.get_channel(LOG_CHANNEL_ID)

        if log:
            await log.send(f"🔒 Ticket kapandı: {interaction.channel.name}")

        await interaction.channel.delete()

class CloseView(View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CloseButton())

# ======================
# PANEL
# ======================

@bot.tree.command(name="panel", description="Ticket paneli oluşturur")
async def panel(interaction: discord.Interaction):

    embed = discord.Embed(
        title="📨 Ares Projects Destek Merkezi",
        description="Kategori seçerek ticket açabilirsiniz.",
        color=discord.Color.blue()
    )

    await interaction.response.send_message(
        embed=embed,
        view=TicketView()
    )

# ======================
# CLEAR
# ======================

@bot.tree.command(name="clear")
async def clear(interaction: discord.Interaction, amount: int):

    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message("Yetkin yok", ephemeral=True)

    await interaction.channel.purge(limit=amount)

    await interaction.response.send_message(
        f"{amount} mesaj silindi",
        ephemeral=True
    )

# ======================
# BAN
# ======================

@bot.tree.command(name="ban")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str="Sebep yok"):

    if not interaction.user.guild_permissions.ban_members:
        return await interaction.response.send_message("Yetkin yok", ephemeral=True)

    await user.ban(reason=reason)

    await interaction.response.send_message(f"{user} banlandı")

# ======================
# UNBAN
# ======================

@bot.tree.command(name="unban")
async def unban(interaction: discord.Interation, userid: str):

    if not interaction.user.guild_permissions.ban_members:
        return await interaction.response.send_message("Yetkin yok", ephemeral=True)

    user = await bot.fetch_user(int(userid))

    await interaction.guild.unban(user)

    await interaction.response.send_message("Ban kaldırıldı")

# ======================
# KICK
# ======================

@bot.tree.command(name="kick")
async def kick(interaction: discord.Interaction, user: discord.Member):

    if not interaction.user.guild_permissions.kick_members:
        return await interaction.response.send_message("Yetkin yok", ephemeral=True)

    await user.kick()

    await interaction.response.send_message(f"{user} atıldı")

# ======================
# MUTE
# ======================

@bot.tree.command(name="mute")
async def mute(interaction: discord.Interaction, user: discord.Member, sure: str):

    units = {"m":60,"h":3600,"d":86400}

    try:
        num=int(sure[:-1])
        unit=sure[-1]
        seconds=num*units[unit]
    except:
        return await interaction.response.send_message("Örnek kullanım: 10m 1h 1d")

    await user.timeout(timedelta(seconds=seconds))

    await interaction.response.send_message(
        f"{user.mention} {sure} susturuldu"
    )

# ======================
# UNMUTE
# ======================

@bot.tree.command(name="unmute")
async def unmute(interaction: discord.Interaction, user: discord.Member):

    await user.timeout(None)

    await interaction.response.send_message("Mute kaldırıldı")

bot.run(TOKEN)
