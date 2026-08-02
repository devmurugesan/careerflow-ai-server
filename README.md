# CareerFlow AI — Backend Platform

CareerFlow AI is an AI-powered Career & Learning Intelligence Platform. This repository contains the **Modular Monolith** backend application built with **Python 3.12**, **FastAPI**, **SQLAlchemy 2.0**, **PostgreSQL**, **Alembic**, and **Google OAuth 2.0**.

---

## 🔐 Phase 2: Google Authentication & Gmail OAuth Setup

CareerFlow AI uses Google's official **OAuth 2.0 PKCE Authorization Code Flow** to allow users to sign in and grant permission to read career-related emails.

### 🌐 Google Cloud Console Setup Guide

Follow these steps to configure your Google Cloud project for local development:

1. **Create a Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/).
   - Click **Select a project** → **New Project**. Name it `CareerFlow AI` and click **Create**.

2. **Enable Gmail API**:
   - Navigate to **APIs & Services** → **Library**.
   - Search for `Gmail API` and click **Enable**.

3. **Configure OAuth Consent Screen**:
   - Navigate to **APIs & Services** → **OAuth consent screen**.
   - Select **External** user type and click **Create**.
   - Provide **App name** (`CareerFlow AI`) and **User support email**.
   - Add the following minimum required scopes:
     - `openid`
     - `https://www.googleapis.com/auth/userinfo.email` (View primary email address)
     - `https://www.googleapis.com/auth/userinfo.profile` (View basic profile details)
     - `https://www.googleapis.com/auth/gmail.readonly` (Read-only access to emails)
   - Add test user email addresses under **Test users**.

4. **Create OAuth 2.0 Credentials**:
   - Navigate to **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth client ID**.
   - Select **Web application**.
   - Add Authorized Redirect URIs:
     - `http://localhost:8000/api/v1/auth/google/callback`
   - Click **Create** and copy your **Client ID** and **Client Secret**.

---

## 🔒 Requested OAuth Scopes Explanation

| Scope | Type | Purpose |
|-------|------|---------|
| `openid` | OIDC | Identity verification standard |
| `userinfo.email` | User Profile | Primary email address identification |
| `userinfo.profile` | User Profile | Display name and profile avatar |
| `gmail.readonly` | Gmail API | **Minimum required permission** to read career email updates without write/delete permissions |

---

## ⚙️ Environment Configuration

Set your Google OAuth credentials in `.env`:

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
```

---

## 🌐 Phase 2 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/auth/google` | Initiates Google OAuth 2.0 flow by returning authorization URL |
| `GET` | `/api/v1/auth/google/callback` | Exchanges code for tokens, upserts user, encrypts tokens, & issues JWT |
| `GET` | `/api/v1/gmail/status` | Returns safe Gmail connection status for authenticated user |
| `POST` | `/api/v1/gmail/disconnect` | Marks Gmail account as disconnected and clears stored OAuth credentials |

---

## 🧪 Testing Phase 2 Google OAuth

Run automated unit and integration tests (with mocked Google API calls):

```bash
python -m pytest tests/
```
