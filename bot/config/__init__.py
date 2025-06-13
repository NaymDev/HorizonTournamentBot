from velinconfig import VelinConfig
from dataclasses import dataclass

@dataclass
class Database:
    uri: str

@dataclass
class HorizonBotConfig(VelinConfig):
    database: Database 

CONFIG = HorizonBotConfig(None).load_from_file("./config.json")