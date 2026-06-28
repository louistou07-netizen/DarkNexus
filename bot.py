import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os

# ─────────────────────────────────────────────
#  Token lu depuis la variable d'environnement
# ─────────────────────────────────────────────
TOKEN = os.getenv("DISCORD_TOKEN")

# ─────────────────────────────────────────────
#  Intents
# ─────────────────────────────────────────────
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user} (ID: {bot.user.id})")
    try:
        synced = await tree.sync()
        print(f"✅ {len(synced)} commande(s) synchronisée(s)")
    except Exception as e:
        print(f"❌ Erreur de synchronisation : {e}")


@tree.command(
    name="ban-all",
    description="Bannis tous les membres du serveur courant (sauf toi et les bots).",
)
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
@app_commands.describe(
    raison="Raison du ban (optionnelle)",
    confirmation="Tape 'CONFIRMER' pour valider l'action",
)
async def ban_all(
    interaction: discord.Interaction,
    confirmation: str,
    raison: str = "Ban massif via /ban-all",
):
    if confirmation != "CONFIRMER":
        await interaction.response.send_message(
            "❌ Action annulée. Tu dois écrire exactement `CONFIRMER` dans le champ confirmation.",
            ephemeral=True,
        )
        return

    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "❌ Cette commande doit être utilisée dans un serveur.",
            ephemeral=True,
        )
        return

    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message(
            "❌ Tu n'as pas la permission de bannir des membres.",
            ephemeral=True,
        )
        return

    if not guild.me.guild_permissions.ban_members:
        await interaction.response.send_message(
            "❌ Le bot n'a pas la permission de bannir des membres.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)

    members = [
        m for m in guild.members
        if m.id != interaction.user.id
        and not m.bot
        and m.id != bot.user.id
        and guild.me.top_role > m.top_role
    ]

    total = len(members)
    banni = 0
    echec = 0
    echecs_liste = []

    for member in members:
        try:
            await guild.ban(member, reason=raison, delete_message_days=0)
            banni += 1
            await asyncio.sleep(0.5)
        except discord.Forbidden:
            echec += 1
            echecs_liste.append(f"`{member}` — permissions insuffisantes")
        except discord.HTTPException as e:
            echec += 1
            echecs_liste.append(f"`{member}` — {e}")

    rapport = (
        f"✅ **Ban massif terminé !**\n"
        f"• Membres ciblés : **{total}**\n"
        f"• Bannis avec succès : **{banni}**\n"
        f"• Échecs : **{echec}**\n"
        f"• Raison : `{raison}`"
    )

    if echecs_liste:
        rapport += "\n\n**Échecs détaillés :**\n" + "\n".join(echecs_liste[:10])
        if len(echecs_liste) > 10:
            rapport += f"\n... et {len(echecs_liste) - 10} autre(s)"

    await interaction.followup.send(rapport, ephemeral=True)


bot.run(TOKEN)
