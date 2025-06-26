from velinconfig import BaseConfig, ConfigField
    
class DBConfig(BaseConfig):
    uri: str = ConfigField(readonly=True)

class SignupConfig(BaseConfig):
    signup_channel_id: int = ConfigField()

class GithubIssuesConfig(BaseConfig):
    github_token: str = ConfigField(sensitive=True, readonly=True, env_var=True)
    github_repository: str = ConfigField(readonly=True)
    github_labels: list[str] = ConfigField(readonly=True)

class HorizonBotConfig(BaseConfig):
    database: DBConfig = ConfigField()
    signups: SignupConfig = ConfigField()
    issues: GithubIssuesConfig = ConfigField()
    version: str = ConfigField(readonly=True)

CONFIG: HorizonBotConfig = HorizonBotConfig.from_json("./config.json")