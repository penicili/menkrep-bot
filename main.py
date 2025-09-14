import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import docker

# load env
load_dotenv()
token = os.getenv ("DISCORD_BOT_TOKEN")
playit_secret_key = os.getenv("PLAYIT_SECRET_KEY")

# setup logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# setup intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

# init bot
bot = commands.Bot(command_prefix='!mc', intents=intents)

# commands
@bot.event
async def on_ready():
    print(f"{bot.user.name} is ready")

@bot.command(help="Nyalain server menkrep")
async def start(ctx):
    allowed_roles = ['Admin', 'Minecraft']
    runServer()
    await ctx.send("Server menkrep nyala")

@bot.command(help="Matikan server menkrep")
async def stop(ctx):
    allowed_roles = ['Admin', 'Minecraft']
    stopServer()
    await ctx.send("Server menkrep mati")



# setup docker daemon
client = docker.from_env()

containers = {}

# buat container bot minecraft
def runServer():
    mc1 = client.containers.run(
        "itzg/minecraft-server",
        name="mc-server-1",
        ports={'25565/tcp': 25565},
        volumes={'./data': {'bind': '/data', 'mode': 'rw'}},
        detach=True,
        environment={
            "EULA": "TRUE",
            "TYPE": "PAPER"
        }
    )
    containers["mc-server-1"] = mc1

    # buat container playit
    playit = client.containers.run(
        image="ghcr.io/playit-cloud/playit-agent:0.15",
        name="playit",
        network_mode="host",
        detach=True,
        depends_on=["mc-server-1"],
        environment={"SECRET_KEY": playit_secret_key},
        
    )
    containers["playit"] = playit

# stop container
def stopServer():
    for c in containers.values():
        c.stop()
        c.remove()
    
    
bot.run(token, log_handler=handler, log_level=logging.INFO)