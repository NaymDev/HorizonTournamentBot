import logging
from logging.handlers import RotatingFileHandler
import discord
from discord.ext import commands
from discord import app_commands

from challonge.client import ChallongeClient
from core.repositories.members import MemberRepository
from db import models
from core.repositories.minecraft import MinecraftRepository
from core.repositories.players import PlayerRepository
from config import CONFIG
from core.repositories.messages import MessageRepository
from core.repositories.teams import TeamRepository
from core.repositories.tournaments import TournamentRepository
from core.services.signups import DuplicateTeamMemberError, PlayerAlreadyInATeam, SignupClosed, SignupError, SignupService, TeamNameTaken, TeamNameTooLong, TournamentNotFound, UnregisteredPlayersError
from core.services.teamreactions import TeamReactionService
from db.session import SessionLocal

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('cogs.signups.log', maxBytes=1000000, backupCount=3)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class SignupCog(commands.Cog):
    def __init__(self, bot, session_factory):
        self.bot: commands.Bot = bot
        self.session_factory = session_factory

    @commands.Cog.listener()
    async def on_ready(self):
        signup_channel = await self.bot.fetch_channel(CONFIG.signups.signup_channel_id)
        if signup_channel is None:
            logger.error(f"Signup channel with ID {CONFIG.signups.signup_channel_id} not found.")
            return
        
        async with self.session_factory() as session:
            team_repo = TeamRepository(session)
            message_repo = MessageRepository(session)
            tournament_repo = TournamentRepository(session)
            member_repo = MemberRepository(session)
            player_repo = PlayerRepository(session)
            challonge_client = ChallongeClient(CONFIG.challonge.api_key)
            service = TeamReactionService(team_repo, message_repo, member_repo, tournament_repo, player_repo, challonge_client)
            
            signup_messages = await message_repo.get_all_signup_messages()
            for msg in signup_messages:
                channel = self.bot.get_channel(msg.discord_channel_id) or await self.bot.fetch_channel(msg.discord_channel_id)
                discord_message = await channel.fetch_message(int(msg.discord_message_id))
                
                if discord_message is None:
                    logger.warning(f"Signup Message with ID {msg.discord_message_id} not found in channel {msg.discord_channel_id}.")
                    continue

                await service.handle_signup_reaction_check(discord_message)
    
    @app_commands.command(
        name="signup",
        description="Register your team",
    )
    @app_commands.describe(
        team_name="Your team’s name (≤20 chars)",
        p1="Team member 1 (must be verified)",
        p2="Team member 2 (must be verified)",
        p3="Team member 3 (must be verified)",
    )
    async def signup(
        self,
        interaction: discord.Interaction,
        team_name: str,
        p1: discord.Member,
        p2: discord.Member,
        p3: discord.Member,
    ) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        async with self.session_factory() as session:
            tournament_repo = TournamentRepository(session)
            team_repo = TeamRepository(session)
            player_repo = PlayerRepository(session)
            minecraft_repo = MinecraftRepository(session)
            message_repo = MessageRepository(session)
            member_repo = MemberRepository(session)
            
            service = SignupService(tournament_repo, team_repo, player_repo, minecraft_repo, message_repo, member_repo)
            
            try:
                msg = await service.signup_team(    
                    channel_id=str(interaction.channel_id),
                    team_name=team_name,
                    members=[p1, p2, p3, interaction.user],
                    message_send=lambda team, members_discord_ids: self.send_singup_message(interaction.channel, team, members_discord_ids)
                )
                await TeamReactionService(team_repo, MessageRepository(session), MemberRepository(session), tournament_repo, player_repo).handle_signup_reaction_check(msg)
                await self.dm_team_status_to_members((await message_repo.get_by_discord_message_id(msg.id)).team_id, msg)
                
                await interaction.followup.send(f"✅ Team '{team_name}' successfully registered!", ephemeral=True)
            except TournamentNotFound:
                await interaction.followup.send("⚠️ No tournament is active in this channel. Please check the tournament channel.", ephemeral=True)
            except SignupClosed:
                await interaction.followup.send("🚫 Signup period is over. Please wait for the next tournament.", ephemeral=True)
            except TeamNameTooLong as e:
                await interaction.followup.send(f"⚠️ Team name must be {e.max_length} characters or less.", ephemeral=True)
            except TeamNameTaken as e:
                await interaction.followup.send(f"⚠️ Team name '{e.team.team_name}' is already taken. Please choose a different name.", ephemeral=True)    
            except DuplicateTeamMemberError:
                await interaction.followup.send("⚠️ A team cannot have duplicate members. Please ensure all members are unique.", ephemeral=True)
            except UnregisteredPlayersError as e:
                await interaction.followup.send(embed=self._create_unregistered_players_embed(e), ephemeral=True)
            except PlayerAlreadyInATeam as e:
                await interaction.followup.send(f"⚠️ Player <@{e.player}> is already in a team. Please remove them from their current team before signing up.", ephemeral=True)
            except SignupError as e:
                await interaction.followup.send(f"⚠️ Signup failed: {str(e)}", ephemeral=True)
            except Exception as e:
                await interaction.followup.send("⚠️ An unexpected error occurred. If this keeps happening please open a ticket!", ephemeral=True)
                raise e
            
    async def send_singup_message(self, channel: discord.TextChannel, team: models.Teams, members_discord_ids: list[int]) -> discord.Message:
        print(f"Sending signup message to channel {channel.id}...")
        msg = await channel.send(embed=discord.Embed(
            title=team.team_name,
            description="\n".join([f"<:pr_enter:1370057653606154260> `👤` <@{user_id}>" for user_id in members_discord_ids])
        ).set_footer(text="React ✅ to approve or ⛔ to deny"))
        return msg
    
    def _create_unregistered_players_embed(self, error: UnregisteredPlayersError) -> discord.Embed:
        embed = discord.Embed(
            title="Unregistered Players",
            description="Some players don't have a linked Minecraft account.",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Unregistered Players",
            value = ", ".join(f"<@{id}>" for id in error.unregistered_ids),
            inline=False
        )
        embed.set_footer(text="Please make sure all players are registered before signing up.")
        return embed
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.on_raw_reaction_action(payload)
        
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self.on_raw_reaction_action(payload)
    
    async def on_raw_reaction_action(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
        
        async with self.session_factory() as session:
            tournament_repo = TournamentRepository(session)
            if not await tournament_repo.get_tournament_for_signup_channel_id(payload.channel_id):
                return
            
            channel = self.bot.get_channel(payload.channel_id) or await self.bot.fetch_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            
            team_repo = TeamRepository(session)
            message_repo = MessageRepository(session)
            member_repo = MemberRepository(session)
            player_repo = PlayerRepository(session)
            
            service = TeamReactionService(team_repo, message_repo, member_repo, tournament_repo, player_repo)
            
            await service.handle_signup_reaction_check(message)
    
    async def dm_team_status_to_members(self, team_id: int, signup_message: discord.Message):
        async with self.session_factory() as session:
            team_repo = TeamRepository(session)
            member_repo = MemberRepository(session)
            player_repo = PlayerRepository(session)
            
            team = await team_repo.get_team_for_team_id(team_id)
            if not team:
                logger.warning(f"Team with ID {team_id} not found.")
                return
            
            members = [await player_repo.get_by_id(member.player_id) for member in await member_repo.get_members_for_team(team_id)]
            
            for member in members:
                user = self.bot.get_user(int(member.discord_user_id)) or await self.bot.fetch_user(int(member.discord_user_id))
                if user:
                    try:
                        await signup_message.forward(user.dm_channel or await user.create_dm())
                        match team.status:
                            case models.TeamStatus.pending:
                                await user.send(f"*Your signup message needs {len(members)} ✅ reactions, one from each team member to be approved!*")
                            case models.TeamStatus.accepted:
                                await user.send(f"Your team '{team.team_name}' has been successfully registered for the tournament! 🎉\n\n")
                            case models.TeamStatus.denied:
                                await user.send(f"Your team '{team.team_name}' has been denied for the tournament. Please check the signup message for details.")
                    except Exception as e:
                        logger.error(f"Could not send DM to {user.name} ({user.id}). They may have DMs disabled: {str(e)}")
        
        

async def setup(bot):
    if CONFIG.signups.signup_channel_id is None:
        logger.warning("SignupCog not loaded: signup_channel_id is not set.")
        raise commands.ExtensionFailed("Signup channel ID not set in config.")
    await bot.add_cog(SignupCog(bot, SessionLocal))