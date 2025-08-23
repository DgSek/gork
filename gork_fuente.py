import discord
import random
import asyncio
import re
import os
import aiohttp
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

# ==========================
# Tags de bloqueo globales (IA y menores)
# ==========================
BLOCKED_TAGS = [
    "-ai_generated", "-ai", "-ai_art",
    "-loli", "-shota", "-young", "-teen", "-child", "-underage", "-kid", "-baby", "-toddler"
]

# ==========================
# Funciones auxiliares para usar API de rule34
# ==========================
async def get_total_results(tags):
    """
    Devuelve el total de resultados para los tags dados (usa API XML).
    """
    # Combinar con bloqueos globales si no están ya
    all_tags = list(tags) + [t for t in BLOCKED_TAGS if t not in tags]
    url = f"https://rule34.xxx/index.php?page=dapi&s=post&q=index&tags={'+'.join(all_tags)}&limit=1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            text = await resp.text()
            match = re.search(r'count="(\d+)"', text)
            if match:
                return int(match.group(1))
    return 0


async def fetch_results(tags, page, limit=100):
    """
    Descarga resultados de rule34.xxx en XML y los convierte en dicts.
    page (pid) es 0-based.
    """
    all_tags = list(tags) + [t for t in BLOCKED_TAGS if t not in tags]
    url = f"https://rule34.xxx/index.php?page=dapi&s=post&q=index&tags={'+'.join(all_tags)}&pid={page}&limit={limit}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            text = await resp.text()
            # Si el XML viniera vacío o mal, evitamos crash
            try:
                root = ET.fromstring(text)
            except ET.ParseError:
                return []
            posts = []
            for post in root.findall("post"):
                posts.append({
                    "id": post.attrib.get("id"),
                    "file_url": post.attrib.get("file_url"),
                    "sample_url": post.attrib.get("sample_url"),
                    "preview_url": post.attrib.get("preview_url"),
                    "tags": post.attrib.get("tags", "").split(),
                })
            return posts


async def get_random_post(tags):
    """
    Obtiene un post aleatorio completamente entre todos los resultados disponibles.
    Intenta hasta 5 páginas aleatorias.
    """
    total_results = await get_total_results(tags)
    if total_results == 0:
        return None

    # pid es 0-based; 100 items por página
    total_pages = max(1, (total_results - 1) // 100 + 1)

    for _ in range(5):  # 5 intentos -> 5 páginas aleatorias
        random_page = random.randint(0, total_pages - 1)
        results = await fetch_results(tags, random_page, limit=100)
        if results:
            return random.choice(results)
    return None


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
        # Comando ¿r34 <busqueda>  (carrusel, hasta 100 imgs)
        # ==========================
        if content.startswith("¿r34 "):
            if not isinstance(message.channel, discord.TextChannel) or not message.channel.is_nsfw():
                return  # Solo funciona en canales NSFW

            query = message.content.strip()[4:]  # conservar mayús/acentos tras "¿r34 "
            # Construir tags desde la query y sumar bloqueos
            # (no toco la query del usuario; solo añado bloqueos globales)
            base_tags = query.split()
            tags = base_tags  # los bloqueos se agregan dentro de fetch/get_total

            try:
                # Buscar hasta 100 imágenes (5 páginas de 20) — mismo comportamiento que tenías
                results = []
                for page in range(0, 5):  # pid 0..4
                    page_results = await fetch_results(tags, page, limit=20)
                    if not page_results:
                        # si una página vacía aparece, seguimos intentando las demás
                        continue
                    results.extend(page_results)

                if not results:
                    await message.channel.send("No encontré resultados.")
                    return

                # Helpers para el carrusel
                def get_image_url(post):
                    return post.get("file_url") or post.get("sample_url") or post.get("preview_url")

                def get_post_url(post):
                    return f"https://rule34.xxx/index.php?page=post&s=view&id={post.get('id')}"

                # ==========================
                # Vista con botones para carrusel de imágenes
                # ==========================
                class R34View(discord.ui.View):
                    def __init__(self, posts):
                        super().__init__(timeout=300)  # Expira en 5 minutos
                        self.posts = posts
                        self.index = 0

                    def current_embed(self):
                        post = self.posts[self.index]
                        image_url = get_image_url(post)
                        post_url = get_post_url(post)

                        # acotar lista de tags para no saturar
                        shown_tags = post['tags'][:10]
                        embed = discord.Embed(
                            title=f"Resultado {self.index + 1}/{len(self.posts)}",
                            url=post_url,
                            description=f"**Tags:** {', '.join(shown_tags)}" + ("..." if len(post['tags']) > 10 else "")
                        )
                        if image_url:
                            embed.set_image(url=image_url)
                        else:
                            embed.description += "\n(No se encontró imagen disponible)"
                        return embed

                    async def update_message(self, interaction: discord.Interaction):
                        await interaction.response.edit_message(embed=self.current_embed(), view=self)

                    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
                    async def left(self, interaction: discord.Interaction, button: discord.ui.Button):
                        self.index = (self.index - 1) % len(self.posts)
                        await self.update_message(interaction)

                    @discord.ui.button(label="🎲", style=discord.ButtonStyle.primary)
                    async def random_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                        new_index = self.index
                        while new_index == self.index and len(self.posts) > 1:
                            new_index = random.randint(0, len(self.posts) - 1)
                        self.index = new_index
                        await self.update_message(interaction)

                    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
                    async def right(self, interaction: discord.Interaction, button: discord.ui.Button):
                        self.index = (self.index + 1) % len(self.posts)
                        await self.update_message(interaction)

                    @discord.ui.button(label="❌", style=discord.ButtonStyle.danger)
                    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
                        await interaction.message.delete()

                view = R34View(results)
                await message.channel.send(embed=view.current_embed(), view=view)

            except Exception as e:
                print(f"Error en búsqueda rule34: {e}")
                await message.channel.send("Hubo un error en la búsqueda.")
            return

        # ==========================
        # Comandos chistosos 100% aleatorios en toda la base
        # ==========================
        async def handle_chistoso(tags, personaje, mensaje_error):
            try:
                post = await get_random_post(tags)
                if not post:
                    await message.channel.send(mensaje_error)
                    return
                image_url = post.get("file_url") or post.get("sample_url") or post.get("preview_url")
                if image_url:
                    await message.channel.send(image_url)
                else:
                    await message.channel.send("No se encontró imagen disponible.")
            except Exception as e:
                print(f"Error al buscar en rule34: {e}")
                await message.channel.send(mensaje_error)

        if content == "teto porno" and isinstance(message.channel, discord.TextChannel) and message.channel.is_nsfw():
            await handle_chistoso(["kasane_teto"], "Teto", "No encontré nada de Teto después de varios intentos.")
            return

        if content == "neru porno" and isinstance(message.channel, discord.TextChannel) and message.channel.is_nsfw():
            await handle_chistoso(["akita_neru"], "Neru", "No encontré nada de Neru después de varios intentos.")
            return

        if content == "miku porno" and isinstance(message.channel, discord.TextChannel) and message.channel.is_nsfw():
            await handle_chistoso(["hatsune_miku"], "Miku", "No encontré nada de Miku después de varios intentos.")
            return

        # ==========================
        # Respuestas de texto simples (mejoradas)
        # ==========================
        # Detectar "kk", "kk?", "kk." etc. → primero
        if re.fullmatch(r"k{2,}[\?\¿\!\.]*", content, re.IGNORECASE) \
           or re.search(r"k{2,}\s*[\?\¿\!\.]*$", content, re.IGNORECASE):
            await message.channel.send("tragas")
            return

        # Detectar si el mensaje termina en "que" y todas sus variantes
        if re.search(r"(q(u|ú|ù)?(e|é|è|ė|ẽ|ê)+|q)(\s*\W*)*$", content, re.IGNORECASE):
            await message.channel.send("so")
            return

        # Detectar si el mensaje termina en "k", "ke", "khe" y todas sus variantes
        if re.search(r"(k(h)?(e|é|è|ė|ẽ|ê)+|k)(\s*\W*)*$", content, re.IGNORECASE):
            await message.channel.send("zo")
            return

        if content == "owo":
            await message.channel.send("uwu")
            return
        elif content == "uwu":
            await message.channel.send("owo")
            return

        if self.user in message.mentions:
            if message.author.id == 852636435677052978 and random.randint(1, 20) == 1:
                await message.channel.send("Ponte a jugar P4G")
                return

            if "is this true?" in content:
                responses = ["Absolutamente.", "Ni hablar.", "Quizá"]
                await message.channel.send(random.choice(responses))
                return

            if "grúñeme" in content or "gruñeme" in content:
                await message.channel.send("Rawr x3")
                return

            if "diselo" in content or "díselo" in content:
                await message.channel.send("Que te importa")
                return

            if "un repo?" in content:
                responses = ["Cállate"]
                await message.channel.send(random.choice(responses))
                return

        if re.search(r'\bbalatro\b', message.content, re.IGNORECASE):
            imagenes_balatro = [
                "https://media.discordapp.net/attachments/1368383731731009636/1368383799347511397/20250503_100614.jpg?ex=68180639&is=6816b4b9&hm=cfd18f47d067a49f1294e752ee1258554cc2387cccee28987148695aa87c2871&=&format=webp",
                "https://media.discordapp.net/attachments/1368383731731009636/1368383817462845560/20250503_100606.jpg?ex=6818063d&is=6816b4bd&hm=6d7473660a1ac5037a5de817a85299def143a6e5a51f8e0159eb84b48da74d40&=&format=webp",
            ]
            await message.channel.send(random.choice(imagenes_balatro))
            return

        if content.lower().startswith("argentino"):
            imagen_argentino = [
                "https://media.discordapp.net/attachments/1368383731731009636/1394860064480821248/image.png?ex=6878582a&is=687706aa&hm=672270cd443e065d4e72a59689268826a3515bb3dd257b24e3fe1fdab277eaa6&=&format=webp&quality=lossless&width=833&height=826"
            ]
            await message.channel.send(random.choice(imagen_argentino))
            return

        if content.startswith("pls penis"):
            if message.mentions:
                target = message.mentions[0].display_name
            else:
                target = message.author.display_name

            length = random.randint(0, 15)
            penis_str = "8" + "=" * length + "D"
            await message.channel.send(f"pene de {target}:\n{penis_str}")
            return

    async def send_random_message(self):
        await self.wait_until_ready()
        channel = discord.utils.get(self.get_all_channels(), name="general")

        mensajes_random = [
            "penesito",
            "yeah un pene waffle uwu",
            "chupala zau",
            "chupala walter",
            "el lucas es puto",
            "tu culo",
            "he comprao leche xD"
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
