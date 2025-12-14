# OAuth Authentication Setup Guide

This document provides instructions for setting up OAuth 2.0 authentication for the Mergington High School Activity Management System.

## Overview

The application uses OAuth 2.0 authentication with PKCE (Proof Key for Code Exchange) to provide secure, production-ready authentication. This replaces the previous basic authentication system and eliminates security risks associated with password storage and credential transmission.

## Features

- **OAuth 2.0 with PKCE**: Enhanced security using authorization code flow with PKCE
- **CSRF Protection**: State parameter prevents cross-site request forgery attacks
- **Secure Token Storage**: 
  - Session tokens stored in httpOnly cookies
  - Refresh tokens stored in httpOnly cookies
  - Access tokens stored in memory (not in localStorage)
- **Automatic Token Refresh**: Built-in token refresh mechanism
- **Session Management**: Secure session handling with expiration
- **Multiple Provider Support**: Compatible with GitHub, Google, or any OAuth 2.0 provider

## Supported OAuth Providers

The application is configured to work with any OAuth 2.0 provider. Common providers include:

- **GitHub OAuth** (default configuration)
- **Google OAuth**
- **Microsoft OAuth**
- **Custom OAuth providers**

## Prerequisites

Before setting up OAuth authentication, you need:

1. Python 3.8 or higher
2. An OAuth application registered with your chosen provider
3. Client ID and Client Secret from your OAuth provider

## Step 1: Register Your OAuth Application

### For GitHub OAuth (Recommended for Testing)

1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Click "New OAuth App"
3. Fill in the application details:
   - **Application name**: Mergington High School Activities
   - **Homepage URL**: `http://localhost:8000` (for local development)
   - **Authorization callback URL**: `http://localhost:8000/auth/callback`
4. Click "Register application"
5. Note your **Client ID**
6. Generate a new **Client Secret** and save it securely

### For Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID
5. Configure OAuth consent screen
6. Set application type to "Web application"
7. Add authorized redirect URI: `http://localhost:8000/auth/callback`
8. Note your **Client ID** and **Client Secret**

### For Production

For production deployments:
- Use HTTPS URLs instead of HTTP
- Update redirect URIs to match your production domain
- Keep Client Secrets secure (use environment variables, never commit to git)

## Step 2: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and configure the following variables:

### Required Configuration

```bash
# Secret keys - MUST be changed in production
SECRET_KEY=your-secret-key-here-change-in-production
SESSION_SECRET=your-session-secret-here-change-in-production

# OAuth Provider Settings
OAUTH_CLIENT_ID=your-oauth-client-id-from-step-1
OAUTH_CLIENT_SECRET=your-oauth-client-secret-from-step-1
OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback

# OAuth Endpoints (GitHub example)
OAUTH_AUTHORIZE_URL=https://github.com/login/oauth/authorize
OAUTH_TOKEN_URL=https://github.com/login/oauth/access_token
OAUTH_USERINFO_URL=https://api.github.com/user

# Token Settings
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application URL
APP_URL=http://localhost:8000
```

### Generate Secure Secret Keys

To generate secure secret keys, run:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Run this command twice to generate both `SECRET_KEY` and `SESSION_SECRET`.

### Provider-Specific Endpoints

**GitHub OAuth:**
```bash
OAUTH_AUTHORIZE_URL=https://github.com/login/oauth/authorize
OAUTH_TOKEN_URL=https://github.com/login/oauth/access_token
OAUTH_USERINFO_URL=https://api.github.com/user
```

**Google OAuth:**
```bash
OAUTH_AUTHORIZE_URL=https://accounts.google.com/o/oauth2/v2/auth
OAUTH_TOKEN_URL=https://oauth2.googleapis.com/token
OAUTH_USERINFO_URL=https://www.googleapis.com/oauth2/v2/userinfo
```

## Step 3: Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Key dependencies for OAuth:
- `authlib`: OAuth 2.0 client library
- `python-jose`: JWT token handling
- `itsdangerous`: Secure token generation
- `python-dotenv`: Environment variable management

## Step 4: Run the Application

Start the development server:

```bash
uvicorn src.app:app --reload
```

The application will be available at `http://localhost:8000`

## Step 5: Test the OAuth Flow

1. Open your browser and navigate to `http://localhost:8000`
2. You should see a "Sign in with OAuth" button
3. Click the button to initiate the OAuth flow
4. You'll be redirected to your OAuth provider's authorization page
5. Grant permissions to the application
6. You'll be redirected back to the application, now authenticated
7. Try signing up for activities

## API Endpoints

### Authentication Endpoints

#### `GET /auth/login`
Initiates the OAuth login flow. Redirects to the OAuth provider's authorization page.

**Response**: 
- Redirects to OAuth provider

#### `GET /auth/callback`
Handles the OAuth callback after authorization.

**Query Parameters**:
- `code`: Authorization code from OAuth provider
- `state`: CSRF protection token

**Response**: 
- Redirects to home page with session cookie set

#### `GET /auth/user`
Gets the current authenticated user's information.

**Response**:
```json
{
  "email": "user@example.com",
  "name": "User Name",
  "id": "user-id",
  "avatar_url": "https://..."
}
```

#### `POST /auth/refresh`
Refreshes the access token using the refresh token.

**Response**:
```json
{
  "message": "Token refreshed"
}
```

#### `POST /auth/logout`
Logs out the current user and clears session.

**Response**:
```json
{
  "message": "Logged out successfully"
}
```

### Activity Endpoints (Protected)

All activity signup and unregister endpoints now require authentication:

#### `POST /activities/{activity_name}/signup`
Sign up the authenticated user for an activity.

**Authentication**: Required (session cookie)

#### `DELETE /activities/{activity_name}/unregister`
Unregister the authenticated user from an activity.

**Authentication**: Required (session cookie)

## Security Features

### PKCE (Proof Key for Code Exchange)

The application implements PKCE to prevent authorization code interception attacks:
1. Generates a code verifier and challenge before authorization
2. Sends code challenge with authorization request
3. Sends code verifier with token exchange
4. OAuth provider verifies the match

### CSRF Protection

The application uses a state parameter to prevent CSRF attacks:
1. Generates a random state token before authorization
2. Stores state in a temporary session
3. Validates state matches when handling callback

### Secure Token Storage

- **Access Tokens**: Stored in memory (not in localStorage or cookies)
- **Refresh Tokens**: Stored in httpOnly, secure cookies
- **Session Tokens**: Stored in httpOnly, secure cookies

### Session Expiration

- Sessions expire after 30 minutes of inactivity (configurable)
- Refresh tokens expire after 7 days (configurable)
- Expired sessions are automatically cleaned up

## Testing

Run the test suite:

```bash
pytest tests/test_app.py -v
```

The test suite includes:
- OAuth authentication tests
- Protected endpoint tests
- Session management tests
- Integration tests

## Production Deployment

### Security Checklist

- [ ] Change `SECRET_KEY` and `SESSION_SECRET` to secure random values
- [ ] Set `secure=True` for cookies (requires HTTPS)
- [ ] Use HTTPS for all URLs (APP_URL, OAUTH_REDIRECT_URI)
- [ ] Store secrets in secure environment variable management system
- [ ] Update CORS settings to only allow your domain
- [ ] Implement rate limiting on OAuth endpoints
- [ ] Set up monitoring and logging for authentication events
- [ ] Use a persistent storage backend (Redis/Database) instead of in-memory sessions

### Environment Variable Management

For production, use:
- **Heroku**: Config Vars in dashboard
- **AWS**: Secrets Manager or Parameter Store
- **Azure**: Key Vault
- **Docker**: Environment files with restricted permissions
- **Kubernetes**: Secrets

### Scaling Considerations

The current implementation uses in-memory storage for sessions and tokens. For production:

1. **Use Redis** for session storage:
   - Install `redis` and `aioredis` packages
   - Update `src/auth.py` to use Redis instead of dict

2. **Use a Database** for user management:
   - Store user profiles in PostgreSQL/MySQL
   - Track login history for audit

3. **Implement Rate Limiting**:
   - Use `slowapi` or similar
   - Limit login attempts per IP

## Troubleshooting

### "Authentication error: invalid_state"
- Clear your browser cookies
- Ensure `OAUTH_REDIRECT_URI` matches exactly in OAuth app settings
- Check system clock is synchronized

### "Authentication error: token_exchange_failed"
- Verify `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET` are correct
- Check `OAUTH_TOKEN_URL` is correct for your provider
- Ensure OAuth app is active and approved

### "Authentication required" on API calls
- Check that session cookie is being sent with requests
- Verify session hasn't expired
- Try logging in again

### CORS errors
- Ensure `APP_URL` in `.env` matches your frontend URL
- Check CORS middleware configuration in `src/app.py`

## Additional Resources

- [OAuth 2.0 RFC](https://tools.ietf.org/html/rfc6749)
- [PKCE RFC](https://tools.ietf.org/html/rfc7636)
- [GitHub OAuth Documentation](https://docs.github.com/en/developers/apps/building-oauth-apps)
- [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)

## Support

For issues or questions:
1. Check this documentation
2. Review the test suite for examples
3. Check the issue tracker
4. Contact the development team
