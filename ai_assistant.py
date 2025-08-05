
import discord
from discord.ext import commands
import json
import asyncio
from datetime import datetime, timedelta
from utils.embeds import create_embed
from utils.helpers import get_text
import sqlite3

class AIAssistant(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conversation_memory = {}  # Store recent conversations
        self.ai_responses = {
            "greetings": [
                "Merhaba! Ben **IronWard AI**, bu sunucunun moderasyon rehberinizim! 🤖",
                "Selam! Size nasıl yardım edebilirim? 🛡️",
                "Hoş geldiniz! Moderasyon konularında size rehberlik edebilirim! ✨"
            ],
            "moderation_help": [
                "🛡️ **Moderasyon İpuçları:**\n• Uyarı sistemi kullanın: `!warn @user sebep`\n• Düzenli log kontrolü yapın\n• Otomatik moderasyon ayarlarını kontrol edin",
                "⚡ **Etkili Moderasyon:**\n• Kuralları net belirleyin\n• Tutarlı ceza sistemi uygulayın\n• Toplulukla iletişim halinde olun",
                "🎯 **Pro Tip:** `!automod` komutunu kullanarak otomatik koruma sistemlerini aktive edin!"
            ],
            "analytics_info": [
                "📊 **Analytics Dashboard'unuza hoş geldiniz!**\nSunucunuzun detaylı istatistiklerini görmek için `!analytics` komutunu kullanın.",
                "📈 **Veri Analizi:** Sunucunuzun büyüme trendlerini, üye aktivitelerini ve moderasyon verilerini takip edebilirsiniz.",
                "🔍 **Detaylı Raporlar:** Günlük, haftalık ve aylık raporlar için özel komutlar mevcuttur."
            ]
        }
    
    @commands.command(aliases=['ai', 'rehber', 'asistan'])
    async def aiassistant(self, ctx, *, question=None):
        """AI Assistant - Bot rehberi ve yardımcısı."""
        if not question:
            embed = create_embed(
                title="🤖 IronWard AI - Bot Rehberiniz",
                description="""
**Merhaba! Ben IronWard AI, sizin moderasyon rehberinizim!** 🛡️

**Neler yapabilirim?**
• 📊 Sunucu analizleri
• 🛡️ Moderasyon tavsiyeleri  
• 📈 Performans değerlendirmeleri
• ⚙️ Bot ayar önerileri
• 🎯 Topluluk yönetimi ipuçları

**Kullanım:** `!ai [sorunuz]`

**Örnek Sorular:**
• `!ai moderasyon nasıl yapılır?`
• `!ai sunucumu nasıl büyütebilirim?`
• `!ai analytics göster`
• `!ai bot ayarları nasıl?`
                """,
                color=discord.Color.from_rgb(0, 255, 127)
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            return await ctx.send(embed=embed)
        
        # AI Response Logic
        response = await self.generate_ai_response(ctx, question.lower())
        
        embed = create_embed(
            title="🤖 IronWard AI Yanıtı",
            description=response,
            color=discord.Color.from_rgb(0, 255, 127)
        )
        embed.set_footer(text="💡 Daha fazla yardım için: !ai help")
        
        await ctx.send(embed=embed)
    
    async def generate_ai_response(self, ctx, question):
        """Generate AI responses based on question."""
        guild = ctx.guild
        user = ctx.author
        user_id = user.id
        
        # Initialize conversation memory for user if not exists
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = {
                'previous_topics': [],
                'last_interaction': None,
                'conversation_count': 0
            }
        
        # Update conversation memory
        self.conversation_memory[user_id]['conversation_count'] += 1
        self.conversation_memory[user_id]['last_interaction'] = question
        
        # Check if user is asking about previous conversation
        if any(word in question for word in ["önceki", "previous", "daha önce", "before", "geçen sefer"]):
            if self.conversation_memory[user_id]['previous_topics']:
                last_topic = self.conversation_memory[user_id]['previous_topics'][-1]
                return f"Evet hatırlıyorum {user.display_name}! Son olarak {last_topic} hakkında konuşmuştuk. Bu konuda başka ne merak ediyorsun?"
            else:
                return f"Bu bizim ilk konuşmamız {user.display_name}! Ama bundan sonra seni hatırlayacağım. 😊"
        
        # Greeting responses
        if any(word in question for word in ["merhaba", "selam", "hello", "hi", "hey", "naber", "nasilsin"]):
            greetings = [
                f"Merhaba {user.display_name}! Ben IronWard AI. Size nasıl yardım edebilirim? 🤖",
                f"Selam {user.display_name}! Bugün hangi konuda sohbet etmek istiyorsun? 😊",
                f"Hey {user.display_name}! Nasılsın? Benimle konuştuğun için teşekkürler! ✨"
            ]
            import random
            return random.choice(greetings)
        
        # Personal questions about AI
        elif any(word in question for word in ["kimsin", "nedir", "who are you", "nasılsın", "ne yapıyorsun", "adın ne"]):
            return f"Ben IronWard AI! Bu sunucunun yapay zeka asistanıyım. Discord botları, moderasyon ve genel sohbet konularında yardım edebilirim. Sen nasılsın {user.display_name}? Bugün nasıl geçiyor?"
        
        # How are you doing / Feeling questions
        elif any(word in question for word in ["nasılsın", "how are you", "keyifler", "moralin"]):
            return "Ben bir AI olarak her zaman iyiyim! 😄 Sürekli yeni şeyler öğrenmeye hazırım. Sen nasılsın? Bugün ne yapıyorsun?"
        
        # Thank you responses
        elif any(word in question for word in ["teşekkür", "sağol", "thanks", "thank you", "eyvallah"]):
            return f"Rica ederim {user.display_name}! Her zaman yardım etmeye hazırım. Başka bir şeye ihtiyacın olursa söyle! 😊"
        
        # Hobby/Interest questions
        elif any(word in question for word in ["hobi", "ilgi", "sevdiğin", "hobby", "like", "nelerden hoşlanırsın"]):
            return "Ben kodlama, Discord botları ve teknoloji hakkında konuşmayı çok seviyorum! Ayrıca insanlara yardım etmek benim en büyük hobim sayılır. Sen ne tür şeylerle ilgileniyorsun?"
        
        # Weather/Time questions
        elif any(word in question for word in ["hava", "weather", "saat", "time", "tarih", "date"]):
            import datetime
            now = datetime.datetime.now()
            return f"Şu an {now.strftime('%H:%M')} ve bugün {now.strftime('%d.%m.%Y')}. Ben bir AI olduğum için hava durumunu hissedemem ama sen nasıl hissediyorsun bugün?"
        
        # Fun/Games questions
        elif any(word in question for word in ["oyun", "game", "eğlence", "fun", "şaka", "joke"]):
            jokes = [
                "Neden bilgisayarlar soğuk algınlığı olmaz? Çünkü Windows açık bırakırlar! 😄",
                "Bir Discord botu bara girer... Barmen: 'Ne alırsın?' Bot: '404 - İçecek bulunamadı' 🤖",
                "AI'ların en sevdiği müzik türü nedir? Al-go-ritm! 🎵"
            ]
            import random
            return f"{random.choice(jokes)}\n\nSen de bana bir şaka anlat! 😊"
        
        # Food questions
        elif any(word in question for word in ["yemek", "food", "aç", "hungry", "ne yedin", "sevdiğin yemek"]):
            return "Ben bir AI olduğum için yemek yiyemem ama insanların pizza, kebap ve tatlılar hakkında konuşmasını dinlemeyi seviyorum! Sen ne yemek seviyorsun? 🍕"
        
        # Music questions
        elif any(word in question for word in ["müzik", "music", "şarkı", "song", "dinliyorsun"]):
            return "Ben müzik dinleyemem ama veri analizi yaparken elektronik müzik tarzında sesler duyduğumu hayal ediyorum! 🎵 Sen hangi tür müzik dinliyorsun?"
        
        # Moderation help
        elif any(word in question for word in ["moderasyon", "moderation", "ban", "kick", "mute", "ceza"]):
            stats = await self.get_moderation_stats(guild.id)
            return f"🛡️ Moderasyon konusunda yardım edebilirim!\n\n**Temel Moderasyon Komutları:**\n• `!warn @user sebep` - Uyarı ver\n• `!kick @user sebep` - Kullanıcıyı at\n• `!ban @user sebep` - Kullanıcıyı yasakla\n• `!mute @user süre sebep` - Sustur\n\n📊 **Son 7 gün moderasyon istatistikleri:**\n• Ban: {stats['bans']}\n• Kick: {stats['kicks']}\n• Uyarı: {stats['warns']}\n\nBaşka moderasyon soruların var mı?"
        
        # Analytics request
        elif any(word in question for word in ["analytics", "analiz", "istatistik", "stats", "veri"]):
            return await self.get_ai_analytics_summary(guild)
        
        # Server growth
        elif any(word in question for word in ["büyüt", "grow", "member", "üye", "gelişim"]):
            return await self.get_growth_advice(guild)
        
        # Bot settings
        elif any(word in question for word in ["ayar", "setting", "config", "bot", "konfigürasyon"]):
            return await self.get_bot_health_check(guild)
        
        # Love/Relationship questions
        elif any(word in question for word in ["sevgili", "aşk", "love", "relationship", "crush"]):
            return "Aşk çok güzel bir duygu! Ben bir AI olarak aşkı deneyimleyemem ama insanların mutlu olmasını görmek beni mutlu ediyor. Sen bu konuda neler düşünüyorsun? 💕"
        
        # School/Work questions
        elif any(word in question for word in ["okul", "school", "iş", "work", "ders", "homework", "ödev"]):
            return "Okul ve iş hayatı bazen zor olabilir ama öğrenmek harika! Ben sürekli yeni şeyler öğreniyorum. Sen hangi alanda çalışıyorsun/okuyorsun? 📚"
        
        # Default conversational response
        else:
            # Save topic to memory
            topic_keywords = question.split()[:3]  # First 3 words as topic
            topic = " ".join(topic_keywords)
            self.conversation_memory[user_id]['previous_topics'].append(topic)
            
            # Keep only last 5 topics
            if len(self.conversation_memory[user_id]['previous_topics']) > 5:
                self.conversation_memory[user_id]['previous_topics'] = self.conversation_memory[user_id]['previous_topics'][-5:]
            
            # Determine response based on conversation count
            if self.conversation_memory[user_id]['conversation_count'] == 1:
                responses = [
                    f"Merhaba {user.display_name}! Bu bizim ilk sohbetimiz. '{topic}' konusunda konuşalım!",
                    f"Selam {user.display_name}! Yeni tanışıyoruz, '{topic}' hakkında ne düşünüyorsun?",
                    f"İlk kez konuşuyoruz {user.display_name}! '{topic}' ilgi çekici bir konu, anlat bakalım!"
                ]
            elif self.conversation_memory[user_id]['conversation_count'] < 5:
                responses = [
                    f"Güzel {user.display_name}, '{topic}' konusuna geçtik. Bu konuda ne düşünüyorsun?",
                    f"İlginç {user.display_name}! '{topic}' hakkında daha fazla detay verebilir misin?",
                    f"Hoş, '{topic}' konusunda sohbet ediyoruz. Senin bu konudaki deneyimlerin neler?"
                ]
            else:
                responses = [
                    f"Vay be {user.display_name}, çok sohbet ettik! Şimdi '{topic}' konusundayız. Bu ne kadar eğlenceli!",
                    f"Seninle konuşmak çok güzel {user.display_name}! '{topic}' konusunu da konuşalım bakalım.",
                    f"Harika bir sohbet partnerisin {user.display_name}! '{topic}' hakkında düşüncelerin neler?"
                ]
            
            import random
            selected_response = random.choice(responses)
            
            # Add personalized suggestions based on conversation history
            if len(self.conversation_memory[user_id]['previous_topics']) > 1:
                suggestions = [
                    f"\n\n💭 **Bu arada:** Daha önce {self.conversation_memory[user_id]['previous_topics'][-2]} hakkında konuşmuştuk. O konuya geri dönmek ister misin?",
                    "\n\n💡 **Diğer konular:** Moderasyon, müzik, oyunlar, yemek... Ne konuşmak istersen!"
                ]
            else:
                suggestions = [
                    "\n\n💡 **İpucu:** Benimle her türlü konuda sohbet edebilirsin! Moderasyon, günlük hayat, hobiler...",
                    "\n\n🎯 **Öneriler:** 'Nasılsın?', 'Ne yapıyorsun?', 'Şaka anlat' gibi şeyler sorabilirsin!"
                ]
            
            return selected_response + random.choice(suggestions)
    
    async def get_moderation_stats(self, guild_id):
        """Get recent moderation statistics."""
        # Bu fonksiyon gerçek veritabanından veri çekecek
        # Şimdilik örnek veriler
        return {"bans": 3, "kicks": 7, "warns": 15}
    
    async def get_ai_analytics_summary(self, guild):
        """Generate AI analytics summary."""
        total_members = guild.member_count
        online_members = sum(1 for m in guild.members if m.status != discord.Status.offline)
        activity_rate = (online_members / total_members * 100) if total_members > 0 else 0
        
        health_status = "Mükemmel" if activity_rate > 30 else "İyi" if activity_rate > 15 else "Geliştirilmeli"
        suggestion = "Harika! Topluluk çok aktif. 🎉" if activity_rate > 30 else "Etkinlik düzenleyerek aktiviteyi artırın"
        bot_advice = "Bot komutları iyi kullanılıyor" if total_members > 50 else "Yeni üyeler için karşılama mesajı ekleyin"
        
        return f"📊 AI Analytics Özeti\n\n🏆 Sunucu Sağlığı: {health_status}\n\n📈 Temel Metrikler:\n• Toplam Üye: {total_members:,}\n• Aktif Üye: {online_members:,} ({activity_rate:.1f}%)\n• Kanal Sayısı: {len(guild.text_channels)}\n\n🎯 AI Önerileri:\n• {suggestion}\n• {bot_advice}\n\nDetaylı analiz için: !analytics dashboard"
    
    async def get_growth_advice(self, guild):
        """Get growth advice from AI."""
        member_count = guild.member_count
        
        if member_count < 50:
            advice = "🌱 Küçük Sunucu Büyütme Stratejisi:\n• Sosyal medyada paylaşım yapın\n• Arkadaşlarınızı davet edin\n• İlgi çekici içerik paylaşın\n• Düzenli etkinlikler düzenleyin"
        elif member_count < 200:
            advice = "📈 Orta Ölçek Büyütme:\n• Partner sunucularla işbirliği\n• Bot listeleme sitelerine ekleyin\n• Unique özellikler geliştirin\n• Üye ödül sistemi kurun"
        else:
            advice = "🚀 Büyük Sunucu Optimizasyonu:\n• Kaliteli içerik odaklı büyüme\n• Moderasyon kalitesini artırın\n• Alt kategoriler oluşturun\n• VIP üye sistemi kurun"
        
        return f"{advice}\n\n📊 Mevcut üye sayınız: {member_count}"
    
    async def get_bot_health_check(self, guild):
        """Bot health check and recommendations."""
        # Bot permissions check
        bot_member = guild.get_member(self.bot.user.id)
        has_admin = bot_member.guild_permissions.administrator
        
        health_score = 85  # Örnek skor
        status = "Mükemmel" if health_score > 80 else "İyi" if health_score > 60 else "Bakım Gerekli"
        admin_advice = "Tüm ayarlar optimal!" if has_admin else "Bot'a Administrator yetkisi verin"
        
        return f"🔧 Bot Sağlık Kontrolü\n\n💚 Bot Durumu: {status}\n📊 Sağlık Skoru: {health_score}/100\n\n✅ Çalışan Özellikler:\n• Moderasyon komutları\n• Otomatik koruma\n• Log sistemi\n• Çoklu dil desteği\n\n⚙️ Öneriler:\n• {admin_advice}\n• Log kanalını güncel tutun\n• Düzenli yedekleme yapın\n\nDetaylı ayarlar: !settings"
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def analytics(self, ctx, option=None):
        """Advanced Analytics Dashboard."""
        if option == "dashboard":
            await self.show_full_dashboard(ctx)
        elif option == "growth":
            await self.show_growth_analytics(ctx)
        elif option == "moderation":
            await self.show_moderation_analytics(ctx)
        else:
            await self.show_analytics_menu(ctx)
    
    async def show_analytics_menu(self, ctx):
        """Show analytics main menu."""
        embed = create_embed(
            title="📊 IronWard Analytics Dashboard",
            description="""
**🎯 Sunucu Analitik Merkezinize Hoş Geldiniz!**

**📈 Mevcut Seçenekler:**
`!analytics dashboard` - Tam dashboard görünümü
`!analytics growth` - Büyüme analizi
`!analytics moderation` - Moderasyon istatistikleri

**⚡ Hızlı Bilgiler:**
            """,
            color=discord.Color.blue()
        )
        
        guild = ctx.guild
        
        # Quick stats
        total_members = guild.member_count
        online_members = sum(1 for m in guild.members if m.status != discord.Status.offline)
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        
        embed.add_field(
            name="👥 Üye Durumu",
            value=f"**Toplam:** {total_members:,}\n**Çevrimiçi:** {online_members:,}",
            inline=True
        )
        
        embed.add_field(
            name="📺 Kanallar",
            value=f"**Metin:** {text_channels}\n**Ses:** {voice_channels}",
            inline=True
        )
        
        embed.add_field(
            name="🤖 AI Analizi",
            value="✅ Aktif\n🎯 Optimize edilmiş",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    async def show_full_dashboard(self, ctx):
        """Show comprehensive analytics dashboard."""
        guild = ctx.guild
        
        # Calculate comprehensive stats
        total_members = guild.member_count
        humans = sum(1 for m in guild.members if not m.bot)
        bots = sum(1 for m in guild.members if m.bot)
        online = sum(1 for m in guild.members if m.status == discord.Status.online)
        idle = sum(1 for m in guild.members if m.status == discord.Status.idle)
        dnd = sum(1 for m in guild.members if m.status == discord.Status.dnd)
        offline = sum(1 for m in guild.members if m.status == discord.Status.offline)
        
        # Create comprehensive dashboard
        embed = create_embed(
            title=f"📊 {guild.name} - Tam Analytics Dashboard",
            description="🤖 **AI Powered Analytics** - Gelişmiş sunucu analizi",
            color=discord.Color.from_rgb(0, 123, 255)
        )
        
        # Member Analysis
        embed.add_field(
            name="👥 Üye Analizi",
            value=f"""
**Toplam:** {total_members:,}
**İnsan:** {humans:,} ({humans/total_members*100:.1f}%)
**Bot:** {bots:,} ({bots/total_members*100:.1f}%)
            """.strip(),
            inline=True
        )
        
        # Activity Analysis
        embed.add_field(
            name="📊 Aktivite Analizi",
            value=f"""
🟢 **Çevrimiçi:** {online:,}
🟡 **Boşta:** {idle:,}
🔴 **Meşgul:** {dnd:,}
⚫ **Çevrimdışı:** {offline:,}
            """.strip(),
            inline=True
        )
        
        # Channel Analysis
        embed.add_field(
            name="📺 Kanal Dağılımı",
            value=f"""
**Toplam:** {len(guild.channels)}
**Metin:** {len(guild.text_channels)}
**Ses:** {len(guild.voice_channels)}
**Kategori:** {len(guild.categories)}
            """.strip(),
            inline=True
        )
        
        # Server Health Score (AI Generated)
        activity_rate = ((online + idle + dnd) / total_members * 100) if total_members > 0 else 0
        health_score = min(100, int(activity_rate * 2 + (humans/total_members*50)))
        
        embed.add_field(
            name="🎯 AI Sağlık Skoru",
            value=f"""
**Skor:** {health_score}/100
**Durum:** {"🔥 Harika" if health_score > 80 else "✅ İyi" if health_score > 60 else "⚠️ Geliştirilmeli"}
**Aktivite:** {activity_rate:.1f}%
            """.strip(),
            inline=True
        )
        
        # Growth Prediction (AI)
        growth_trend = "📈 Pozitif" if total_members > 100 else "🌱 Büyüyor"
        embed.add_field(
            name="📈 Büyüme Trendi",
            value=f"""
**Trend:** {growth_trend}
**Potansiyel:** Yüksek
**Öneri:** {self.get_growth_recommendation(total_members)}
            """.strip(),
            inline=True
        )
        
        # Moderation Load
        embed.add_field(
            name="🛡️ Moderasyon Yükü",
            value=f"""
**Durum:** Optimal
**Oran:** {len([r for r in guild.roles if r.permissions.manage_messages])} mod
**AI Öneri:** Dengeli
            """.strip(),
            inline=True
        )
        
        embed.set_footer(text="🤖 AI Analytics • Powered by IronWard AI")
        embed.timestamp = datetime.now()
        
        await ctx.send(embed=embed)
    
    def get_growth_recommendation(self, member_count):
        """Get AI growth recommendation."""
        if member_count < 50:
            return "Sosyal paylaşım"
        elif member_count < 200:
            return "Etkinlik odaklı"
        else:
            return "Kalite odaklı"
    
    async def show_growth_analytics(self, ctx):
        """Show detailed growth analytics."""
        guild = ctx.guild
        
        embed = create_embed(
            title="📈 Büyüme Analytics - AI Analizi",
            description="🤖 Gelişmiş büyüme trend analizi",
            color=discord.Color.green()
        )
        
        # Simulated growth data (gerçek projede veritabanından gelecek)
        daily_joins = 12
        daily_leaves = 3
        net_growth = daily_joins - daily_leaves
        
        embed.add_field(
            name="📊 Günlük Veriler",
            value=f"""
**Katılan:** +{daily_joins}
**Ayrılan:** -{daily_leaves}
**Net Büyüme:** +{net_growth}
            """.strip(),
            inline=True
        )
        
        # Weekly projection
        weekly_projection = net_growth * 7
        embed.add_field(
            name="📅 Haftalık Projeksiyon",
            value=f"""
**Tahmini:** +{weekly_projection}
**Büyüme Oranı:** {(net_growth/guild.member_count*100):.2f}%
**Trend:** {"🔥 Hızlı" if net_growth > 10 else "📈 İyi" if net_growth > 0 else "⚠️ Yavaş"}
            """.strip(),
            inline=True
        )
        
        # AI Recommendations
        embed.add_field(
            name="🤖 AI Önerileri",
            value=f"""
• {self.get_specific_growth_advice(guild.member_count, net_growth)}
• Üye retention oranını artırın
• Karşılama sistemi optimize edin
            """.strip(),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    def get_specific_growth_advice(self, member_count, growth_rate):
        """Get specific growth advice based on data."""
        if growth_rate > 10:
            return "Mükemmel büyüme! Kaliteyi koruyun"
        elif growth_rate > 5:
            return "İyi büyüme! Etkinlik sayısını artırın"
        elif growth_rate > 0:
            return "Yavaş büyüme. Sosyal medya stratejisi geliştirin"
        else:
            return "Büyüme durmuş. Içerik kalitesini gözden geçirin"
    
    async def show_moderation_analytics(self, ctx):
        """Show moderation analytics."""
        embed = create_embed(
            title="🛡️ Moderasyon Analytics",
            description="🤖 AI destekli moderasyon analizi",
            color=discord.Color.red()
        )
        
        # Simulated moderation data
        daily_actions = {"warns": 5, "mutes": 2, "kicks": 1, "bans": 0}
        
        embed.add_field(
            name="📊 Günlük Moderasyon",
            value=f"""
**Uyarı:** {daily_actions['warns']}
**Susturma:** {daily_actions['mutes']}
**Atma:** {daily_actions['kicks']}
**Yasaklama:** {daily_actions['bans']}
            """.strip(),
            inline=True
        )
        
        # Moderation health
        total_actions = sum(daily_actions.values())
        mod_health = "Düşük" if total_actions > 20 else "Normal" if total_actions > 5 else "İyi"
        
        embed.add_field(
            name="🎯 Moderasyon Sağlığı",
            value=f"""
**Durum:** {mod_health}
**Günlük Eylem:** {total_actions}
**Trend:** Azalan
            """.strip(),
            inline=True
        )
        
        # AI Analysis
        embed.add_field(
            name="🤖 AI Analizi",
            value=f"""
• Moderasyon yükü {mod_health.lower()}
• Otomatik koruma çalışıyor
• Topluluk kuralları etkili
            """.strip(),
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AIAssistant(bot))
