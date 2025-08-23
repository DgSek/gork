import discord
import random
import asyncio
import re
import os
from dotenv import load_dotenv

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True

# ==========================
# Cliente del bot
# ==========================
class GorkClient(discord.Client):
    def __init__(self, *, intents):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.add_command(ping)
        self.tree.add_command(coinflip)
        await self.tree.sync()
        self.bg_task = self.loop.create_task(self.send_random_message())

    async def on_ready(self):
        print(f'✅ Bot conectado como {self.user}')

    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.strip().lower()

        # ==========================
        # Respuestas de texto simples
        # ==========================
        if re.fullmatch(r"(q(u|ú)(e|é)+|pq|q+)", content, re.IGNORECASE) \
            or re.search(r"(q(u|ú)(e|é)+)\s*[\?\¿]?$", content, re.IGNORECASE):
            await message.channel.send("so")
            return

        if re.fullmatch(r"k(h)?(e|é)?", content, re.IGNORECASE):
            await message.channel.send("zo")
            return

        if content == "owo":
            await message.channel.send("uwu")
            return
        elif content == "uwu":
            await message.channel.send("owo")
            return

        # ==========================
        # Mentions y respuestas personalizadas
        # ==========================
        if self.user in message.mentions:
            if message.author.id == 852636435677052978 and random.randint(1, 20) == 1:
                await message.channel.send("Ponte a jugar P4G")
                return

            if "is this true?" in content:
                await message.channel.send(random.choice(["Absolutamente.", "Ni hablar.", "Quizá"]))
                return

            if "grúñeme" in content or "gruñeme" in content:
                await message.channel.send("Rawr x3")
                return

            if "diselo" in content or "díselo" in content:
                await message.channel.send("Que te importa")
                return

            if "un repo?" in content:
                await message.channel.send("Cállate")
                return

        # ==========================
        # Imágenes específicas
        # ==========================
        if re.search(r'\bbalatro\b', message.content, re.IGNORECASE):
            imagenes_balatro = [
                "https://media.discordapp.net/attachments/1368383731731009636/1368383799347511397/20250503_100614.jpg",
                "https://media.discordapp.net/attachments/1368383731731009636/1368383817462845560/20250503_100606.jpg",
                "https://media.discordapp.net/attachments/1368383731731009636/1368383828162515006/20250503_100719.jpg",
                "https://cdn.discordapp.com/attachments/1368383731731009636/1368385117449490553/20250504_022609.jpg",
                "https://media.discordapp.net/attachments/1368383731731009636/1368385131030646904/Screenshot_20250504_022628_Gallery.jpg",
                "https://media.discordapp.net/attachments/1368383731731009636/1368385142271250493/20250504_022014.jpg",
                "https://media.discordapp.net/attachments/1368383731731009636/1368385151582863460/20250504_023038.jpg",
                "https://media.discordapp.net/attachments/1368383731731009636/1368385200458825798/20250504_023108.jpg",
                "https://media.discordapp.net/attachments/1368383731731009636/1368385556257570876/Screenshot_20250504_023349_Gallery.jpg",
                "https://media.discordapp.net/attachments/1368383731731009636/1368385583126151178/Screenshot_20250504_023414_Gallery.jpg",
                "https://media.discordapp.net/attachments/1368383731731009636/1369011421186363422/9mo488.png",
                "https://media.discordapp.net/attachments/1368383731731009636/1369012509813641426/facebook_1746458761888_7325178970824882627.png",
                "https://media.discordapp.net/attachments/1368383731731009636/1369045626582601728/ZTc1OTIw.png",
                "https://media.discordapp.net/attachments/1368383731731009636/1373467789464961124/GrJ-_ZUWUAAF7TS.png",
                "https://media.discordapp.net/attachments/1368383731731009636/1373467828975566868/GrKLckuW8AAthAK.png",
                "https://media.discordapp.net/attachments/1368383731731009636/1373467879122407474/GrKXXbJWAAAJwzj.png",
                "https://media.discordapp.net/attachments/1368383731731009636/1373467953260925080/498281336_4066399776977681_3756171527715474276_n.png",
            ]
            await message.channel.send(random.choice(imagenes_balatro))
            return

        if content.lower().startswith("argentino"):
            imagen_argentino = [
                "https://media.discordapp.net/attachments/1368383731731009636/1394860064480821248/image.png"
            ]
            await message.channel.send(random.choice(imagen_argentino))
            return

        if content.startswith("pls penis"):
            target = message.mentions[0].display_name if message.mentions else message.author.display_name
            length = random.randint(0, 15)
            penis_str = "8" + "=" * length + "D"
            await message.channel.send(f"pene de {target}:\n{penis_str}")
            return

    # ==========================
    # Mensajes aleatorios periódicos
    # ==========================
    async def send_random_message(self):
        await self.wait_until_ready()
        channel = discord.utils.get(self.get_all_channels(), name="general")
        mensajes_random = [
            "penesito", "yeah un pene waffle uwu", "chupala zau",
            "chupala walter", "el lucas es puto", "tu culo", "he comprao leche xD"
        ]
        while not self.is_closed():
            await asyncio.sleep(600)
            if random.random() < 0.02 and channel:
                await channel.send(random.choice(mensajes_random))

# ==========================
# Slash commands
# ==========================
@discord.app_commands.command(name="ping", description="Responde con Pong!")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!", ephemeral=True)

@discord.app_commands.command(name="coinflip", description="Lanza una moneda.")
async def coinflip(interaction: discord.Interaction):
    resultado = random.choice(["Cara", "Cruz"])
    await interaction.response.send_message(f"🪙 ¡Salió **{resultado}**!")

# ==========================
# Ejecución
# ==========================
client = GorkClient(intents=intents)
client.run(os.getenv("DISCORD_TOKEN"))
