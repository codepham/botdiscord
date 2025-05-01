
import discord
import os
import pandas as pd
from discord.ext import commands
import re
from flask import Flask
from threading import Thread
import logging
import datetime
from typing import Optional



# =====================
# 🛠️ CẤU HÌNH HỆ THỐNG
# =====================
ANIME_CSV_FILE = 'https://raw.githubusercontent.com/niyakipham/data/refs/heads/main/anisub/anidata.csv'
COMMAND_PREFIX = '!'
ALLOWED_CHANNEL_IDS = [1290541556733841432, 1366045565871460452]
FLASK_PORT = 8080

# =====================
# 🎨 THIẾT KẾ GIAO DIỆN
# =====================
class SciFiTheme:
    COLORS = {
        'primary': discord.Color.from_rgb(138, 43, 226),  # Purple
        'secondary': discord.Color.from_rgb(0, 255, 255),  # Cyan
        'success': discord.Color.from_rgb(50, 205, 50),   # LimeGreen
        'warning': discord.Color.from_rgb(255, 165, 0),   # Orange
        'danger': discord.Color.from_rgb(220, 20, 60),    # Crimson
        'info': discord.Color.from_rgb(30, 144, 255)      # DodgerBlue
    }
    
    ICONS = {
        'search': 'https://i.pinimg.com/736x/5e/79/8d/5e798d7e97c1f4ab238de322229b305b.jpg',
        'anime': 'https://i.pinimg.com/736x/5e/79/8d/5e798d7e97c1f4ab238de322229b305b.jpg',
        'error': 'https://i.pinimg.com/736x/e6/0e/c4/e60ec4a21dfa69a1596280816cde6c46.jpg',
        'success': 'https://i.pinimg.com/736x/4a/58/0c/4a580cadf8ec1dbb7a9025534631e56c.jpg',
        'system': ''
    }
    
    @staticmethod
    def random_color():
        return discord.Color.from_rgb(
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )

# =====================
# 🖼️ EMBED BUILDER
# =====================
class SciFiEmbed:
    @staticmethod
    def create(title: str, description: str = "", color: Optional[discord.Color] = None):
        """Tạo embed với phong cách sci-fi"""
        embed = discord.Embed(
            title=f"⚡ {title}",
            description=description,
            color=color if color else SciFiTheme.COLORS['primary'],
            timestamp=datetime.datetime.utcnow()
        )
        return embed
    
    @staticmethod
    def add_field(embed, name: str, value: str, inline: bool = False):
        """Thêm field với style sci-fi"""
        embed.add_field(
            name=f"🔮 {name}",
            value=value,
            inline=inline
        )
        return embed
    
    @staticmethod
    def set_thumbnail(embed, url: str):
        """Thiết lập thumbnail"""
        embed.set_thumbnail(url=url)
        return embed
    
    @staticmethod
    def set_image(embed, url: str):
        """Thiết lập ảnh lớn"""
        embed.set_image(url=url)
        return embed
    
    @staticmethod
    def set_footer(embed, text: str = None):
        """Thiết lập footer"""
        embed.set_footer(
            text=text or "Dữ liệu cập nhật đến 5/1/2025 >_<",
            icon_url=SciFiTheme.ICONS['system']
        )
        return embed

# =====================
# 📊 DATA HANDLER
# =====================
class AnimeData:
    def __init__(self):
        self.data = None
        self.logger = logging.getLogger('anime_data')
        
    def load_data(self):
        """Tải dữ liệu anime từ nguồn"""
        self.logger.info(f"Đang tải dữ liệu từ: {ANIME_CSV_FILE}")
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            self.data = pd.read_csv(ANIME_CSV_FILE, storage_options={'User-Agent': headers['User-Agent']})
            self.logger.info(f"✅ Đã tải thành công {len(self.data)} bản ghi")
            return True
        except Exception as e:
            self.logger.error(f"❌ Lỗi khi tải dữ liệu: {e}")
            self.data = pd.DataFrame()
            return False
    
    def search(self, keywords: str, episode: str = None):
        """Tìm kiếm anime theo từ khóa và tập"""
        if self.data is None or self.data.empty:
            self.logger.warning("Dữ liệu chưa được tải hoặc rỗng")
            return None
        
        try:
            keyword_list = keywords.lower().split()
            filtered = self.data.copy()
            
            # Lọc theo từ khóa
            for keyword in keyword_list:
                filtered = filtered[filtered['name'].notna() & 
                                  filtered['name'].str.lower().str.contains(keyword, na=False)]
            
            # Lọc theo tập nếu có
            if episode:
                filtered['episodes_str'] = filtered['episodes'].astype(str)
                filtered = filtered[filtered['episodes_str'] == str(episode).strip()]
            
            return filtered.head(10) if not filtered.empty else None
        except Exception as e:
            self.logger.error(f"Lỗi khi tìm kiếm: {e}")
            return None

# =====================
# 🤖 BOT CORE
# =====================
class AnimeBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.messages = True
        super().__init__(command_prefix=COMMAND_PREFIX, intents=intents)
        
        self.anime_data = AnimeData()
        self.logger = logging.getLogger('anime_bot')
        
    async def on_ready(self):
        self.logger.info(f'✅ {self.user} đã sẵn sàng!')
        self.anime_data.load_data()
        
    async def on_message(self, message):
        if message.author == self.user:
            return
            
        if message.channel.id in ALLOWED_CHANNEL_IDS and not message.content.startswith(COMMAND_PREFIX):
            await self.handle_auto_search(message)
            
        await self.process_commands(message)
    
    async def handle_auto_search(self, message):
        """Xử lý tìm kiếm tự động từ tin nhắn"""
        content = message.content.lower().strip()
        match = re.search(r"(.+?)\s+(?:tập|tap|ep|episode)\s+(\d+)", content)
        
        if not match:
            return
            
        keywords, episode = match.group(1).strip(), match.group(2).strip()
        self.logger.info(f"Tìm kiếm tự động: '{keywords}' - Tập {episode}")
        
        results = self.anime_data.search(keywords, episode)
        
        if results is None or results.empty:
            embed = SciFiEmbed.create(
                title="Không tìm thấy kết quả",
                description=f"Không tìm thấy anime phù hợp với `{keywords}` tập `{episode}`",
                color=SciFiTheme.COLORS['warning']
            )
            embed = SciFiEmbed.set_thumbnail(embed, SciFiTheme.ICONS['error'])
            embed = SciFiEmbed.add_field(embed, "Gợi ý", "• Kiểm tra lại chính tả\n• Thử từ khóa rộng hơn")
            await message.channel.send(embed=embed)
            return
            
        await self.send_search_results(message.channel, keywords, episode, results)
    
    async def send_search_results(self, channel, keywords, episode, results):
        """Gửi kết quả tìm kiếm dưới dạng embed"""
        for _, row in results.iterrows():
            anime_name = row.get('name', 'Không có tên')
            anime_link = row.get('link', '')
            
            embed = SciFiEmbed.create(
                title=anime_name,
                description=f"🌀 **Tập {episode}**",
                color=SciFiTheme.COLORS['secondary']
            )
            
            embed = SciFiEmbed.set_thumbnail(embed, SciFiTheme.ICONS['anime'])
            
            if anime_link and pd.notna(anime_link):
                embed = SciFiEmbed.add_field(
                    embed,
                    "Liên kết truy cập",
                    f"[Khởi chạy trình xem]({anime_link})"
                )
            else:
                embed = SciFiEmbed.add_field(
                    embed,
                    "Liên kết truy cập",
                    "`Hệ thống đang cập nhật liên kết...`"
                )
            
            if 'score' in row and pd.notna(row['score']):
                embed = SciFiEmbed.add_field(
                    embed,
                    "Đánh giá hệ thống",
                    f"⭐ {row['score']}/10",
                    True
                )
                
            if 'year' in row and pd.notna(row['year']):
                embed = SciFiEmbed.add_field(
                    embed,
                    "Năm phát hành",
                    f"📅 {row['year']}",
                    True
                )
            
            embed = SciFiEmbed.set_footer(embed)
            await channel.send(embed=embed)

# =====================
# 🎮 COMMANDS
# =====================
def setup_commands(bot):
    @bot.command(name='ani', help='Tìm kiếm anime theo tên. Ví dụ: !ani One Piece')
    @commands.check(lambda ctx: ctx.channel.id in ALLOWED_CHANNEL_IDS)
    async def search_anime(ctx, *, anime_name: str):
        """Tìm kiếm thông tin anime"""
        if bot.anime_data.data is None or bot.anime_data.data.empty:
            embed = SciFiEmbed.create(
                title="⚠️ Hệ thống tạm ngưng",
                description="Cơ sở dữ liệu anime đang được nâng cấp...",
                color=SciFiTheme.COLORS['danger']
            )
            embed = SciFiEmbed.add_field(
                embed,
                "Thử lại sau",
                "Vui lòng thử lại sau ít phút"
            )
            await ctx.send(embed=embed)
            return
            
        results = bot.anime_data.search(anime_name.strip())
        
        if results is None or results.empty:
            embed = SciFiEmbed.create(
                title="Không tìm thấy kết quả",
                description=f"Không tìm thấy anime nào chứa `{anime_name}`",
                color=SciFiTheme.COLORS['warning']
            )
            await ctx.send(embed=embed)
            return
            
        await send_paginated_results(ctx, anime_name, results)
    
    async def send_paginated_results(ctx, query, results):
        """Gửi kết quả phân trang"""
        items_per_page = 5
        pages = []
        
        for i in range(0, len(results), items_per_page):
            page_data = results.iloc[i:i + items_per_page]
            page_num = (i // items_per_page) + 1
            total_pages = (len(results) + items_per_page - 1) // items_per_page
            
            embed = SciFiEmbed.create(
                title=f"Kết quả tìm kiếm: {query}",
                description=f"📊 **Trang {page_num}/{total_pages}**",
                color=SciFiTheme.COLORS['info']
            )
            
            for _, row in page_data.iterrows():
                anime_title = row.get('name', 'Không rõ tên')
                episode_info = row.get('episodes', 'N/A')
                link_info = row.get('link', '')
                
                value_str = f"```diff\n+ Tập: {episode_info}\n```"
                if link_info and pd.notna(link_info):
                    value_str += f"\n[📡 Kết nối trình xem]({link_info})"
                    
                embed = SciFiEmbed.add_field(
                    embed,
                    f"📺 {anime_title[:100]}",
                    value_str[:1000],
                    False
                )
            
            pages.append(embed)
        
        for page in pages:
            await ctx.send(embed=page)

# =====================
# 🌐 WEB SERVER
# =====================
def run_web_server():
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Kaguya AI Status</title>
            <style>
                body { 
                    font-family: 'Arial', sans-serif; 
                    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
                    color: white;
                    height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    text-align: center;
                }
                .container {
                    background: rgba(0, 0, 0, 0.7);
                    padding: 2rem;
                    border-radius: 15px;
                    box-shadow: 0 0 20px rgba(138, 43, 226, 0.5);
                }
                h1 {
                    color: #8a2be2;
                    text-shadow: 0 0 10px rgba(138, 43, 226, 0.7);
                }
                .status {
                    color: #00ffff;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✨ Kaguya Anime Bot ✨</h1>
                <p>Trạng thái: <span class="status">ĐANG HOẠT ĐỘNG</span></p>
                <p>Phiên bản: Sci-Fi Edition</p>
                <p>Hệ thống đang chạy ổn định</p>
            </div>
        </body>
        </html>
        """
    
    app.run(host='0.0.0.0', port=FLASK_PORT)

# =====================
# 🚀 KHỞI CHẠY HỆ THỐNG
# =====================
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    if not BOT_TOKEN:
        logging.critical("❌ Không tìm thấy BOT_TOKEN!")
        exit(1)
    
    # Khởi chạy web server trong thread riêng
    web_thread = Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Khởi chạy bot Discord
    bot = AnimeBot()
    setup_commands(bot)
    
    try:
        bot.run(BOT_TOKEN)
    except discord.LoginFailure:
        logging.critical("❌ Token không hợp lệ!")
    except Exception as e:
        logging.critical(f"❌ Lỗi không mong muốn: {e}")

bot.run(os.getenv('HAITEN'))
