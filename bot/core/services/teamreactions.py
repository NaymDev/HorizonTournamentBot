import discord

from core.repositories.messages import MessageRepository
from core.repositories.teams import TeamRepository
from db import models

class TeamReactionService:
    def __init__(self, team_repo: TeamRepository, msg_repo: MessageRepository, member_repo):
        self.team_repo: TeamRepository = team_repo
        self.msg_repo: MessageRepository = msg_repo
        self.member_repo = member_repo

    async def handle_signup_reaction_check(self, discord_message):
        msg_model = self.msg_repo.get_by_discord_message_id(discord_message.id)
        team_id = msg_model.team_id
        
        team = await self.team_repo.get_team_for_team_id(team_id)
        if team.status != models.TeamStatus.pending:
            return
        
        member_ids = self.member_repo.get_member_ids(team_id)

        await self._clean_invalid_reactions(discord_message, member_ids)

        reactions = await self._collect_reactions(discord_message)
        await self._ensure_reaction_presence(discord_message)
        await self._update_team_status(team_id, reactions, member_ids)

    async def _clean_invalid_reactions(self, message, member_ids):
        for reaction in message.reactions:
            emoji = str(reaction.emoji)
            if emoji not in {"✅", "❌"}:
                await message.clear_reaction(reaction.emoji)
                continue

            users = await reaction.users().flatten()
            for user in users:
                if not user.bot and user.id not in member_ids:
                    await message.remove_reaction(reaction.emoji, user)

    async def _collect_reactions(self, message):
        result = {}
        for reaction in message.reactions:
            emoji = str(reaction.emoji)
            users = await reaction.users().flatten()
            result[emoji] = [user.id for user in users if not user.bot]
        return result
    
    async def _ensure_reaction_presence(self, message: discord.Message):
        required_emojis = {"✅", "❌"}
        bot_user = message.guild.me

        for emoji in required_emojis:
            reaction = next((r for r in message.reactions if str(r.emoji) == emoji), None)

            if reaction:
                users = await reaction.users().flatten()
                non_bot_users = [u for u in users if not u.bot]
                bot_reacted = any(u.id == bot_user.id for u in users)

                if not non_bot_users and not bot_reacted:
                    await message.add_reaction(emoji)
                elif non_bot_users and bot_reacted:
                    await message.remove_reaction(emoji, bot_user)
            else:
                await message.add_reaction(emoji)

    async def _update_team_status(self, team_id, reactions, member_ids):
        accepted = all(uid in reactions.get("✅", []) for uid in member_ids)
        denied = any(uid in reactions.get("❌", []) for uid in member_ids)

        if denied:
            await self.team_repo.set_status(team_id, models.TeamStatus.denied)
        elif accepted:
            await self.team_repo.set_status(team_id, models.TeamStatus.accepted)
        else:
            await self.team_repo.set_status(team_id, models.TeamStatus.pending)
