from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "elder-care-server"
    host: str = "0.0.0.0"
    port: int = 8000

    # 以下数据库/JWT 默认值仅便于本地演示；部署请用 .env 覆盖
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "elder_care"
    db_user: str = "root"
    db_password: str = "123456"

    jwt_secret: str = "system-jwt-secret-key-for-graduation-project-min-32-chars"
    jwt_expiration_ms: int = 86400000

    upload_path: str = "./uploads"

    # Agent：未配置 Key 或 AGENT_DEMO_MODE=true 时走演示编排（仍真实调工具写库）
    # 文档：https://api-docs.deepseek.com/zh-cn/
    agent_demo_mode: bool = True
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    # deepseek-v4-flash（快）/ deepseek-v4-pro（强）；deepseek-chat 将于 2026-07-24 弃用
    llm_model: str = "deepseek-v4-flash"
    # Tool Calls 推荐非思考模式：disabled；复杂推理可设 enabled
    llm_thinking: str = "disabled"
    llm_reasoning_effort: str = "high"
    llm_temperature: float = 0.2
    llm_max_tokens: int | None = 4096

    # RAG：Chroma 持久化目录（相对 fastapi 工作目录）
    chroma_path: str = "./data/chroma"
    knowledge_collection: str = "elder_care_knowledge"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?charset=utf8mb4"
        )

    @property
    def upload_root(self) -> Path:
        return Path(self.upload_path).resolve()

    @property
    def chroma_root(self) -> Path:
        return Path(self.chroma_path).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
