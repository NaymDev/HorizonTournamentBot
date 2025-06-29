import discord

from core.repositories.members import MemberRepository
from core.repositories.players import PlayerRepository
from core.repositories.tournaments import TournamentRepository
from core.repositories.messages import MessageRepository
from core.repositories.teams import TeamRepository
from db import models

class TeamReactionService:
    def __init__(self, team_repo: TeamRepository, msg_repo: MessageRepository, member_repo: MemberRepository, tournament_repo: TournamentRepository, player_repo: PlayerRepository):
        self.team_repo: TeamRepository = team_repo
        self.msg_repo: MessageRepository = msg_repo
        self.member_repo: MemberRepository = member_repo
        self.tournament_repo: TournamentRepository = tournament_repo
        self.player_repo: PlayerRepository = player_repo

    async def handle_signup_reaction_check(self, discord_message):
        msg_model: models.Messages = await self.msg_repo.get_by_discord_message_id(discord_message.id)
        if not msg_model:
            return
        
        team_id = msg_model.team_id
        
        team = await self.team_repo.get_team_for_team_id(team_id)
        if not team or team.status != models.TeamStatus.pending:
            return
        
        members_discord_ids = [int((await self.player_repo.get_by_id(member.player_id)).discord_user_id) for member in await self.member_repo.get_members_for_team(team_id)]

        await self._clean_invalid_reactions(discord_message, members_discord_ids)

        reactions = await self._collect_reactions(discord_message)
        await self._ensure_reaction_presence(discord_message)
        
        tournament = await self.tournament_repo.get_tournament_for_signup_channel_id(discord_message.channel.id)
        if not tournament or tournament.status != models.TournamentStatus.signups or tournament.signups_locked_reason:
            return
        
        match await self._update_team_status(team_id, reactions, members_discord_ids):
            case models.TeamStatus.accepted:
                await self._handle_team_approved(discord_message, team.team_name, members_discord_ids)

    async def _clean_invalid_reactions(self, message, member_ids):
        for reaction in message.reactions:
            emoji = str(reaction.emoji)
            if emoji not in {"✅", "⛔"}:
                await message.clear_reaction(reaction.emoji)
                continue

            users = [user async for user in reaction.users()]
            for user in users:
                if not user.bot and user.id not in member_ids:
                    await message.remove_reaction(reaction.emoji, user)

    async def _collect_reactions(self, message):
        result = {}
        for reaction in message.reactions:
            emoji = str(reaction.emoji)
            users = [user async for user in reaction.users()]
            result[emoji] = [user.id for user in users if not user.bot]
        return result
    
    async def _ensure_reaction_presence(self, message: discord.Message):
        required_emojis = {"✅", "⛔"}
        bot_user = message.guild.me

        for emoji in required_emojis:
            reaction = next((r for r in message.reactions if str(r.emoji) == emoji), None)

            if reaction:
                users = [user async for user in reaction.users()]
                non_bot_users = [u for u in users if not u.bot]
                bot_reacted = any(u.id == bot_user.id for u in users)

                if not non_bot_users and not bot_reacted:
                    await message.add_reaction(emoji)
                elif non_bot_users and bot_reacted:
                    await message.remove_reaction(emoji, bot_user)
            else:
                await message.add_reaction(emoji)

    async def _update_team_status(self, team_id, reactions, member_ids) -> models.TeamStatus:
        accepted = all(uid in reactions.get("✅", []) for uid in member_ids)
        denied = any(uid in reactions.get("⛔", []) for uid in member_ids)

        
        if denied:
            status = models.TeamStatus.denied
        elif accepted:
            status = models.TeamStatus.accepted
        else:
            status = models.TeamStatus.pending
        
        await self.team_repo.set_status(team_id, status)
        return status
    
    async def _handle_team_approved(self, message: discord.Message, team_name: str, members_discord_ids: list[str]):
        await message.edit(embed=
                     discord.Embed(
                         title= team_name,
                         description="\n".join([f"<:pr_enter:1370057653606154260> <@{user_id}>" for user_id in members_discord_ids]),
                         footer="Team Approved",
                         color=discord.Color.green()
                     )
                    )
        await message.clear_reactions()
        await message.add_reaction("🟢")