import os
from typing import Any

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, status
from jwt import PyJWKClient

APP_CHECK_JWKS_URL = "https://firebaseappcheck.googleapis.com/v1/jwks"
JWKS_CACHE_SECONDS = 6 * 60 * 60  # Google recommends caching JWKS for up to 6 hours

FIREBASE_PROJECT_NUMBER = os.getenv("FIREBASE_PROJECT_NUMBER", "").strip()
if not FIREBASE_PROJECT_NUMBER:
    raise RuntimeError(
        "FIREBASE_PROJECT_NUMBER environment variable is required. "
        "Find it in Firebase Console -> Project Settings -> General -> Project number."
    )

EXPECTED_ISSUER = f"https://firebaseappcheck.googleapis.com/{FIREBASE_PROJECT_NUMBER}"
EXPECTED_AUDIENCE = f"projects/{FIREBASE_PROJECT_NUMBER}"

jwks_client = PyJWKClient(
    APP_CHECK_JWKS_URL,
    cache_jwk_set=True,
    lifespan=JWKS_CACHE_SECONDS,
)

app = FastAPI(title="Minimal Firebase App Check Backend (Manual JWKS)")


def verify_app_check_token(
    x_firebase_appcheck: str | None = Header(default=None, alias="X-Firebase-AppCheck"),
) -> dict[str, Any]:
    """Manually verify a Firebase App Check JWT against the public JWKS endpoint."""
    if not x_firebase_appcheck:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Firebase-AppCheck header",
        )

    try:
        header = jwt.get_unverified_header(x_firebase_appcheck)
        if header.get("alg") != "RS256" or header.get("typ") != "JWT":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid App Check token header",
            )

        signing_key = jwks_client.get_signing_key_from_jwt(x_firebase_appcheck)
        claims = jwt.decode(
            x_firebase_appcheck,
            signing_key.key,
            algorithms=["RS256"],
            audience=EXPECTED_AUDIENCE,
            issuer=EXPECTED_ISSUER,
            options={"require": ["exp", "sub", "aud", "iss"]},
        )
    except HTTPException:
        raise
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid App Check token: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"App Check verification failed: {exc}",
        ) from exc

    if not claims.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="App Check token missing subject (app ID)",
        )

    return claims


@app.get("/health")
def health() -> dict[str, str]:
    """Unprotected endpoint to verify emulator-to-MacBook connectivity."""
    return {"status": "ok"}


@app.get("/api/test")
def test_app_check(claims: dict[str, Any] = Depends(verify_app_check_token)) -> dict[str, Any]:
    """Protected endpoint that requires a valid Firebase App Check token."""
    return {
        "verified": True,
        "app_id": claims["sub"],
        "issuer": claims["iss"],
        "audience": claims["aud"],
        "expires_at": claims["exp"],
    }
