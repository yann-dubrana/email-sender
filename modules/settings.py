from pydantic import BaseModel, Field
from pydantic_settings import SettingsConfigDict, BaseSettings


class SMTPSettings(BaseModel):
    server: str
    port: int
    username: str
    password: str
    sender: str = Field(alias="from")
    ssl: bool = Field(False, alias="use_ssl")
    to: str | None = None
    timeout: float = 30.0


class Settings(BaseSettings):
    smtp: SMTPSettings

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        extra="allow",
    )


settings = Settings()
