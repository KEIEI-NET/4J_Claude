"""
Application Settings

pydantic-settings を使用した環境変数管理
"""

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定"""

    # Neo4j Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # CORS Configuration
    cors_allowed_origins: str = "*"  # カンマ区切り or "*"

    # Server Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False

    # Logging
    log_level: str = "INFO"

    # API Metadata
    api_title: str = "Code Relationship Visualization API"
    api_description: str = "Phase 4: ソースコード関係性可視化・影響範囲分析API"
    api_version: str = "4.0.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """CORS許可オリジンをリストで取得"""
        if self.cors_allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_allowed_origins.split(",")]


# シングルトンインスタンス
settings = Settings()
