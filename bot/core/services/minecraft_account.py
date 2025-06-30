import discord
from mojang import fetch_minecraft_username, fetch_minecraft_uuid
from config import CONFIG
from hypixel import fetch_hypixel_discord_tag
from core.repositories.minecraft import MinecraftRepository
from core.repositories.players import PlayerRepository

class AccountLinkError(Exception):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code

class PlayerNotFound(AccountLinkError):
    pass

class MinecraftAccountNotFound(AccountLinkError):
    def __init__(self, username: str):
        super().__init__(f"No Minecraft account found for username: {username}", code="minecraft_account_not_found")
        self.username = username

class NoDiscordTagOnHypixel(AccountLinkError):
    pass

class DiscordTagMissmatch(AccountLinkError):
    pass

class MinecraftAccountService:
    def __init__(self, minecraft_repo: MinecraftRepository, player_repo: PlayerRepository):
        self.minecraft_repo: MinecraftRepository = minecraft_repo
        self.player_repo: PlayerRepository = player_repo

    async def link_account(self, discord_member: discord.Member, username: str):
        player = await self.player_repo.get_by_discord_id(discord_member.id)
        if not player:
            raise PlayerNotFound("Player not found for the provided Discord user ID")
        
        uuid = await fetch_minecraft_uuid(username)
        if not uuid:
            raise MinecraftAccountNotFound(username)
        
        try:
            discord_tag = await fetch_hypixel_discord_tag(CONFIG.hypixel.api_key, uuid)
        except Exception as e:
            raise AccountLinkError(f"Failed to fetch Discord tag from Hypixel: {str(e)}")
        if not discord_tag:
            raise NoDiscordTagOnHypixel()
        if discord_tag != discord_member.id and discord_tag != discord_member.name:
            raise DiscordTagMissmatch("Discord tag from Hypixel does not match the player's Discord ID")

        existing = await self.minecraft_repo.get_by_player_id(player.id)
        if existing:
            await self.minecraft_repo.update_account(player.id, uuid, username)
        else:
            await self.minecraft_repo.create_account(player.id, uuid, username)

        await self.minecraft_repo.log_history(player.id, uuid, username, change_type="linked")
        await self.update_discord_nick(member=discord_member, username=username)

    async def update_discord_nick(self, member: discord.Member, username: str = None):
        if not username:
            player = await self.player_repo.get_by_discord_id(member.id)
            if not player:
                raise PlayerNotFound("Player not found for the provided Discord user ID")

            minecraft_account = await self.minecraft_repo.get_by_player_id(player.id)
            if not minecraft_account:
                await member.edit(nick=None)
                return

            username = await fetch_minecraft_username(minecraft_account.minecraft_uuid) or minecraft_account.minecraft_username
            self.minecraft_repo.update_account(player.id, minecraft_account.minecraft_uuid, username)
            
        await member.edit(nick=username)

# TODO: (next) add a method to ensure the Discord members nick = minecraft username
# TODO: (next) fetching the Minecraft username from the UUID should be done inside the service layer (aka. inside link_account) and not pased as an arg