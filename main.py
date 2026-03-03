import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Button
import os
import json
import chat_exporter
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
SUPPORT_ROLE_ID = int(os.getenv("SUPPORT_ROLE_ID"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


# ==============================
# TICKET SAYACI
# ==============================

def get_ticket_number():
    if not os.path.exists("tickets.json"):
        with open("tickets.json", "w") as f:
            json.dump({"count": 0}, f)

    with open("tickets.json", "r") as f:
        data = json.load(f)

    data["count"] += 1

    with open("tickets.json", "w") as f:
        json.dump(data, f)

    return data["count"]


# ==============================
# CLOSE BUTTON
# ==============================

class CloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔒 Ticket Kapat",
        style=discord.ButtonStyle.danger,
        custom_id="close_ticket_button"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: Button):

        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message(
                "Bu ticketi kapatamazsın.",
                ephemeral=True
            )

        log_channel = bot.get_channel(LOG_CHANNEL_ID)

        # Transcript oluştur
        transcript = await chat_exporter.export(interaction.channel)

        if transcript:
            file = discord.File(
                fp=transcript,
                filename=f"{interaction.channel.name}.html"
            )

            await log_channel.send(
                content=f"🔒 Ticket kapatıldı: {interaction.channel.name}\nKapatan: {interaction.user.mention}",
                file=file
            )
        else:
            await log_channel.send(
                f"🔒 Ticket kapatıldı: {interaction.channel.name}\nKapatan: {interaction.user.mention}\n(Transcript oluşturulamadı)"
            )

        await interaction.channel.delete()


# ==============================
# SELECT MENU
# ==============================

class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Sipariş", value="siparis"),
            discord.SelectOption(label="Destek", value="destek"),
            discord.SelectOption(label="Proje", value="proje"),
            discord.SelectOption(label="Diğer", value="diger"),
        ]

        super().__init__(
            placeholder="Kategori seç...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_select_menu"
        )

    async def callback(self, interaction: discord.Interaction):

        guild = interaction.guild
        ticket_number = get_ticket_number()

        category = discord.utils.get(guild.categories, name="TICKETS")
        if category is None:
            category = await guild.create_category("TICKETS")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.get_role(SUPPORT_ROLE_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{ticket_number}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title=f"🎫 Ticket #{ticket_number}",
            description="Destek ekibi en kısa sürede ilgilenecektir.",
            color=discord.Color.green()
        )

        await channel.send(
            content=f"{interaction.user.mention} <@&{SUPPORT_ROLE_ID}>",
            embed=embed,
            view=CloseView()
        )

        # LOG GÖNDER
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        await log_channel.send(
            f"📩 Yeni ticket açıldı: {channel.mention}\nAçan: {interaction.user.mention}\nTicket No: {ticket_number}"
        )

        await interaction.response.send_message(
            f"Ticket oluşturuldu: {channel.mention}",
            ephemeral=True
        )


# ==============================
# VIEW
# ==============================

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


# ==============================
# SLASH COMMAND PANEL
# ==============================

@tree.command(name="panel", description="Ticket paneli oluştur")
@app_commands.checks.has_permissions(administrator=True)
async def panel(interaction: discord.Interaction):

    embed = discord.Embed(
        title="📩 Destek Paneli",
        description="Aşağıdan kategori seçerek ticket açabilirsiniz.",
        color=discord.Color.blue()
    )

    await interaction.response.send_message(embed=embed, view=TicketView())


# ==============================
# READY
# ==============================

@bot.event
async def on_ready():
    await tree.sync()
    bot.add_view(TicketView())
    bot.add_view(CloseView())
    print(f"{bot.user} aktif!")


bot.run(TOKEN)
