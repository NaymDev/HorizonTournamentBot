import discord
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

class NoDiscordTagOnHypixel(AccountLinkError):
    pass

class DiscordTagMissmatch(AccountLinkError):
    pass

class MinecraftAccountService:
    def __init__(self, minecraft_repo: MinecraftRepository, player_repo: PlayerRepository):
        self.minecraft_repo: MinecraftRepository = minecraft_repo
        self.player_repo: PlayerRepository = player_repo

    async def link_account(self, discord_member: discord.Member, uuid: str, username: str):
        player = await self.player_repo.get_by_discord_id(discord_member.id)
        if not player:
            raise PlayerNotFound("Player not found for the provided Discord user ID")
        
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
        return True