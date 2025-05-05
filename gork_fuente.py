import discord
import random
import asyncio
import re  # Para expresiones regulares
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

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

        # 🆕 Responder "so" si el mensaje es o termina en "que", "qué", "pq" o "q"
        if re.fullmatch(r"(que|qué|pq|q)", content) or re.search(r"\b(que|qué|pq|q)[\s\?\.!\)]*$", message.content, re.IGNORECASE):
            await message.channel.send("so")
            return

        if content == "owo":
            await message.channel.send("uwu")
            return
        elif content == "uwu":
            await message.channel.send("owo")
            return

        # ✅ Si un usuario específico menciona al bot
        if self.user in message.mentions and message.author.id == 852636435677052978:
            await message.channel.send("Ponte a jugar P4G")
            return

        # Detectar palabra "balatro"
        if re.search(r'\bbalatro\b', message.content, re.IGNORECASE):
            imagenes_balatro = [
                "https://media.discordapp.net/attachments/1368383731731009636/1368383799347511397/20250503_100614.jpg?ex=68180639&is=6816b4b9&hm=cfd18f47d067a49f1294e752ee1258554cc2387cccee28987148695aa87c2871&=&format=webp",
                "https://media.discordapp.net/attachments/1368383731731009636/1368383817462845560/20250503_100606.jpg?ex=6818063d&is=6816b4bd&hm=6d7473660a1ac5037a5de817a85299def143a6e5a51f8e0159eb84b48da74d40&=&format=webp",
                "https://media.discordapp.net/attachments/1368383731731009636/1368383828162515006/20250503_100719.jpg?ex=6818063f&is=6816b4bf&hm=bc9ccb0cb645ecb18186b7a9c953c96313e15d3ee14597eac6d0f1b609050f20&=&format=webp&width=1245&height=722",
                "https://media.discordapp.net/attachments/1368383731731009636/1368385117449490553/20250504_022609.jpg?ex=68180773&is=6816b5f3&hm=fa2952751f31d96e0d193b797d2c048b6a1b2ca6470d6c5cab63c6339df96b13&=&format=webp&width=849&height=826",
                "https://media.discordapp.net/attachments/1368383731731009636/1368385131030646904/Screenshot_20250504_022628_Gallery.jpg?ex=68180776&is=6816b5f6&hm=3266df02d284f5d1aa751bd28d057bb5d27f29b2b6251e100698d262d0609828&=&format=webp&width=818&height=826",
                "https://media.discordapp.net/attachments/1368383731731009636/1368385142271250493/20250504_022014.jpg?ex=68180779&is=6816b5f9&hm=16a7dbf66300831cdfce318423252f7589360ab232bc68f7f98d5aac2b6f467f&=&format=webp&width=1330&height=722",
                "https://media.discordapp.net/attachments/1368383731731009636/1368385151582863460/20250504_023038.jpg?ex=6818077b&is=6816b5fb&hm=90477e2f2398a0f0a047d5bf8b0087cc2909226ecd0d5d114b65251ed1752d25&=&format=webp&width=1230&height=722",
                "https://media.discordapp.net/attachments/1368383731731009636/1368385200458825798/20250504_023108.jpg?ex=68180787&is=6816b607&hm=6178e90e83a598faa5f449c03891d41adafc64fff84e04004be8746af12f530f&=&format=webp&width=831&height=826",
                "https://media.discordapp.net/attachments/1368383731731009636/1368385556257570876/Screenshot_20250504_023349_Gallery.jpg?ex=681807db&is=6816b65b&hm=e923ba8e04708c72bc1da055d517839810fbe38eec8bda27f53c8d0379b609cb&=&format=webp&width=813&height=826",
                "https://media.discordapp.net/attachments/1368383731731009636/1368385583126151178/Screenshot_20250504_023414_Gallery.jpg?ex=681807e2&is=6816b662&hm=2ac27e3db96d10517b543d547dcd588137aaf3b93534285ae84805cf8bb22f03&=&format=webp&width=842&height=826",
                "https://media.discordapp.net/attachments/1368383731731009636/1369011421186363422/9mo488.png?ex=681a4ebd&is=6818fd3d&hm=3a9d278ba8f436af5ed433f907ce0249ee4b825f4530adafd2f050b4841f4a8e&=&format=webp&quality=lossless",
                "https://media.discordapp.net/attachments/1368383731731009636/1369012509813641426/facebook_1746458761888_7325178970824882627.png?ex=681a4fc1&is=6818fe41&hm=c7397e3026deac2ba53197bf36da2c7c780f2b258584cb970e6b96d6a4a34e8f&=&format=webp&quality=lossless",
            ]
            await message.channel.send(random.choice(imagenes_balatro))
            return

        # ✅ Comando "pls penis" con opción de mencionar a otro usuario
        if content.startswith("pls penis"):
            if message.mentions:
                target = message.mentions[0].display_name
            else:
                target = message.author.display_name

            length = random.randint(0, 15)
            penis_str = "8" + "=" * length + "D"
            await message.channel.send(f"pene de {target}:\n{penis_str}")
            return

        if self.user in message.mentions and "is this true?" in content:
            responses = ["Absolutamente.", "Ni hablar.", "Quizá"]
            await message.channel.send(random.choice(responses))

        elif self.user in message.mentions and ("grúñeme" in content or "gruñeme" in content):
            await message.channel.send("Rawr x3")

        elif self.user in message.mentions and ("diselo" in content or "díselo" in content):
            await message.channel.send("Que te importa")

    async def send_random_message(self):
        await self.wait_until_ready()
        channel = discord.utils.get(self.get_all_channels(), name="general")

        mensajes_random = [
            "penesito",
            "yeah un pene waffle uwu",
            "chupala zau",
            "chupala walter",
            "el lucas es puto",
            "tu culo"
        ]

        while not self.is_closed():
            await asyncio.sleep(600)
            if random.random() < 0.02 and channel:
                await channel.send(random.choice(mensajes_random))


@discord.app_commands.command(name="ping", description="Responde con Pong!")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!", ephemeral=True)

@discord.app_commands.command(name="coinflip", description="Lanza una moneda.")
async def coinflip(interaction: discord.Interaction):
    resultado = random.choice(["Cara", "Cruz"])
    await interaction.response.send_message(f"🪙 ¡Salió **{resultado}**!")

client = GorkClient(intents=intents)
client.run(os.getenv("DISCORD_TOKEN"))
