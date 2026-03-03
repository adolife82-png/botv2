import discord
from discord.ext import commands
from discord.ui import View, Select
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


# =========================
# TICKET SELECT
# =========================

class TicketSelect(discord.ui.Select):
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
            custom_id="persistent_ticket_select"  # ZORUNLU
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild

        category = discord.utils.get(guild.categories, name="TICKETS")
        if category is None:
            category = await guild.create_category("TICKETS")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        await channel.send(
            f"{interaction.user.mention} Ticket oluşturuldu."
        )

        await interaction.response.send_message(
            f"Ticket açıldı: {channel.mention}",
            ephemeral=True
        )


# =========================
# PERSISTENT VIEW
# =========================

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)  # ZORUNLU
        self.add_item(TicketSelect())


# =========================
# KOMUT
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def panel(ctx):
    embed = discord.Embed(
        title="📩 Destek Paneli",
        description="Aşağıdan kategori seçerek ticket açabilirsiniz.",
        color=discord.Color.blue()
    )

    await ctx.send(embed=embed, view=TicketView())


# =========================
# READY
# =========================

@bot.event
async def on_ready():
    bot.add_view(TicketView())  # artık hata vermeyecek
    print(f"{bot.user} aktif!")


bot.run(TOKEN)
