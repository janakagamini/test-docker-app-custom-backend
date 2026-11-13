# Minimal Firebase App Check Backend (FastAPI + Manual JWKS)

Verifies `X-Firebase-AppCheck` JWTs manually using Firebase's public JWKS endpoint (`https://firebaseappcheck.googleapis.com/v1/jwks`) without `firebase-admin`.

## 1. Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Run

Replace `123456789012` with your **Firebase Project Number** (Firebase Console → Project Settings → General → Project number):

```bash
FIREBASE_PROJECT_NUMBER=123456789012 uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

## 3. Connect from Android Emulator

- **Option A (`10.0.2.2`)**: Call `http://10.0.2.2:8080/api/test` from your Android app.
  - Ensure your debug build allows cleartext HTTP for `10.0.2.2` (via `network_security_config.xml` or `android:usesCleartextTraffic="true"`).
- **Option B (`adb reverse`)**: Run:
  ```bash
  adb reverse tcp:8080 tcp:8080
  ```
  Then call `http://localhost:8080/api/test` from your Android app.

## 4. Endpoints

- `GET /health` — Unprotected, useful for testing emulator-to-Mac connectivity first.
- `GET /api/test` — Requires a valid `X-Firebase-AppCheck` header; returns `200 OK` with decoded claims or `401 Unauthorized`.
