# Quick Start: JWT Authentication

## 🚀 Getting Started in 3 Steps

### Step 1: Install Auth Dependencies

Run the installation script:
```bash
install_auth_deps.bat
```

Or manually:
```bash
venv\Scripts\activate
pip install python-jose[cryptography] passlib[bcrypt] python-multipart bcrypt
```

### Step 2: Restart Backend

Stop and restart the backend server. It will automatically create the default admin user.

```bash
cd backend
..\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

You should see:
```
[INFO] Default admin user created: admin / admin123
```

### Step 3: Test Authentication

Run the test script:
```bash
venv\Scripts\python.exe test_auth.py
```

## 📋 Default Credentials

```
Username: admin
Password: admin123
```

**⚠️ Change this password immediately!**

## 🔑 Quick API Examples

### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"admin123\"}"
```

### Get Alerts (with token)
```bash
curl http://localhost:8000/alerts \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Change Password
```bash
curl -X POST http://localhost:8000/auth/change-password \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"old_password\":\"admin123\",\"new_password\":\"newpassword\"}"
```

## 📚 Full Documentation

See [AUTH_GUIDE.md](AUTH_GUIDE.md) for complete documentation including:
- All API endpoints
- Role-based access control
- Frontend integration examples
- Security best practices
- Troubleshooting

## 🎯 User Roles

| Role | Can Do |
|------|--------|
| **viewer** | View dashboard, alerts, events |
| **operator** | viewer + Create events, manage cameras |
| **admin** | operator + User management, system config |

## 🔧 CV Pipeline Configuration

The CV pipeline now uses the public endpoint (no auth required):
```
BACKEND_URL = "http://localhost:8000/api/events/public"
```

To require authentication for CV pipeline events, use:
```
BACKEND_URL = "http://localhost:8000/api/events"
```
And add the access token in the pipeline code.

## 📖 Interactive API Docs

After starting the backend, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Test all endpoints interactively with built-in authentication!

## ❓ Troubleshooting

**Dependencies won't install?**
- Make sure you're in the virtual environment
- Try: `python -m pip install --upgrade pip` first

**Backend won't start?**
- Check if dependencies installed: `pip list | findstr jose`
- Check database file permissions
- See error logs

**Can't login?**
- Verify backend is running at http://localhost:8000
- Check if admin user was created (see startup logs)
- Try: http://localhost:8000/docs to test via Swagger UI

**Token expired?**
- Access tokens expire in 24 hours
- Just login again to get new tokens
- Implement refresh token logic for production

## 🎓 Next Steps

1. Change the default admin password
2. Create users for your team
3. Update the dashboard to use JWT authentication
4. Secure the SECRET_KEY in production
5. Enable HTTPS for production deployment

For detailed information, see [AUTH_GUIDE.md](AUTH_GUIDE.md)
