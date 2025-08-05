# Overview

This is a comprehensive Discord moderation bot called "IronWard" built with Python using the discord.py library. The bot provides extensive server moderation capabilities including user management (ban, kick, mute, warn), message management (purge, slowmode), role management, channel management, advanced moderation tools, logging system, and automated moderation features. It supports multiple languages (Turkish and English) and uses SQLite for data persistence. The bot includes over 50+ commands covering all aspects of Discord server moderation, plus an AI assistant feature for conversational interaction both in Discord and web dashboard.

## Recent Changes
- Fixed OAuth2 "Integration requires code grant" error for bot invite links
- Bot successfully deployed and active on Discord (IronWard#3738)
- Web dashboard links updated with correct bot invite URLs
- AI assistant implemented for both Discord and web dashboard with conversational chat
- PythonAnywhere setup files prepared for 7/24 hosting on free account
- GitHub repository files prepared with proper .gitignore and LICENSE (MIT)

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Bot Framework
- **discord.py**: Primary framework for Discord API interaction
- **Commands Extension**: Uses discord.ext.commands for structured command handling
- **Cogs System**: Modular architecture with separate cogs for different functionality areas:
  - `moderation.py` - Core moderation commands (ban, kick, mute, warn, purge, slowmode)
  - `advanced_moderation.py` - Advanced commands (tempban, softban, timeout, nickname, voice management)
  - `automod.py` - Automated moderation features and punishment expiry checking
  - `settings.py` - Server configuration commands and language switching
  - `utility.py` - General utility commands (userinfo, avatar, help, ping)
  - `logging.py` - Comprehensive logging system (modlogs, reports, banlist, auditlog)
  - `channel_management.py` - Channel operations (create, delete, hide, lock, pin/unpin)
  - `role_management.py` - Role operations (create, delete, mass role, role stats, color)

## Data Layer
- **SQLite Database**: Local file-based database (`moderation_bot.db`)
- **Async Database Operations**: Thread-safe database operations using asyncio locks
- **Core Tables**:
  - `guild_settings` - Server-specific configuration (language, prefix, channels, roles)
  - `warnings` - User warning system with moderator tracking
  - `temp_bans` - Temporary ban management
  - `mutes` - Mute tracking with expiration times
  - `mod_logs` - Comprehensive moderation action logging

## Internationalization
- **Multi-language Support**: JSON-based language files for Turkish and English
- **Dynamic Text Loading**: Runtime language switching based on server settings
- **Fallback System**: Defaults to Turkish if translation keys are missing

## Permission & Security System
- **Hierarchy Validation**: Prevents users from moderating higher-ranked members
- **Permission Decorators**: Built-in Discord permission checking
- **Bot Permission Validation**: Ensures bot has necessary permissions before actions
- **Owner Protection**: Special handling to prevent actions against server owners

## Automated Features
- **Background Tasks**: Scheduled tasks for checking expired punishments
- **Spam Detection**: Message tracking for anti-spam measures
- **Auto-unmute**: Automatic role removal when mute periods expire
- **Auto-unban**: Automatic ban removal for temporary bans

## Utility Systems
- **Embed Standardization**: Consistent embed formatting across all commands
- **Time Parsing**: Flexible time input parsing (supports various formats and languages)
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Logging**: Structured logging for debugging and monitoring

# External Dependencies

## Discord API
- **discord.py**: Primary library for Discord bot functionality
- **Discord Gateway**: Real-time event handling for messages, members, guilds
- **Discord REST API**: HTTP-based operations for moderation actions

## Environment Configuration
- **Environment Variables**: Bot token management through `DISCORD_BOT_TOKEN`
- **No external config files**: Configuration stored in database per-guild

## Database
- **SQLite**: Built-in Python SQLite3 module for local data storage
- **No external database services**: Self-contained database solution

## Development Tools
- **Semgrep**: Static analysis tool configuration for security scanning
- **Python Standard Library**: asyncio, json, datetime, re, logging, os