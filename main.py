import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import docker
import time

# load env
load_dotenv()
token = os.getenv("DISCORD_TOKEN")
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

# setup docker daemon
client = docker.from_env()
containers = {}

@bot.event
async def on_ready():
    print(f"{bot.user.name} is ready")

@bot.command(help="Nyalain server menkrep")
async def start(ctx):
    # Check if user has required roles
    allowed_roles = ['Admin', 'Minecraft']
    user_roles = [role.name for role in ctx.author.roles]
    
    if not any(role in allowed_roles for role in user_roles):
        await ctx.send("Kamu ga punya akses untuk start server!")
        return
    
    await ctx.send("wait")
    print("Starting server...")
    
    try:
        runServer()
        await ctx.send("Server menkrep nyala")
    except Exception as e:
        await ctx.send(f"Error starting server: {str(e)}")
        print(f"Error: {e}")

@bot.command(help="Matikan server menkrep")
async def stop(ctx):
    # Check if user has required roles
    allowed_roles = ['Admin', 'Minecraft']
    user_roles = [role.name for role in ctx.author.roles]
    
    if not any(role in allowed_roles for role in user_roles):
        await ctx.send("Kamu ga punya akses untuk stop server!")
        return
        
    await ctx.send("wait")
    print("Stopping server...")
    
    try:
        stopServer()
        await ctx.send("Server menkrep mati")
    except Exception as e:
        await ctx.send(f"Error stopping server: {str(e)}")
        print(f"Error: {e}")

# buat container minecraft
def runServer():
    try:
        # Stop existing containers if running
        try:
            existing_mc = client.containers.get("mc-server-1")
            existing_mc.stop()
            existing_mc.remove()
        except docker.errors.NotFound:
            pass
            
        try:
            existing_playit = client.containers.get("playit")
            existing_playit.stop()
            existing_playit.remove()
        except docker.errors.NotFound:
            pass

        # Start Minecraft server
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
        print("Minecraft server started")
        
        # Wait a bit for MC server to initialize
        time.sleep(5)

        # Start playit agent
        playit = client.containers.run(
            "ghcr.io/playit-cloud/playit-agent:0.15",
            name="playit",
            network_mode="host",
            detach=True,
            environment={
                "PLAYIT_SECRET_KEY": playit_secret_key  # Fixed environment variable name
            }
        )
        containers["playit"] = playit
        print("Playit started")
        
    except Exception as e:
        print(f"Error starting server: {e}")
        raise e

# stop container
def stopServer():
    try:
        # Stop containers by name to be more reliable
        container_names = ["mc-server-1", "playit"]
        
        for name in container_names:
            try:
                container = client.containers.get(name)
                container.stop()
                container.remove()
                print(f"Stopped and removed {name}")
            except docker.errors.NotFound:
                print(f"Container {name} not found")
            except Exception as e:
                print(f"Error stopping {name}: {e}")
        
        # Clear the containers dict
        containers.clear()
        print("All containers stopped")
        
    except Exception as e:
        print(f"Error stopping servers: {e}")
        raise e

bot.run(token, log_handler=handler, log_level=logging.DEBUG)