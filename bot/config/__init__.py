from velinconfig import BaseConfig, ConfigField
    
class DBConfig(BaseConfig):
    uri: str = ConfigField(readonly=True)

class SignupConfig(BaseConfig):
    signup_channel_id: int = ConfigField()

class HorizonBotConfig(BaseConfig):
    database: DBConfig = ConfigField()
    signups: SignupConfig = ConfigField()
    version: str = ConfigField(readonly=True)

CONFIG: HorizonBotConfig = HorizonBotConfig.from_json("./config.json")