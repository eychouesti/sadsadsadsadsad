import asyncio
import time
from datetime import datetime
from urllib.parse import unquote

import aiohttp
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.functions.messages import RequestWebView
from pyrogram.types import Message
from pyrogram.filters import command, private

from bot.config.config import settings  # Doğru içe aktarma
from bot.utils.logger import logger
from bot.exceptions import InvalidSession

class WigwamClaimer:
    def __init__(self, client: Client):
        self.client = client
        self.session_name = client.name
        self.is_authorized = False
        self.auth_code = None

    async def get_tg_web_data(self) -> str:
        try:
            if not self.client.is_connected:
                await self.client.connect()

            web_view = await self.client.invoke(RequestWebView(
                peer=await self.client.resolve_peer('drumtap_bot'),
                bot=await self.client.resolve_peer('drumtap_bot'),
                platform='android',
                from_bot_menu=False,
                url='https://drum.wigwam.app'
            ))

            auth_url = web_view.url
            tg_web_data = unquote(
                string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0])

            return tg_web_data

        except Exception as error:
            logger.error(f"{self.session_name} | Telegram web verileri alınamadı: {error}")
            await asyncio.sleep(delay=3)

    async def get_drum_game_data(self, user_id) -> dict:
        try:
            headers = {"Authorization": f"Bearer {settings.API_TOKEN}"} 
            response = requests.post(f"{settings.API_BASE_URL}/getUserInfo", json={"devAuthData": user_id, "authData": await self.get_tg_web_data(), "platform": "web", "data": {}}, headers=headers)
            response.raise_for_status()

            response_json = response.json()
            drum_game_data = response_json['data']
            return drum_game_data
        except Exception as error:
            logger.error(f"{self.session_name} | Kullanıcı bilgileri alınamadı: {error}")
            await asyncio.sleep(delay=3)

    async def tap_drum(self, user_id) -> bool:
        try:
            headers = {"Authorization": f"Bearer {settings.API_TOKEN}"}
            response = requests.post(f"{settings.API_BASE_URL}/tapDrum", json={"userId": user_id}, headers=headers)
            response.raise_for_status()

            log(f"{self.session_name} | Tap işlemi başarılı: {response.json()}")
            return True
        except Exception as error:
            log(f"{self.session_name} | Tap işlemi başarısız: {error}")
            await asyncio.sleep(delay=3)
            return False

    async def claim_farm_reward(self, user_id) -> bool:
        try:
            headers = {"Authorization": f"Bearer {settings.API_TOKEN}"}
            response = requests.post(f"{settings.API_BASE_URL}/claimFarm", headers=headers)
            response.raise_for_status()

            response_json = await response.json()
            claimed_balance = response_json['data']['claimedBalance']

            log(f"{self.session_name} | Çiftlik ödülü başarıyla toplandı: {claimed_balance} DRUM")
            return True
        except Exception as error:
            log(f"{self.session_name} | Çiftlik ödülü toplama başarısız: {error}")
            await asyncio.sleep(delay=3)
            return False

    async def on_message(self, client: Client, message: Message):
        if message.text and message.text.startswith("/baslat") and not self.is_authorized:
            await self.send_auth_code(message.from_user.id)
        elif message.text and self.auth_code:
            if message.text == self.auth_code:
                self.is_authorized = True
                await message.reply_text("Doğrulama başarılı! Bot başlatılıyor...")
                await self.run(message)
            else:
                await message.reply_text("Yanlış doğrulama kodu. Lütfen tekrar deneyin.")

    async def send_auth_code(self, user_id):
        self.auth_code = str(random.randint(100000, 999999))
        await self.client.send_message(user_id, f"Doğrulama kodu: {self.auth_code}")

    async def run(self, message) -> None:
        try:
            proxy_connector = ProxyConnector().from_url(settings.PROXY_URL) if settings.USE_PROXY else None
            async with aiohttp.ClientSession(connector=proxy_connector) as http_client:
                while self.is_authorized:
                    user_info = await self.get_drum_game_data(message.from_user.id)

                    if user_info["availableTaps"] > 0:
                        await self.tap_drum(message.from_user.id)
                    else:
                        remaining_time = user_info["currentTapWindowFinishIn"] / 1000
                        log(f"{self.session_name} | Tap hakkı yok. Kalan süre: {remaining_time} saniye")
                        time.sleep(remaining_time)

                    await asyncio.sleep(settings.TAP_INTERVAL)
                    await self.claim_farm_reward(message.from_user.id)
                    await asyncio.sleep(settings.CLAIM_FARM_INTERVAL)
        except FloodWait as e:
            logger.info(f"{self.session_name} Flood beklemede. Kalan süre: {e.x} saniye")
            await asyncio.sleep(e.x)
            await self.run(message)
        except InvalidSession:
            logger.error(f"{self.session_name} | Invalid Session")
            self.is_authorized = False
            await self.client.send_message(message.from_user.id, "Oturum geçersizleşti. Lütfen tekrar /baslat komutunu kullanın.")
        except Exception as e:
            logger.error(f"Hata oluştu: {e}")
            await asyncio.sleep(5)  


async def main():
    app = Client("my_bot", api_id=settings.API_ID, api_hash=settings.API_HASH)
    claimer = WigwamClaimer(app)

    with app:
        @app.on_message(filters.command("baslat") & filters.private)
        async def start_command(client, message: Message):
            await message.reply_text("Bot başlatılıyor...")
            await claimer.run(message)

        await app.run()

if __name__ == "__main__":
    asyncio.run(main())
