from velinconfig import BaseConfig, ConfigField
    
class DBConfig(BaseConfig):
    uri: str = ConfigField(readonly=True)

class HorizonBotConfig(BaseConfig):
    database: DBConfig = ConfigField()
    version: str = ConfigField(readonly=True)

CONFIG: HorizonBotConfig = HorizonBotConfig.from_json("./config.json")