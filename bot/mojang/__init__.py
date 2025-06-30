from typing import Optional
import aiohttp

async def fetch_minecraft_uuid(username: str) -> Optional[str]:
    """
    Fetch the Minecraft UUID for a given username.

    Args:
        username (str): The Minecraft username to look up.

    Returns:
        Optional[str]: The UUID without dashes if found, or None if not found or an error occurs.
    """
    url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("id")
            elif resp.status == 204:
                return None
            else:
                print(f"Error fetching UUID: HTTP {resp.status}")
                return None

async def fetch_minecraft_username(uuid: str) -> Optional[str]:
    """
    Fetch the Minecraft UUID for a given username.

    Args:
        username (str): The Minecraft username to look up.

    Returns:
        Optional[str]: The UUID without dashes if found, or None if not found or an error occurs.
    """
    url = f"https://api.mojang.com/users/profiles/minecraft/{uuid}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("name")
            elif resp.status == 204:
                return None
            else:
                print(f"Error fetching UUID: HTTP {resp.status}")
                return None