# bot/core/registrator.py

import asyncio
from pyrogram import Client
from pyrogram.errors import FloodWait
from pyrogram.types import Message
from pyrogram.filters import command, private

from ..config import settings

async def register_session(client: Client):
    """
    Bu fonksiyon, Telegram web uygulaması üzerinden yetkilendirme işlemini gerçekleştirir.
    """
    try:
        if not client.is_connected:
            await client.connect()

        web_view = await client.invoke(RequestWebView(
            peer=await client.resolve_peer('drumtap_bot'),
            bot=await client.resolve_peer('drumtap_bot'),
            platform='android',
            from_bot_menu=False,
            url='https://drum.wigwam.app'
        ))

        auth_url = web_view.url
        await client.send_message(client.me.id, f"Lütfen bu bağlantıya tıklayarak yetkilendirme yapın: {auth_url}")

    except FloodWait as e:
        await asyncio.sleep(e.x)  # Telegram flood bekleme süresini bekle
    except Exception as error:
        print(f"Yetkilendirme hatası: {error}")

async def register_sessions():
    """
    Tüm oturumları kaydetmek için kullanılır.
    """
    clients = []
    for session_name in get_session_names():
        client = Client(session_name, api_id=settings.API_ID, api_hash=settings.API_HASH, workdir="sessions")
        await client.start()
        clients.append(client)

    tasks = [register_session(client) for client in clients]
    await asyncio.gather(*tasks)

    for client in clients:
        await client.stop()
