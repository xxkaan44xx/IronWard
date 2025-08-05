import asyncio
import os
from bot import IronWardBot

async def main():
    """Main entry point for the Discord moderation bot."""
    # Get bot token from environment variables
    token = os.getenv('DISCORD_BOT_TOKEN')

    if not token:
        print("❌ HATA: DISCORD_BOT_TOKEN çevre değişkeni bulunamadı!")
        print("Bot tokenınızı DISCORD_BOT_TOKEN çevre değişkenine ekleyin.")
        return

    # Debug token (show first 5 and last 5 characters)
    if len(token) > 50:
        print(f"✅ Token bulundu: {token[:5]}...{token[-5:]}")
        print(f"Token uzunluğu: {len(token)} karakter")
    else:
        print(f"❌ Token çok kısa! Discord bot tokenleri 70+ karakter olmalı.")
        print(f"Mevcut token uzunluğu: {len(token)} karakter")
        print("Lütfen Discord Developer Portal'dan yeni bir bot token alın:")
        print("1. https://discord.com/developers/applications adresine gidin")
        print("2. Botunuzun sayfasını açın")
        print("3. 'Bot' sekmesinden 'Reset Token' yapın")
        print("4. Yeni tokeni DISCORD_BOT_TOKEN çevre değişkenine ekleyin")
        return

    # Initialize and run the bot
    bot = IronWardBot()

    try:
        print("🤖 Bot başlatılıyor...")
        # Load cogs - unified list without duplicates
        initial_extensions = [
            'cogs.moderation',
            'cogs.utility',
            'cogs.settings',
            'cogs.automod',
            'cogs.advanced_moderation',
            'cogs.logging',
            'cogs.channel_management',
            'cogs.role_management',
            'cogs.server_management',
            'cogs.ticket_system',
            'cogs.reaction_roles',
            'cogs.fun_commands',
            'cogs.security_moderation',
            'cogs.modmail',
            'cogs.ai_assistant'
        ]

        for extension in initial_extensions:
            try:
                await bot.load_extension(extension)
                print(f"✅ {extension} yüklendi!")
            except Exception as e:
                print(f"❌ {extension} yüklenirken hata: {e}")

        await bot.start(token)
    except Exception as e:
        print(f"❌ Bot başlatılırken hata oluştu: {e}")
    finally:
        await bot.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot kapatılıyor...")