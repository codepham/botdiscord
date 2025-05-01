from discord.ext import commands, tasks
import requests, discord
import asyncio
import random, os
from dotenv import load_dotenv

# ID kênh mặc định để gửi ảnh
load_dotenv()
TOKEN = os.getenv('HAITEN')

KISS_ID  = 1367407970304000032

# Danh sách các loại ảnh (sfw)
haiten = ["waifu", "neko" "trap", "blowjob"]

intents = discord.Intents.default()


bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@tasks.loop(seconds=150)
async def send_waifu_image():
    try:
        # Chọn ngẫu nhiên một loại ảnh
        category = random.choice(haiten)
        
        # Gọi API để lấy URL ảnh
        response = requests.get(f"https://api.waifu.pics/nsfw/{category}")
        response.raise_for_status() # Kiểm tra lỗi HTTP
        image_url = response.json()["url"]

        # Lấy kênh mặc định
        aakis = bot.get_channel(KISS_ID)
        if aakis is None:
            print(f"Không tìm thấy kênh có ID {KISS_ID}")
            return
        
        # Gửi ảnh
        await aakis.send(image_url)

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gọi API: {e}")
    except Exception as e:
        print(f"Lỗi khác: {e}")




@bot.event
async def on_ready():
    print(f"{bot.user} đã kết nối!")
    send_waifu_image.start() # Bắt đầu task

bot.run(TOKEN)
