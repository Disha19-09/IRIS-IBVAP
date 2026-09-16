# JWT Authentication Guide

## Overview

The IRIS-IBVAP backend now includes comprehensive JWT (JSON Web Token) authentication with role-based access control.

## Installation

1. Install authentication dependencies:
   ```bash
   # Run the install script
   install_auth_deps.bat
   
   # OR manually:
   venv\Scripts\activate
   pip install python-jose[cryptography] passlib[bcrypt] python-multipart bcrypt
   ```

2. Restart the backend server (it will auto-create the admin user on first run)

## User Roles

The system supports three roles with hierarchical permissions:

| Role | Permissions |
|------|------------|
| **viewer** | View alerts, events, and dashboard data |
| **operator** | All viewer permissions + create events, manage cameras |
| **admin** | All operator permissions + user management, system configuration |

## Default Admin Account

On first run, the system automatically creates an admin account:

```
Username: admin
Password: admin123
Email: admin@iris-ibvap.local
```

**⚠️ IMPORTANT:** Change the default admin password immediately after first login!

## API Endpoints

### Authentication

#### Register New User (Public)
```bash
POST /auth/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe"
}
```
Note: Public registration creates users with "viewer" role only.

#### Login
```bash
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Get Current User
```bash
GET /auth/me
Authorization: Bearer <access_token>

Response:
{
  "id": 1,
  "username": "admin",
  "email": "admin@iris-ibvap.local",
  "full_name": "System Administrator",
  "roles": ["admin", "operator", "viewer"],
  "is_active": true,
  "created_at": "2026-09-16T07:00:00"
}
```

#### Change Password
```bash
POST /auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "old_password": "admin123",
  "new_password": "newsecurepassword"
}
```

### User Management (Admin Only)

#### List All Users
```bash
GET /users
Authorization: Bearer <admin_access_token>
```

#### Create User (Admin)
```bash
POST /users
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{
  "username": "operator1",
  "email": "operator@example.com",
  "password": "password123",
  "full_name": "Camera Operator",
  "roles": ["operator", "viewer"]
}
```

#### Update User Roles
```bash
PUT /users/{user_id}/roles
Authorization: Bearer <admin_access_token>
Content-Type: application/json

["admin", "operator", "viewer"]
```

#### Delete User
```bash
DELETE /users/{user_id}
Authorization: Bearer <admin_access_token>
```

### Protected Alert Endpoints

All alert endpoints now require authentication:

#### Get Alerts (Requires: viewer or higher)
```bash
GET /alerts?limit=100
Authorization: Bearer <access_token>
```

#### Get Alert Count (Requires: viewer or higher)
```bash
GET /alerts/count
Authorization: Bearer <access_token>
```

#### Clear Alerts (Requires: admin)
```bash
DELETE /alerts
Authorization: Bearer <admin_access_token>
```

#### Create Event (Requires: operator or higher)
```bash
POST /api/events
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "camera_id": "CAM_01",
  "event_type": "crossing",
  "object_type": "person",
  "track_id": 123,
  "confidence": 0.95,
  "timestamp": "2026-09-16T07:00:00",
  "snapshot_path": "snapshot.jpg",
  "plate_number": null
}
```

### Public Endpoint (No Auth)

For the CV pipeline to submit events without authentication:

```bash
POST /api/events/public
Content-Type: application/json

{
  "camera_id": "CAM_01",
  "event_type": "crossing",
  "object_type": "person",
  ...
}
```

## Using JWT in Frontend

### JavaScript/React Example

```javascript
// Login
const login = async (username, password) => {
  const response = await fetch('http://localhost:8000/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  
  const data = await response.json();
  
  // Store tokens
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  
  return data;
};

// Make authenticated request
const getAlerts = async () => {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://localhost:8000/alerts', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
};

// Logout
const logout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};
```

### Python Example

```python
import requests

# Login
response = requests.post('http://localhost:8000/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
tokens = response.json()
access_token = tokens['access_token']

# Make authenticated request
headers = {'Authorization': f'Bearer {access_token}'}
alerts = requests.get('http://localhost:8000/alerts', headers=headers).json()
```

## Token Expiration

- **Access Token**: Expires in 24 hours
- **Refresh Token**: Expires in 7 days

When the access token expires, you'll receive a 401 Unauthorized response. You can:
1. Re-login with username/password
2. Implement refresh token logic (to be added in future update)

## Security Best Practices

1. **Change Default Password**: Immediately change the default admin password
2. **Use HTTPS**: In production, always use HTTPS to encrypt tokens in transit
3. **Secure Storage**: Store tokens securely (localStorage for web, secure storage for mobile)
4. **Token Rotation**: Implement token refresh logic to avoid frequent re-logins
5. **Environment Variables**: Move SECRET_KEY to environment variable in production
6. **Password Policy**: Enforce strong passwords for all users
7. **Audit Logs**: Consider adding audit logging for sensitive operations

## Troubleshooting

### "Invalid authentication credentials"
- Token expired - login again
- Token corrupted - clear storage and login again
- Wrong SECRET_KEY - backend was restarted with different key

### "Operation not permitted. Required roles: ..."
- User doesn't have sufficient permissions
- Contact admin to update your roles

### "User not found"
- User was deleted after token was issued
- Login again with valid credentials

## Custom Role Implementation

To add custom roles or permissions, edit `backend/auth.py`:

```python
# Add new role checker
def require_security_guard(current_user: User = Depends(get_current_user)):
    """Dependency to require security_guard role."""
    checker = RoleChecker(["security_guard", "admin"])
    return checker(current_user)

# Use in routes
@app.get("/guard-panel", dependencies=[Depends(require_security_guard)])
async def guard_panel():
    return {"message": "Security guard panel"}
```

## API Documentation

After starting the backend, visit these URLs for interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Both provide interactive testing of authenticated endpoints!
