# Discord Webhook Manager Bot

A Discord bot that manages custom webhooks and commands, with additional features like Roblox profile image fetching.

## Features

- Create and manage Discord webhooks
- Add custom commands with descriptions
- Fetch Roblox profile images
- Custom action messages with embedded formatting
- SQLite database for persistent storage

## Commands

- `/action [user] [title] [action] [color] [custom_color?] [notes?]` - Create custom action message
- `!create-webhook [webhook_url] [name]` - Create a new webhook
- `!add-command [webhook_name] [command_name] [description] [message]` - Add a custom command
- `!list-webhooks` - Show all webhooks
- `!list-commands [webhook_name]` - Show all commands for a webhook
- `!run [webhook_name] [command_name]` - Execute a webhook command
- `!roblox [username]` - Get Roblox profile image

### Custom Action Command
The `/action` command creates formatted messages with the following parameters:
- `user`: Enter Roblox username or userID
- `title`: Action title (e.g., "Discipline Action", "Employee Action")
- `action`: Action description (e.g., "has been **awarded** the **Award Commendation**")
- `color`: Choose from: Aqua, Gold, Dark Gold, Green, Dark Green, Default
- `custom_color` (optional): HEX color value (e.g., #FF0000) - used if color is "Default"
- `notes` (optional): Additional information, reasons, or callsigns

Example:
```
/action JohnDoe "Employee Action" "has been **promoted** to **Senior Officer**" Green
/action JaneDoe "Discipline Action" "has received a **warning**" Default #FF0000 "Excessive tardiness"
```

### Command Examples:
```
# Create a webhook
!create-webhook https://discord.com/api/webhooks/... announcements

# Add a command with description
!add-command announcements welcome "Welcome message for new members" Welcome to our server! 🎉

# Run a command
!run announcements welcome

# Get Roblox profile
!roblox username123
```

## Setup Instructions

### Prerequisites
1. Python 3.11 or higher
2. Visual Studio Code
3. Discord Bot Token

### IMPORTANT: Discord Bot Configuration
Before running the bot, you MUST enable privileged intents:
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application
3. Click on "Bot" in the left sidebar
4. Scroll down to "Privileged Gateway Intents"
5. Enable ALL of the following:
   - Message Content Intent
   - Server Members Intent
   - Presence Intent
6. Click "Save Changes"

### VS Code Setup
1. Clone or download the project files:
   - bot.py
   - database.py
   - .env (create this)
   - README.md

2. Open the project in VS Code:
   ```bash
   code discord-webhook-bot
   ```

3. Create a Python virtual environment (recommended):
   ```bash
   python -m venv venv
   # On Windows
   .\venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

4. Install required packages:
   ```bash
   pip install discord.py python-dotenv aiohttp
   ```

5. Create a `.env` file in the project root with your Discord bot token:
   ```
   DISCORD_TOKEN=your_token_here
   ```

6. Run the bot:
   ```bash
   python bot.py
   ```

### VS Code Extensions (Recommended)
- Python (Microsoft)
- Python Environment Manager
- SQLite Viewer
- Discord Presence
- Prettier - Code formatter

## Files Structure

- `bot.py` - Main bot code
- `database.py` - Database handler
- `.env` - Environment variables
- `webhooks.db` - SQLite database (created automatically)

## Required Permissions

The bot needs the following permissions:
- Read Messages/View Channels
- Send Messages
- Manage Webhooks
- Embed Links

## Development Tips

1. Debugging in VS Code:
   - Use the built-in debugger with F5
   - Set breakpoints by clicking the line number
   - Watch variables in the debug console

2. Database Management:
   - Use VS Code's SQLite Viewer extension to inspect the database
   - Keep backups of webhooks.db if needed

3. Environment Variables:
   - Use python-dotenv for local development
   - Keep .env in .gitignore

## Troubleshooting

If the bot fails to start:
1. Verify Privileged Intents are enabled in the Discord Developer Portal
   - All three intents (Message Content, Server Members, Presence) must be enabled
   - Changes may take a few minutes to propagate
2. Check your bot token is correct and up to date
3. Try regenerating the bot token if issues persist
4. Ensure you've installed all required dependencies

## Support

If you encounter any issues:
1. Check if privileged intents are enabled
2. Verify the bot token is correct
3. Ensure all required permissions are granted
4. Check Python version compatibility
5. Verify all dependencies are installed correctly

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.