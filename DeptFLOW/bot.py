import os
import discord
from discord.ext import commands
from discord import Webhook, app_commands
from discord.app_commands import checks
import aiohttp
import asyncio
from database import WebhookDatabase
from database import BotConfigDatabase
from dotenv import load_dotenv
from typing import Optional
from datetime import datetime

# Load environment variables
load_dotenv()

# Bot setup with required intents
intents = discord.Intents.default()
intents.message_content = True  # Required for reading message content
intents.guilds = True          # Required for guild/server related features
intents.members = True         # Required for member-related features

# Create bot instance with command handler
class CustomBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)
        self.tree.error(self.on_app_command_error)

    async def setup_hook(self):
        print("Setting up command tree...")
        try:
            print("Attempting to sync commands...")
            synced = await self.tree.sync()
            print(f"Successfully synced {len(synced)} command(s)")
            for cmd in synced:
                print(f"- Synced command: {cmd.name}")
        except Exception as e:
            print(f"Failed to sync commands: {e}")
        print("Command tree synced!")

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(f"Please wait {error.retry_after:.2f} seconds before using this command again.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An error occurred: {str(error)}", ephemeral=True)
            print(f"Command error: {str(error)}")

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Bot is in {len(self.guilds)} servers')
        print('✅ Bot is ready! All commands have been synced.')
        print('Available commands:')
        print('- /setup - Configure bot settings (Admin only)')
        print('- /action - Create custom action messages')
        print('- /roblox - Get Roblox profile images')
        print('\nIMPORTANT: An administrator must run /setup first to:')
        print('1. Set the log channel for action messages')
        print('2. Configure which role can use commands')
        print('\nMake sure you have enabled:')
        print('- Message Content Intent')
        print('- Server Members Intent')
        print('- Presence Intent')
        print('in your Discord Developer Portal')


# Add after WebhookDatabase initialization
bot_config_db = BotConfigDatabase()

async def get_roblox_profile_image(username: str) -> Optional[str]:
    """Fetch Roblox profile image URL for a given username"""
    # Configure timeout and retry settings
    timeout = aiohttp.ClientTimeout(total=30, connect=10)
    retry_attempts = 3

    for attempt in range(retry_attempts):
        try:
            conn = aiohttp.TCPConnector(
                ssl=True,
                verify_ssl=True,
                use_dns_cache=True,
                ttl_dns_cache=300,
                family=0,  # Allow both IPv4 and IPv6
                resolver=aiohttp.AsyncResolver()  # Use async DNS resolver
            )

            async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
                # Add headers to mimic a browser request
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'application/json',
                    'Accept-Language': 'en-US,en;q=0.9',
                }

                # First get user ID from username
                user_api_url = f"https://users.roblox.com/v1/users/search?keyword={username}&limit=1"
                print(f"[Roblox API] Attempt {attempt + 1}/{retry_attempts}")
                print(f"[Roblox API] Requesting user data from: {user_api_url}")

                async with session.get(user_api_url, headers=headers) as response:
                    print(f"[Roblox API] User search status code: {response.status}")
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[Roblox API] Error response: {error_text}")
                        if attempt < retry_attempts - 1:
                            continue
                        return None

                    data = await response.json()
                    print(f"[Roblox API] User search response: {data}")
                    if not data.get("data") or not data["data"]:
                        print(f"[Roblox API] No user found for username: {username}")
                        return None

                    user_id = data["data"][0]["id"]
                    print(f"[Roblox API] Found user ID: {user_id}")

                # Then get the profile image using the newer thumbnails API with larger size
                thumbnail_api_url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=720x720&format=Png"
                print(f"[Roblox API] Requesting thumbnail from: {thumbnail_api_url}")

                async with session.get(thumbnail_api_url, headers=headers) as response:
                    print(f"[Roblox API] Thumbnail status code: {response.status}")
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[Roblox API] Error response: {error_text}")
                        if attempt < retry_attempts - 1:
                            continue
                        return None

                    data = await response.json()
                    print(f"[Roblox API] Thumbnail response: {data}")
                    if data.get("data") and data["data"]:
                        image_url = data["data"][0].get("imageUrl")
                        print(f"[Roblox API] Successfully retrieved image URL: {image_url}")
                        return image_url

            return None

        except aiohttp.ClientConnectorError as e:
            print(f"[Roblox API] Connection error (attempt {attempt + 1}): {str(e)}")
            if attempt < retry_attempts - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            print("[Roblox API] Failed to connect after all retries")
            return None

        except aiohttp.ClientError as e:
            print(f"[Roblox API] Network error: {str(e)}")
            return None

        except Exception as e:
            print(f"[Roblox API] Unexpected error: {str(e)}")
            return None

bot = CustomBot()

@bot.tree.command(name="setup", description="Configure bot settings for your server")
@app_commands.describe(
    log_channel="Department log channel",
    manage_role="The role that has access to commands",
    al_message="Message to send when someone is put on Administrative Leave"
)
@app_commands.checks.has_permissions(administrator=True)
async def setup_bot(
    interaction: discord.Interaction,
    log_channel: discord.TextChannel,
    manage_role: discord.Role,
    al_message: Optional[str] = None
):
    try:
        # Defer response since we'll be doing database operations
        await interaction.response.defer(ephemeral=True)

        # Save configuration to database
        success = bot_config_db.save_config(
            str(interaction.guild_id),
            str(log_channel.id),
            str(manage_role.id),
            al_message
        )

        if success:
            embed = discord.Embed(
                title="Bot Configuration",
                description="✅ Setup completed successfully!",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Log Channel",
                value=f"Set to {log_channel.mention}",
                inline=False
            )
            embed.add_field(
                name="Management Role",
                value=f"Set to {manage_role.mention}",
                inline=False
            )
            if al_message:
                embed.add_field(
                    name="Administrative Leave Message",
                    value=al_message,
                    inline=False
                )

            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(
                "❌ Failed to save configuration. Please try again.",
                ephemeral=True
            )

    except Exception as e:
        await interaction.followup.send(
            f"❌ An error occurred: {str(e)}",
            ephemeral=True
        )
        print(f"Setup command error: {str(e)}")

def has_management_role():
    async def predicate(interaction: discord.Interaction):
        if interaction.guild is None:
            return False

        config = bot_config_db.get_config(str(interaction.guild_id))
        if not config:
            await interaction.response.send_message(
                "❌ Server not configured! An administrator needs to run the /setup command first.",
                ephemeral=True
            )
            return False

        manage_role_id = int(config[1])  # Index 1 is manage_role_id
        user_roles = [role.id for role in interaction.user.roles]

        return manage_role_id in user_roles

    return app_commands.check(predicate)

@bot.tree.command(name="action", description="Create a custom action message with Roblox profile")
@app_commands.describe(
    user="Enter Roblox username or userID",
    title="Action title e.g. Discipline Action, Employee Action",
    action="e.g. has been **awarded** the **Award Commendation**",
    color="Embed color (Aqua, Gold, Dark Gold, Green, Dark Green, Default)",
    custom_color="Custom embed color, enter a HEX value. Used if color is set to Default",
    notes="Notes"
)
@app_commands.choices(color=[
    app_commands.Choice(name="Aqua", value="aqua"),
    app_commands.Choice(name="Gold", value="gold"),
    app_commands.Choice(name="Dark Gold", value="dark_gold"),
    app_commands.Choice(name="Green", value="green"),
    app_commands.Choice(name="Dark Green", value="dark_green"),
    app_commands.Choice(name="Default", value="default"),
])
@checks.cooldown(1, 5.0)  # 1 use per 5 seconds
@has_management_role()
async def custom_action(
    interaction: discord.Interaction,
    user: str,
    title: str,
    action: str,
    color: str,
    custom_color: Optional[str] = None,
    notes: Optional[str] = None
):
    try:
        # Immediately defer the response
        await interaction.response.defer(ephemeral=True)
        print(f"Processing action command for user: {user}")

        # Get the configured log channel
        config = bot_config_db.get_config(str(interaction.guild_id))
        if not config:
            await interaction.followup.send(
                "❌ Server not configured! An administrator needs to run the /setup command first.",
                ephemeral=True
            )
            return

        log_channel_id = int(config[0])  # Index 0 is log_channel_id
        log_channel = interaction.guild.get_channel(log_channel_id)

        if not log_channel:
            await interaction.followup.send(
                "❌ Could not find the configured log channel. Please ask an administrator to run /setup again.",
                ephemeral=True
            )
            return

        # Create initial embed with basic info
        color = color.lower()
        embed_color = COLOR_PRESETS.get(color, discord.Color.default())

        # Handle custom color if provided
        if color == 'default' and custom_color:
            try:
                custom_color = custom_color.strip('#')
                embed_color = discord.Color(int(custom_color, 16))
            except ValueError:
                await interaction.followup.send("❌ Invalid HEX color format! Example: #FF0000", ephemeral=True)
                return

        # Create embed with basic information first
        embed = discord.Embed(
            title=title,
            description=f"{user} {action}",
            color=embed_color
        )

        # Add notes if provided
        if notes:
            embed.add_field(name="Notes", value=notes, inline=False)

        # Add timestamp
        embed.timestamp = datetime.utcnow()

        # Fetch Roblox profile image in background with timeout
        try:
            print(f"Fetching Roblox profile for user: {user}")
            profile_url = await asyncio.wait_for(
                get_roblox_profile_image(user),
                timeout=10.0
            )
            if profile_url:
                print(f"Successfully got profile image for {user}")
                embed.set_image(url=profile_url)
            else:
                print(f"No profile image found for {user}")
                embed.add_field(name="Note", value="⚠️ Could not fetch Roblox profile image", inline=False)
        except asyncio.TimeoutError:
            print(f"Timeout while fetching profile image for {user}")
            embed.add_field(name="Note", value="⚠️ Timed out while fetching Roblox profile image", inline=False)
        except Exception as e:
            print(f"Error fetching profile image: {str(e)}")
            embed.add_field(name="Note", value="⚠️ Error fetching Roblox profile image", inline=False)

        # Send the embed to the log channel
        await log_channel.send(embed=embed)

        # Send confirmation to the user
        await interaction.followup.send("✅ Action message sent to the log channel!", ephemeral=True)

    except Exception as e:
        error_msg = f"❌ Error creating action message: {str(e)}"
        print(error_msg)
        try:
            await interaction.followup.send(error_msg, ephemeral=True)
        except:
            if not interaction.response.is_done():
                await interaction.response.send_message(error_msg, ephemeral=True)

@bot.tree.command(name="roblox", description="Get Roblox profile image for a username")
@app_commands.describe(username="The Roblox username to look up")
async def roblox_profile(interaction: discord.Interaction, username: str):
    try:
        await interaction.response.defer()
        profile_url = await get_roblox_profile_image(username)
        if profile_url:
            embed = discord.Embed(title=f"Roblox Profile: {username}", color=discord.Color.blue())
            embed.set_image(url=profile_url)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ Couldn't find Roblox profile for username: {username}")
    except Exception as e:
        await interaction.followup.send(f"❌ Error fetching Roblox profile: {str(e)}")
        print(f"Roblox API error for username {username}: {str(e)}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command!", ephemeral=True)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required argument! Please check the command usage.", ephemeral=True)
    elif isinstance(error, commands.CommandInvokeError):
        if isinstance(error.original, discord.errors.PrivilegedIntentsRequired):
            await ctx.send("❌ Bot needs privileged intents enabled in Discord Developer Portal (Message Content, Server Members, and Presence Intents). Please contact the bot administrator.", ephemeral=True)
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}", ephemeral=True)
            print(f"Error in command {ctx.command}: {str(error)}")
    else:
        await ctx.send(f"❌ An error occurred: {str(error)}", ephemeral=True)
        print(f"Unhandled error in command {ctx.command}: {str(error)}")

# Define color presets
COLOR_PRESETS = {
    'aqua': discord.Color.blue(),
    'gold': discord.Color.gold(),
    'dark_gold': discord.Color.dark_gold(),
    'green': discord.Color.green(),
    'dark_green': discord.Color.dark_green(),
    'default': None  # Will be replaced with custom color if provided
}

# Add this at the end of the file
if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found in environment variables!")
    else:
        print("Starting bot... Make sure you have enabled ALL required intents in Discord Developer Portal:")
        print("- Message Content Intent")
        print("- Server Members Intent")
        print("- Presence Intent")
        bot.run(TOKEN)