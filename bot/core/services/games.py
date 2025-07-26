import asyncio
import random
import string
import discord
from discord.ext import commands

from core.repositories.players import PlayerRepository
from core.services.dm_notification import ModelTeamMembersGroup
from config import CONFIG
from core.repositories.members import MemberRepository
from core.repositories.minecraft import MinecraftRepository
from core.repositories.teams import TeamRepository
from core.repositories.tournaments import TournamentRepository

FACTIONS = [
    "THR",  # Throneshard
    "OBL",  # Oblivion
    "KRA",  # Krakspire
    "ZNT",  # Zenith
    "VEX",  # Vexforge
    "DWN",  # Duskwind
    "NYX",  # Nyxshade
    "AXL",  # Axleon
    "GRM",  # Grimvale
    "LDN",  # Lodenfell
]

CONSONANTS = "BCDFGHJKLMNPQRSTVWXYZ"

class GameService:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tournament_repo: TournamentRepository
        self.team_repo: TeamRepository
        self.member_repo: MemberRepository
        self.minecraft_repo: MinecraftRepository
        self.player_repo: PlayerRepository
    
    async def create_game(self, team_ids: list[str]) -> None:
        if len(team_ids) < 2:
            raise ValueError("At least two team IDs are required to create a game.")
        elif any(team_id is None for team_id in team_ids):
            raise ValueError("One or more team IDs are None.")
        elif len(set(team_ids)) < len(team_ids):
            raise ValueError("Duplicate team IDs found.")
        
        teams = [await self.team_repo.get_team_for_team_id(team_id) for team_id in team_ids]
        
        if any(team is None for team in teams):
            raise ValueError("One or more teams not found.")
        elif not all(team.tournament_id is teams[0].tournament_id for team in teams):
            raise ValueError("Teams are not in the same tournament.")
        
        tournament = await self.tournament_repo.get_tournament_by_id(teams[0].tournament_id)
        
        texts_category = self.bot.get_channel(tournament.game_texts_category_id) or await self.bot.fetch_channel(tournament.game_texts_category_id)
        if texts_category is None:
            raise ValueError("Game texts category not found.")
        elif not isinstance(texts_category, discord.CategoryChannel):
            raise ValueError("Game texts category is not a category channel.")
        
        voice_category = self.bot.get_channel(tournament.game_vc_category_id) or await self.bot.fetch_channel(tournament.game_vc_category_id)
        if voice_category is None:
            raise ValueError("Game vc category not found.")
        elif not isinstance(voice_category, discord.CategoryChannel):
            raise ValueError("Game vc category is not a category channel.")
        
        game_id = self._generate_game_id()
        
        game_text_channel = await texts_category.create_text_channel(
            f"game-{game_id}",
        )
        # This hole func can be imrpoved a lot! Especially the section below generating the embeds. Eg by just looping trough all teams once and adding fields to both embeds
        embed = discord.Embed(
            color=discord.Color.from_rgb(224, 122, 36),
            title=f"`🎮` Game `{game_id}`"
        ).set_footer(
            text="discord.gg/tourney",
            icon_url=self.bot.user.display_avatar.url
        )
        for i, team in enumerate(teams, start=1):
            group = await ModelTeamMembersGroup.create(await self.member_repo.get_members_for_team(team.id), self.player_repo)
            embed.add_field(
                name=f"`{self._number_to_emoji(i)}` **{team.team_name}**",
                value="\n".join([f"{CONFIG.styles.pr_enter_emoji} `👤` <@{user_id}>" for user_id in group.get_target_discord_ids()]),
                inline=True
            )
        await game_text_channel.send(embed=embed)
        
        embed = discord.Embed(
            color=discord.Color.from_rgb(224, 122, 36),
            title="Party Commands",
        ).set_footer(
            text="Game in progress",
            icon_url=self.bot.user.display_avatar.url
        )
        for i, team in enumerate(teams, start=1):
            async def get_minecraft_username(member):
                mc_account = await self.minecraft_repo.get_by_player_id(member.player_id)
                return mc_account.minecraft_username if mc_account else "_Unknown_"

            minecraft_usernames = await asyncio.gather(*(get_minecraft_username(member) for member in await self.member_repo.get_members_for_team(team.id)))
            embed.add_field(
                name=f"Party Command {i}",
                value=f"```/p {" ".join(minecraft_usernames)}```",
                inline=False
            )
        await game_text_channel.send(embed=embed)
    
    
    def _generate_rune(self):
        pattern = [
            random.choice(CONSONANTS),
            random.choice(CONSONANTS),
            random.choice(string.digits),
            random.choice(CONSONANTS)
        ]
        return ''.join(pattern)

    def _generate_game_id(self):
        faction = random.choice(FACTIONS)
        rune = self._generate_rune()
        return f"{faction}-{rune}"
    
    def _number_to_emoji(self, num):
        if 0 <= num <= 9:
            return chr(ord('0') + num) + '\uFE0F\u20E3'
        else:
            return f"[{num}]"