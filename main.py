import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# =========================
# Ticket Oluşturma Sistemi
# =========================

class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Sipariş", description="Yeni sipariş vermek istiyorum"),
            discord.SelectOption(label="Destek", description="Bir sorunum var"),
            discord.SelectOption(label="Proje İsteği", description="Özel proje talebi"),
            discord.SelectOption(label="Ücretsiz Proje", description="Ücretsiz proje bilgisi"),
            discord.SelectOption(label="Diğer", description="Diğer konular"),
        ]

        super().__init__(placeholder="Bir kategori seç...", options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        category_name = "TICKETS"

        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)

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
            f"{interaction.user.mention} Talebiniz oluşturuldu.\n"
            "Yetkili ekip en kısa sürede ilgilenecektir."
        )

        await interaction.response.send_message(
            f"Ticket oluşturuldu: {channel.mention}",
            ephemeral=True
        )


class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


@bot.command()
@commands.has_permissions(administrator=True)
async def ticketpanel(ctx):
    embed = discord.Embed(
        title="📩 Destek Merkezi",
        description="Aşağıdan kategori seçerek ticket oluşturabilirsiniz.\n\nGereksiz ticket açmayınız.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=TicketView())


# =========================
# Ticket Kapatma Butonu
# =========================

class CloseButton(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ticket Kapat", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: Button):
        await interaction.channel.delete()


@bot.event
async def on_ready():
    bot.add_view(TicketView())
    bot.add_view(CloseButton())
    print(f"{bot.user} aktif!")


bot.run(TOKEN)
