"""
JWT verification — uses same secret as all Spring Boot services.
"""

import os
import logging
from typing import Optional, Dict, Any

import jwt as pyjwt

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "7c1015921c5d90739574de77e2c5bb7661a555f493e0c2b0ca47f550b938368bd7e839ba6ff0dc617716913dfaf61c7bd87b57f3920241f008cd54fb6c7918fa",
)


def verify_jwt(authorization: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Verify the Bearer JWT and return the decoded claims.
    Returns None if the token is missing or invalid.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization[7:].strip()
    if not token:
        return None

    try:
        import base64
        key_bytes = base64.b64decode(JWT_SECRET)
        payload = pyjwt.decode(
            token,
            key_bytes,
            algorithms=["HS256"],
            options={"verify_exp": True},
        )
        return payload
    except pyjwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except pyjwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
