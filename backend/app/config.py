import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    allowed_origins: list[str] = field(default_factory=list)


    hybrid_candidate_k: int = int(os.getenv("HYBRID_CANDIDATE_K", "20"))

    def __post_init__(self):
        origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
        self.allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]


settings = Settings()