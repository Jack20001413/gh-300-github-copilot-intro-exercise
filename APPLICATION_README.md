# Mergington High School Activity Management System

A secure web application for managing extracurricular activities at Mergington High School, built with FastAPI and OAuth 2.0 authentication.

## 🔐 Security Features

This application implements **production-ready OAuth 2.0 authentication** with the following security features:

- **OAuth 2.0 with PKCE**: Authorization code flow with Proof Key for Code Exchange
- **CSRF Protection**: State parameter prevents cross-site request forgery attacks
- **Secure Token Storage**: httpOnly cookies for sessions and refresh tokens
- **Automatic Token Refresh**: Built-in token refresh mechanism
- **Session Management**: Secure session handling with expiration
- **Protected Endpoints**: All signup and unregister operations require authentication

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OAuth application credentials (GitHub, Google, or other OAuth 2.0 provider)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Jack20001413/gh-300-github-copilot-intro-exercise.git
   cd gh-300-github-copilot-intro-exercise
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure OAuth (see [OAuth Setup Guide](OAUTH_SETUP.md)):
   ```bash
   cp .env.example .env
   # Edit .env with your OAuth credentials
   ```

4. Run the application:
   ```bash
   uvicorn src.app:app --reload
   ```

5. Open your browser and navigate to `http://localhost:8000`

## 📚 Documentation

- **[OAuth Setup Guide](OAUTH_SETUP.md)** - Complete guide for configuring OAuth authentication
- **[API Documentation](http://localhost:8000/docs)** - Interactive API documentation (available when running)

## 🧪 Testing

Run the test suite:

```bash
pytest tests/test_app.py -v
```

All tests include:
- OAuth authentication tests
- Protected endpoint tests  
- Session management tests
- Integration tests

## 🏗️ Architecture

### Backend (FastAPI)

- **`src/app.py`**: Main application with OAuth and activity endpoints
- **`src/auth.py`**: OAuth authentication logic with PKCE and session management
- **`src/config.py`**: Configuration management with environment variables

### Frontend (Vanilla JS)

- **`src/static/index.html`**: Main UI with OAuth login flow
- **`src/static/app.js`**: Client-side OAuth handling and API calls
- **`src/static/styles.css`**: Styling for the application

## 🔑 Key Features

1. **OAuth 2.0 Authentication**
   - Secure sign-in with OAuth providers (GitHub, Google, etc.)
   - No passwords stored in the application
   - Automatic token refresh
   - Secure session management

2. **Activity Management**
   - View all available extracurricular activities
   - Sign up for activities (authenticated users only)
   - Unregister from activities (authenticated users only)
   - Real-time participant list updates

3. **User Experience**
   - Clean, intuitive interface
   - Responsive design
   - Clear authentication status
   - Error handling with user-friendly messages

## 📋 Environment Variables

Required environment variables (see `.env.example`):

```bash
SECRET_KEY=                    # Application secret key
SESSION_SECRET=                # Session encryption key
OAUTH_CLIENT_ID=              # OAuth application client ID
OAUTH_CLIENT_SECRET=          # OAuth application client secret
OAUTH_REDIRECT_URI=           # OAuth callback URL
OAUTH_AUTHORIZE_URL=          # OAuth provider authorization endpoint
OAUTH_TOKEN_URL=              # OAuth provider token endpoint
OAUTH_USERINFO_URL=           # OAuth provider user info endpoint
ACCESS_TOKEN_EXPIRE_MINUTES=  # Session expiration (default: 30)
REFRESH_TOKEN_EXPIRE_DAYS=    # Refresh token expiration (default: 7)
APP_URL=                      # Application URL (default: http://localhost:8000)
```

## 🛡️ Security Best Practices Implemented

- ✅ PKCE for authorization code flow
- ✅ State parameter for CSRF protection
- ✅ httpOnly cookies for token storage
- ✅ Secure session management
- ✅ Token expiration and refresh
- ✅ Protected API endpoints
- ✅ No sensitive data in localStorage
- ✅ Environment-based configuration
- ✅ Input validation and sanitization

## 🚢 Production Deployment

For production deployment:

1. **Use HTTPS** for all URLs
2. **Set secure cookie flags** (`secure=True` in auth.py)
3. **Use strong secret keys** (generate with `secrets.token_urlsafe(32)`)
4. **Use persistent storage** (Redis/Database) instead of in-memory sessions
5. **Implement rate limiting** on OAuth endpoints
6. **Set up monitoring** and logging for authentication events
7. **Use environment variable management** (AWS Secrets Manager, Azure Key Vault, etc.)

See [OAuth Setup Guide](OAUTH_SETUP.md) for detailed production deployment instructions.

## 🤝 Contributing

Contributions are welcome! Please ensure:

- All tests pass before submitting
- New features include tests
- Security best practices are followed
- Documentation is updated

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

This application was enhanced with OAuth 2.0 authentication as part of a security improvement initiative to eliminate the risks associated with basic authentication.

---

For detailed OAuth setup instructions, see [OAUTH_SETUP.md](OAUTH_SETUP.md)
