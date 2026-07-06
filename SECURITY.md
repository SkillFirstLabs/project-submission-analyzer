# 🔒 Security Guidelines for ProctorAI

## Environment Variables Setup

### 1. Create Your Local `.env` File

Copy the example file and add your actual API keys:

```bash
cp .env.example .env
```

### 2. Required Environment Variables

Edit `.env` with your credentials:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-actual-key-here

# Database (if applicable)
DATABASE_URL=your-database-url

# Security Keys
SECRET_KEY=your-secret-key-here

# Other API Keys (add as needed)
# ANOTHER_API_KEY=your-key-here
```

### 3. Never Commit These Files

The following files are automatically ignored by `.gitignore`:
- `.env` (your actual credentials)
- `.env.local`
- `.env.production`
- `*.key`
- `credentials.json`
- `secrets.json`

**✅ SAFE to commit:**
- `.env.example` (template with no real values)

**❌ NEVER commit:**
- `.env` (contains real API keys)

## API Key Best Practices

### OpenAI API Key Security

1. **Never hardcode keys in code**
   ```python
   # ❌ BAD
   client = OpenAI(api_key="sk-proj-abc123...")
   
   # ✅ GOOD
   client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
   ```

2. **Use environment variables**
   ```python
   import os
   from dotenv import load_dotenv
   
   load_dotenv()  # Load from .env file
   api_key = os.getenv("OPENAI_API_KEY")
   ```

3. **Validate keys exist**
   ```python
   if not os.getenv("OPENAI_API_KEY"):
       raise ValueError("OPENAI_API_KEY not found in environment")
   ```

### Rotating Compromised Keys

If your API key is exposed:

1. **Immediately revoke** the key at https://platform.openai.com/api-keys
2. **Generate a new key**
3. **Update your `.env` file**
4. **Check git history** for any commits with the key
5. **If key was committed**, use BFG Repo-Cleaner or `git filter-branch`

```bash
# Remove sensitive data from git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (⚠️ WARNING: rewrites history)
git push origin --force --all
```

## File Upload Security

### ZIP File Validation

ProctorAI includes protections against:
- **Zip Slip attacks** (path traversal)
- **Zip bombs** (decompression bombs)
- **Malicious file types**

Current limits:
- Max file size: **25MB**
- Allowed extensions: `.zip` only
- Extraction path validation enabled

### User Submission Storage

⚠️ **Important**: Do NOT commit user submissions to git

These are automatically ignored:
- `uploads/`
- `temp_uploads/`
- `extracted_files/`
- `submissions/`

## Proctoring Data Privacy

### Camera & Biometric Data

✅ **Privacy-preserving design:**
- All face detection happens **client-side** (browser)
- No video/audio streams uploaded to server
- Only anonymized event signals sent (timestamps, face count, gaze direction)
- Photos captured are **optional** and stored locally only

### Session Data

- Session IDs are temporary and non-reversible
- Integrity scores calculated server-side
- Activity logs contain no personally identifiable information (PII)

## Database Security

### SQLite (Development)

If using local SQLite:
```python
# .env
DATABASE_URL=sqlite:///./local.db
```

File `local.db` is automatically ignored by `.gitignore`

### Production Database

For production, use environment-specific credentials:
```python
# .env.production (ignored by git)
DATABASE_URL=postgresql://user:password@host:port/dbname
```

## Dependency Security

### Regular Updates

Check for vulnerabilities:
```bash
pip install safety
safety check

# Or use pip-audit
pip install pip-audit
pip-audit
```

### Pin Dependencies

`requirements.txt` should have exact versions:
```
fastapi==0.104.1
uvicorn==0.24.0
openai==1.3.5
```

Update regularly:
```bash
pip list --outdated
pip install --upgrade package-name
```

## CORS Configuration

Current CORS policy (in `app/main.py`):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Change in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production recommendation:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://proctorai.yourdomain.com",
        "https://app.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "Authorization"],
)
```

## Rate Limiting

### OpenAI API Limits

Monitor your usage at: https://platform.openai.com/usage

Implement rate limiting:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/analyze-submission")
@limiter.limit("5/minute")  # Max 5 requests per minute per IP
async def analyze_submission(...):
    ...
```

## Incident Response

### If API Key is Compromised

1. ✅ Rotate key immediately
2. ✅ Check API usage logs for unauthorized access
3. ✅ Review recent git commits
4. ✅ Notify team members
5. ✅ Update deployment configurations

### If User Data is Exposed

1. ✅ Identify scope of exposure
2. ✅ Stop the service if necessary
3. ✅ Notify affected users (if applicable)
4. ✅ Review access logs
5. ✅ Implement additional safeguards

## Deployment Security Checklist

Before deploying to production:

- [ ] All API keys in environment variables (not hardcoded)
- [ ] `.env` file added to `.gitignore`
- [ ] CORS configured with specific origins
- [ ] Rate limiting enabled
- [ ] HTTPS/TLS certificates configured
- [ ] Database credentials secured
- [ ] File upload limits enforced
- [ ] Input validation on all endpoints
- [ ] Error messages don't leak sensitive info
- [ ] Logging configured (no API keys in logs)
- [ ] Security headers set (CSP, HSTS, X-Frame-Options)

## Security Headers (Recommended)

Add to your FastAPI app:
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Force HTTPS in production
app.add_middleware(HTTPSRedirectMiddleware)

# Prevent host header attacks
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["proctorai.yourdomain.com", "*.yourdomain.com"]
)

# Security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

## Reporting Security Issues

If you discover a security vulnerability, please email:
**security@proctorai.com** (replace with your actual security contact)

Do NOT create public GitHub issues for security vulnerabilities.

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OpenAI Security Best Practices](https://platform.openai.com/docs/guides/safety-best-practices)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security.html)

---

**Last Updated:** 2024
**Version:** 1.0
