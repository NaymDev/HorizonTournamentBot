from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Enum, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base
import enum
import datetime

Base = declarative_base()

class TeamStatus(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    rejected = "rejected"

class MatchStatus(enum.Enum):
    open = "open"
    finished = "finished"

class Reaction(enum.Enum):
    accept = "accept"
    reject = "reject"

class PlayerRole(enum.Enum):
    member = "member"
    substitute = "substitute"

class Tournaments(Base):
    __tablename__ = 'tournaments'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    start_date = Column(DateTime)
    status = Column(String)  # e.g. 'planned', 'active', 'finished'
    
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
    
    team_memberships = relationship("TeamMembers", back_populates="player")


class Teams(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey('tournaments.id'), nullable=False)
    team_name = Column(String, nullable=False)
    signup_time = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(Enum(TeamStatus), default=TeamStatus.pending)
    
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
    accepted = Column(Boolean, default=False)
    responded = Column(Boolean, default=False)
    response = Column(Enum(Reaction), nullable=True)
    
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
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class Messages(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    discord_message_id = Column(String, nullable=False, unique=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    purpose = Column(String)  # e.g. 'signup confirmation message'
    
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