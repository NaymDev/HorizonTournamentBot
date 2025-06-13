from velinconfig import VelinConfig
from dataclass import dataclass

@dataclass
class HorozonBotConfig(VelinConfig):
    class database::
        url: str

CONFIG = HorizonBotConfif().load_from_file("./config.json")