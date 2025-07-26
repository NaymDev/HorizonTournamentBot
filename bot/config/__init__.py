from dotenv import load_dotenv
from velinconfig import BaseConfig, ConfigField
    
class DBConfig(BaseConfig):
    uri: str = ConfigField(readonly=True)

class SignupConfig(BaseConfig):
    signup_channel_id: int = ConfigField()

class GithubIssuesConfig(BaseConfig):
    github_repository: str = ConfigField(readonly=True)
    github_labels: list[str] = ConfigField(readonly=True)
    
    github_app_id: str = ConfigField(sensitive=True, env_var="GITHUB_APP_ID", readonly=True)
    github_installation_id: str = ConfigField(sensitive=True, env_var="GITHUB_INSTALLATION_ID", readonly=True)
    github_private_key_path: str = ConfigField(sensitive=True, env_var="GITHUB_PRIVATE_KEY_PATH", readonly=True)

class RegisterConfig(BaseConfig):
    hello_channel_id: int = ConfigField()
    hello_messages: list[str] = ConfigField()

class HypixelConfig(BaseConfig):
    _placeholder: int = ConfigField(readonly=True) # The sub config (HypixelConfig) will be None without this
    api_key: str = ConfigField(sensitive=True, env_var="HYPIXEL_API_KEY", readonly=True)

class ChallongeConfig(BaseConfig):
    _placeholder: int = ConfigField(readonly=True) # The sub config (ChallongeConfig) will be None without this
    api_key: str = ConfigField(sensitive=True, env_var="CHALLONGE_API_KEY", readonly=True)

class StyleConfig(BaseConfig):
    pr_enter_emoji: str = ConfigField(readonly=True)

class HorizonBotConfig(BaseConfig):
    database: DBConfig = ConfigField()
    signups: SignupConfig = ConfigField()
    issues: GithubIssuesConfig = ConfigField()
    register: RegisterConfig = ConfigField()
    hypixel: HypixelConfig = ConfigField()
    challonge: ChallongeConfig = ConfigField()
    styles: StyleConfig = ConfigField()
    version: str = ConfigField(readonly=True)

load_dotenv(dotenv_path=".env", override=True)
CONFIG: HorizonBotConfig = HorizonBotConfig.from_json("./config.json")