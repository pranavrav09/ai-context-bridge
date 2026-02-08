from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import settings


def _rate_limit_string() -> str:
    window = settings.RATE_LIMIT_WINDOW
    requests = settings.RATE_LIMIT_REQUESTS

    if window == 3600:
        return f"{requests}/hour"
    if window == 60:
        return f"{requests}/minute"
    return f"{requests}/{window} second"


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[_rate_limit_string()],
)
