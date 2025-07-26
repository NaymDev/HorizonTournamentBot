from sqlalchemy import (
    Column, Integer, String, DateTime, Enum, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base
import enum
import datetime

Base = declarative_base()

class TournamentStatus(enum.Enum):
    planned = "planned"
    signups = "signups"
    active = "active"
    finished = "finished"
    cancelled = "cancelled"

class TeamStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    substitute = "substitute"

class MatchStatus(enum.Enum):
    open = "open"
    finished = "finished"

class MinecraftAccountHistoryChangeType(enum.Enum):
    linked = "linked"
    unlinked = "unlinked"
    updated = "updated"

class Reaction(enum.Enum):
    accept = "accept"
    reject = "reject"

class PlayerRole(enum.Enum):
    member = "member"
    substitute = "substitute"

class BanType(enum.Enum):
    discord_user = "discord_user"
    minecraft_account = "minecraft_account"

class Tournaments(Base):
    __tablename__ = 'tournaments'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    start_date = Column(DateTime)
    status = Column(Enum(TournamentStatus), default=TournamentStatus.planned)
    
    signup_channel_id = Column(String, nullable=False, unique=True)
    game_texts_category_id = Column(String, nullable=False)
    game_vc_category_id = Column(String, nullable=False)
    
    signups_locked_reason = Column(String, nullable=True)
    
    max_accepted_teams = Column(Integer, default=16)
    
    challonge_tournament_id = Column(String, nullable=True)
    
    brackets = relationship("Brackets", back_populates="tournament")
    teams = relationship("Teams", back_populates="tournament")


class Brackets(Base):
    __tablename__ = 'brackets'
    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey('tournaments.id'), nullable=False)
    round_number = Column(Integer, nullable=False)
    match_number = Column(Integer, nullable=False)
    team1_id = Column(Integer, ForeignKey('teams.id'), nullable=True)
    team2_id = Column(Integer, ForeignKey('teams.id'), nullable=True)
    winner_team_id = Column(Integer, ForeignKey('teams.id'), nullable=True)
    match_status = Column(Enum(MatchStatus), default=MatchStatus.open)

    tournament = relationship("Tournaments", back_populates="brackets")
    team1 = relationship("Teams", foreign_keys=[team1_id])
    team2 = relationship("Teams", foreign_keys=[team2_id])
    winner_team = relationship("Teams", foreign_keys=[winner_team_id])


class Players(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    discord_user_id = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=False)
    
    minecraft_account = relationship("MinecraftAccounts", uselist=False, back_populates="player")
    minecraft_account_history = relationship("MinecraftAccountHistory", back_populates="player", cascade="all, delete-orphan")
    
    team_memberships = relationship("TeamMembers", back_populates="player")

# Minecraft start
class MinecraftAccounts(Base):
    __tablename__ = 'minecraft_accounts'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False, unique=True)
    minecraft_uuid = Column(String, unique=True, nullable=False)
    minecraft_username = Column(String, nullable=False)
    linked_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))

    player = relationship("Players", back_populates="minecraft_account")

class MinecraftAccountHistory(Base):
    __tablename__ = 'minecraft_account_history'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    minecraft_uuid = Column(String, nullable=False)
    minecraft_username = Column(String, nullable=False)
    change_type = Column(Enum(MinecraftAccountHistoryChangeType), nullable=False)
    changed_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    note = Column(String, nullable=True)

    player = relationship("Players", back_populates="minecraft_account_history")
# Minecraft end

class Teams(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey('tournaments.id'), nullable=False)
    team_name = Column(String, nullable=False)
    signup_time = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    status = Column(Enum(TeamStatus), default=TeamStatus.pending)
    signup_completed_time = Column(DateTime, nullable=True)
    
    challonge_team_id = Column(String, nullable=True)
    
    tournament = relationship("Tournaments", back_populates="teams")
    members = relationship("TeamMembers", back_populates="team")
    messages = relationship("Messages", back_populates="team")
    substitutions = relationship("Substitutions", back_populates="team")

    __table_args__ = (
        UniqueConstraint('tournament_id', 'team_name', name='uix_tournament_teamname'),
    )


class TeamMembers(Base):
    __tablename__ = 'team_members'
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    role = Column(Enum(PlayerRole), default=PlayerRole.member)
    #accepted = Column(Boolean, default=False) # unsused?
    #responded = Column(Boolean, default=False) # unsused?
    #response = Column(Enum(Reaction), nullable=True) # unsused?
    
    team = relationship("Teams", back_populates="members")
    player = relationship("Players", back_populates="team_memberships")

    __table_args__ = (
        UniqueConstraint('team_id', 'player_id', name='uix_team_player'),
    )


class PlayerAcceptance(Base):
    __tablename__ = 'player_acceptance'
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    reacting_player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    reaction = Column(Enum(Reaction), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class Messages(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    discord_message_id = Column(String, nullable=False, unique=True)
    discord_channel_id = Column(String, nullable=False)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    purpose = Column(String, default="signup confirmation message")  # e.g. 'signup confirmation message'
    
    team = relationship("Teams", back_populates="messages")


class Substitutions(Base):
    __tablename__ = 'substitutions'
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    substitute_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    status = Column(Enum(TeamStatus), default=TeamStatus.pending)
    timestamp = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    
    team = relationship("Teams", back_populates="substitutions")

class Bans(Base):
    __tablename__ = 'bans'
    id = Column(Integer, primary_key=True)
    type = Column(Enum(BanType), nullable=False)
    discord_user_id = Column(String, nullable=True)
    minecraft_uuid = Column(String, nullable=True)
    reason = Column(String, nullable=False)
    banned_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    expires_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint('type', 'discord_user_id', name='uix_discord_ban'),
        UniqueConstraint('type', 'minecraft_uuid', name='uix_minecraft_ban'),
    )