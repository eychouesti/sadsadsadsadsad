# bot/launcher.py

import asyncio
import argparse
from itertools import cycle

from pyrogram import Client

from ..config import settings
from ..utils import logger
from .claimer import WigwamClaimer
from .registrator import register_sessions

start_text = """
Wigwam Drum Game Botu

Seçenekler:

1. Oturum Oluştur
2. Botu Başlat
"""

def get_session_names():
    # ... (sessions klasöründeki oturum dosyalarını okuyun)

def get_proxies():
    # ... (proxy'leri okuyun - eğer kullanılacaksa)

async def get_tg_clients() -> list[Client]:
    # ... (Pyrogram istemcilerini oluşturun)

async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--action', type=int, help='Yapılacak eylem (1: Oturum Oluştur, 2: Botu Başlat)')
    args = parser.parse_args()

    if not args.action:
        print(start_text)
        while True:
            action = input("Seçiminiz (1 veya 2): ")
            if action in ["1", "2"]:
                action = int(action)
                break
            else:
                print("Geçersiz seçim. Lütfen 1 veya 2 girin.")
    else:
        action = args.action

    if action == 1:
        await register_sessions()
    elif action == 2:
        tg_clients = await get_tg_clients()
        await run_tasks(tg_clients)

async def run_tasks(tg_clients: list[Client]):
    proxies = get_proxies()
    proxy_cycle = cycle(proxies) if proxies else None
    tasks = [
        asyncio.create_task(WigwamClaimer(client).run(next(proxy_cycle) if proxy_cycle else None))
        for client in tg_clients
    ]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(process())
