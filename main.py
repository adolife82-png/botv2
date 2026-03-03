import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))
SUPPORT_ROLE_ID = int(os.getenv("SUPPORT_ROLE_ID"))

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


# ------------------ TICKET KAPAT BUTONU ------------------

class CloseButton(Button):
    def __init__(self):
        super().__init__(
            label="🔒 Ticket Kapat",
            style=discord.ButtonStyle.danger,
            custom_id="close_ticket"
        )

    async def callback(self, interaction: discord.Interaction):
        log_channel = bot.get_channel(LOG_CHANNEL_ID)

        await log_channel.send(
            f"🔒 Ticket kapatıldı: {interaction.channel.name}\nKapatan: {interaction.user}"
        )

        await interaction.channel.delete()


class CloseView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CloseButton())


# ------------------ PANEL BUTONU ------------------

class OpenTicketButton(Button):
    def __init__(self):
        super().__init__(
            label="🎫 Ticket Aç",
            style=discord.ButtonStyle.primary,
            custom_id="open_ticket"
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
            title="🎫 Atlas Project Destek",
            description=f"{interaction.user.mention} talebiniz oluşturuldu.\n\nYetkili ekip en kısa sürede ilgilenecektir.",
            color=discord.Color.blue()
        )

        await channel.send(
            content=f"<@&{SUPPORT_ROLE_ID}>",
            embed=embed,
            view=CloseView()
        )

        await log_channel.send(
            f"📩 Yeni ticket açıldı: {channel.mention}\nAçan: {interaction.user}"
        )

        await interaction.response.send_message(
            f"Ticket oluşturuldu: {channel.mention}",
            ephemeral=True
        )


class PanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(OpenTicketButton())


# ------------------ SLASH PANEL KOMUTU ------------------

@bot.tree.command(name="panel", description="Ticket paneli oluştur")
async def panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎫 Atlas Project Destek Sistemi",
        description="Destek almak için aşağıdaki butona tıklayın.",
        color=discord.Color.blue()
    )

    await interaction.response.send_message(embed=embed, view=PanelView())


# ------------------ TICKET MESAJ LOG ------------------

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if message.channel.name.startswith("ticket-"):

        log_channel = bot.get_channel(LOG_CHANNEL_ID)

        embed = discord.Embed(
            title="📨 Ticket Mesaj Log",
            description=f"Kanal: {message.channel.name}",
            color=discord.Color.green()
        )

        embed.add_field(name="Gönderen", value=str(message.author), inline=False)
        embed.add_field(name="Mesaj", value=message.content or "Dosya / Embed", inline=False)

        await log_channel.send(embed=embed)

    await bot.process_commands(message)


# ------------------ READY ------------------

@bot.event
async def on_ready():
    await bot.tree.sync()
    bot.add_view(PanelView())
    bot.add_view(CloseView())
    print(f"{bot.user} aktif.")


bot.run(TOKEN)
