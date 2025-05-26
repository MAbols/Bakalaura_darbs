from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    openai_key: str | None = None
    anthropic_key: str | None = None
    gcp_project: str | None = None
    gcp_location: str = "us-central1"
    dry_run: bool = False          # True ⇒ stub response
    jira_base:    str | None = None      # https://my.atlassian.net
    jira_user:    str | None = None
    jira_token:   str | None = None
    jira_project: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
