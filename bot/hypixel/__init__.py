from typing import Optional
from aiohttp import ClientTimeout
import aiohttp

async def fetch_hypixel_discord_tag(api_key: str, uuid: str) -> Optional[str]:
    hypixel_url = f"https://api.hypixel.net/player?key={api_key}&uuid={uuid}"
    fetched_discord_tag = None

    async with aiohttp.ClientSession(timeout=ClientTimeout(total=10)) as sess:
        async with sess.get(hypixel_url) as resp:
            if resp.status == 200:
                result = await resp.json()
                if result.get("success") and result.get("player"):
                    links = result["player"].get("socialMedia", {}).get("links", {})
                    fetched_discord_tag = links.get("DISCORD")
            else:
                raise Exception(
                    f"Failed to fetch data from Hypixel API. Status code: {resp.status}"
                )

    return fetched_discord_tag
