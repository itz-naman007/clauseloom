"""Environment configuration. Local inference endpoints only."""

import os
import ipaddress
from urllib.parse import urlparse
from dataclasses import dataclass


@dataclass
class Settings:
    llm_base_url: str = os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434")
    model: str = os.getenv("LLM_MODEL", "qwen2.5:3b-instruct")
    concurrency: int = max(1, int(os.getenv("LLM_CONCURRENCY", "2")))
    context: int = int(os.getenv("LLM_NUM_CTX", "4096"))
    threads: int = max(0, int(os.getenv("LLM_NUM_THREADS", "0")))
    timeout: float = float(os.getenv("LLM_TIMEOUT", "60"))
    max_upload: int = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024
    max_pages: int = int(os.getenv("MAX_PAGES", "30"))
    max_chars: int = 150000
    ttl: int = int(os.getenv("SESSION_TTL_MIN", "30")) * 60
    max_sessions: int = int(os.getenv("MAX_SESSIONS", "24"))
    max_memory: int = int(os.getenv("MAX_MEMORY_MB", "64")) * 1024 * 1024
    rate_limit: int = int(os.getenv("RATE_LIMIT", "10/hour").split("/")[0])
    jurisdiction: str = os.getenv("DEFAULT_JURISDICTION", "india")
    origins: tuple = tuple(os.getenv("ALLOWED_ORIGINS", "http://localhost:8080,http://localhost:5173").split(","))
    llm_enabled: bool = os.getenv("LLM_ENABLED", "true").lower() == "true"
    frame_ancestors: str = os.getenv("FRAME_ANCESTORS", "'none'")

    def __post_init__(self):
        if any(character in self.frame_ancestors for character in "\r\n;"):
            raise ValueError("FRAME_ANCESTORS must contain exact HTTPS origins or 'none'.")
        ancestors = self.frame_ancestors.split()
        if not ancestors or ("'none'" in ancestors and len(ancestors) != 1):
            raise ValueError("FRAME_ANCESTORS must contain exact HTTPS origins or 'none'.")
        for ancestor in ancestors:
            if ancestor in {"'none'", "'self'"}:
                continue
            frame = urlparse(ancestor)
            if (
                frame.scheme != "https" or not frame.hostname or frame.path or frame.query or frame.fragment
                or frame.username or frame.password or "*" in ancestor or ";" in ancestor
                or "\r" in ancestor or "\n" in ancestor
            ):
                raise ValueError("FRAME_ANCESTORS must contain exact HTTPS origins or 'none'.")
        parsed = urlparse(self.llm_base_url)
        host = parsed.hostname or ""
        allowed = host in {"localhost", "ollama", "host.docker.internal", "llama"}
        try:
            address = ipaddress.ip_address(host)
            allowed = address.is_private or address.is_loopback
        except ValueError:
            pass
        if not allowed or parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
            raise ValueError("LLM_BASE_URL must be a local/private inference endpoint.")
        if self.jurisdiction not in {"india", "default"}:
            raise ValueError("Choose india or default jurisdiction.")


settings = Settings()
