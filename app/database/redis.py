from uuid import UUID

from redis.asyncio import Redis

from app.config import db_settings


_token_blacklist = Redis.from_url(
    db_settings.REDIS_URL(0),
)

_shipment_verification_codes = Redis.from_url(
    db_settings.REDIS_URL(1),
    decode_responses=True,
)


async def add_jti_to_blacklist(jti: str):
    try:
        await _token_blacklist.set(jti, "blacklisted")
    except Exception:
        pass


async def is_jti_blacklisted(jti: str) -> bool:
    try:
        return bool(await _token_blacklist.exists(jti))
    except Exception:
        return False


async def add_shipment_verification_code(id: UUID, code: int):
    try:
        await _shipment_verification_codes.set(str(id), code)
    except Exception:
        pass


async def get_shipment_verification_code(id: UUID):
    try:
        code = await _shipment_verification_codes.get(str(id))
        return int(code) if code is not None else None
    except Exception:
        return None