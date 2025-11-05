# Upstash Redis Setup Guide

## 🚀 Migration from Local Redis to Upstash Cloud

This guide walks you through setting up Upstash Redis for your NLP API (free tier).

---

## 📋 Prerequisites

- Upstash account (sign up at https://console.upstash.com/)
- Free tier provides: 10,000 commands/day
- Perfect for development and small-scale production

---

## 🔧 Step 1: Get Upstash Redis Credentials

### 1.1 Create Redis Database

1. Go to https://console.upstash.com/
2. Click **"Create Database"**
3. Configure:
   - **Name**: `nlp-api-cache` (or your preferred name)
   - **Type**: Regional (recommended for free tier)
   - **Region**: Choose closest to your deployment
   - **TLS**: Enabled (required for Upstash)
   - **Eviction**: Enable with `allkeys-lru` policy

### 1.2 Get Connection Details

After creating the database, you'll see:

```
Endpoint: <database-name>.upstash.io
Port: 6379 or 6380
Password: <your-redis-password>
```

### 1.3 Get Connection URLs

Upstash provides multiple connection URL formats. Use **REST API URL** or **Redis URL**:

#### Option A: Redis URL (Recommended)
```
rediss://:YOUR_PASSWORD@YOUR-ENDPOINT.upstash.io:6379
```

#### Option B: REST API URL (Alternative)
```
https://YOUR-ENDPOINT.upstash.io
```

**Example:**
```
rediss://:AYNDAAIjcDFiYmY2MjExOWRjMjE0ZWRlODdhMDQxNzRkYWU5ZDEzZHAxMA@premium-sunbird-12345.upstash.io:6379
```

---

## 🔐 Step 2: Configure Environment Variables

### 2.1 Update `.env` File

Open your `.env` file and update the Redis configuration:

```properties
# Redis - Upstash Configuration
# Get your credentials from: https://console.upstash.com/
REDIS_ENABLED=true
REDIS_URL=rediss://:YOUR_PASSWORD@YOUR-ENDPOINT.upstash.io:6379
REDIS_PASSWORD=YOUR_PASSWORD
REDIS_TTL=3600
REDIS_MAX_RETRIES=3
REDIS_TIMEOUT=10
```

### 2.2 Example Configuration

```properties
# Example (replace with your actual credentials)
REDIS_ENABLED=true
REDIS_URL=rediss://:AYNDAAIjcDFiYmY2MjExOWRjMjE0ZWRlODdhMDQxNzRkYWU5ZDEzZHAxMA@premium-sunbird-12345.upstash.io:6379
REDIS_PASSWORD=AYNDAAIjcDFiYmY2MjExOWRjMjE0ZWRlODdhMDQxNzRkYWU5ZDEzZHAxMA
REDIS_TTL=3600
REDIS_MAX_RETRIES=3
REDIS_TIMEOUT=10
```

### 2.3 Important Notes

⚠️ **Security:**
- Never commit `.env` file to version control
- Keep your Redis password secret
- Use environment variables in production

✅ **Verification:**
- Make sure URL starts with `rediss://` (with double 's' for SSL)
- Password should be after `//:`
- Endpoint should end with `.upstash.io:6379`

---

## 📦 Step 3: Install Required Dependencies

The API already has Redis dependencies in `requirements.txt`:

```bash
pip install redis==5.0.1 hiredis==2.2.3
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

---

## ✅ Step 4: Test Connection

### 4.1 Test via Python Script

Create a test script or use the built-in test:

```bash
python redis_cache.py
```

Expected output:
```
============================================================
Redis Cache Manager - Test
============================================================
Health Status: {'status': 'healthy', 'active': True, 'message': 'Redis is connected and responsive', ...}
✓ Set test key: test:key
✓ Retrieved: {'message': 'Hello Redis!', ...}
✓ Deleted test key
...
============================================================
```

### 4.2 Test via API Endpoint

1. Start the API:
```bash
uvicorn api:app --reload
```

2. Check Redis health:
```bash
curl http://localhost:8000/redis/health
```

Expected response:
```json
{
  "status": "healthy",
  "active": true,
  "message": "Redis is connected and responsive",
  "provider": "Upstash (Cloud)",
  "is_upstash": true,
  "redis_version": "Upstash (free tier)",
  "connection_time": "2025-11-05T10:30:45.123Z",
  "last_error": null
}
```

### 4.3 Test System Status (Frontend Endpoint)

```bash
curl http://localhost:8000/status
```

Expected response:
```json
{
  "api": {
    "status": "operational",
    "version": "1.1.0 - Async + Redis + Upstash",
    "timestamp": "2025-11-05T10:30:45.123Z"
  },
  "redis": {
    "active": true,
    "status": "healthy",
    "provider": "Upstash (Cloud)",
    "is_upstash": true,
    "message": "Redis is connected and responsive",
    "connection_time": "2025-11-05T10:15:30.456Z"
  },
  "cache": {
    "redis_enabled": true,
    "redis_active": true,
    "file_cache_enabled": true,
    "fallback_available": true,
    "ttl": 3600
  },
  "alerts": [],
  "timestamp": "2025-11-05T10:30:45.123Z"
}
```

---

## 🎯 Step 5: Frontend Integration

### 5.1 Status Indicator Component (React Example)

```jsx
import { useEffect, useState } from 'react';

function RedisStatusIndicator() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/status');
        const data = await response.json();
        setStatus(data);
      } catch (error) {
        console.error('Failed to fetch status:', error);
      } finally {
        setLoading(false);
      }
    };

    checkStatus();
    // Poll every 30 seconds
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div>Loading...</div>;

  const redisActive = status?.redis?.active;
  const hasAlerts = status?.alerts?.length > 0;

  return (
    <div className="status-indicator">
      <div className={`status-badge ${redisActive ? 'active' : 'inactive'}`}>
        <span className="status-dot"></span>
        <span className="status-text">
          {redisActive ? 'Cache Active' : 'Cache Unavailable'}
        </span>
      </div>
      
      {redisActive && (
        <div className="status-details">
          <small>{status.redis.provider}</small>
        </div>
      )}

      {hasAlerts && (
        <div className="alerts">
          {status.alerts.map((alert, i) => (
            <div key={i} className={`alert alert-${alert.level}`}>
              {alert.message}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default RedisStatusIndicator;
```

### 5.2 CSS for Status Indicator

```css
.status-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.active {
  background: #d4edda;
  color: #155724;
}

.status-badge.inactive {
  background: #f8d7da;
  color: #721c24;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.status-badge.active .status-dot {
  background: #28a745;
}

.status-badge.inactive .status-dot {
  background: #dc3545;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.alert {
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
}

.alert-warning {
  background: #fff3cd;
  color: #856404;
}

.alert-error {
  background: #f8d7da;
  color: #721c24;
}
```

---

## 🐳 Step 6: Docker Deployment

### 6.1 Update Docker Environment

The `docker-compose.yml` has been updated to use Upstash. You need to pass environment variables:

Create `.env.docker` file:

```properties
API_ENV=production
REDIS_ENABLED=true
REDIS_URL=rediss://:YOUR_PASSWORD@YOUR-ENDPOINT.upstash.io:6379
REDIS_PASSWORD=YOUR_PASSWORD
REDIS_TTL=3600
REDIS_MAX_RETRIES=3
REDIS_TIMEOUT=10
```

### 6.2 Deploy with Docker Compose

```bash
# Build and start
docker-compose --env-file .env.docker up -d

# Check logs
docker-compose logs -f api

# Check Redis connection
curl http://localhost:8000/redis/health
```

---

## 📊 Monitoring & Management

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/status` | GET | **Frontend-friendly** system status with alerts |
| `/redis/health` | GET | Detailed Redis health check |
| `/redis/stats` | GET | Redis cache statistics |
| `/redis/clear` | DELETE | Clear all or specific cache patterns |

### Example Monitoring

```bash
# Check system status (use this in frontend)
curl http://localhost:8000/status

# Get detailed Redis stats
curl http://localhost:8000/redis/stats

# Clear specific cache
curl -X DELETE "http://localhost:8000/redis/clear?pattern=analysis:*"
```

---

## 🔍 Troubleshooting

### Issue 1: Connection Refused

**Error:**
```
Redis connection failed: Connection refused
```

**Solution:**
- Check if `REDIS_URL` is correct
- Verify it starts with `rediss://` (with SSL)
- Confirm password is included in URL

### Issue 2: Authentication Failed

**Error:**
```
Redis connection failed: WRONGPASS invalid username-password pair
```

**Solution:**
- Verify your password is correct
- Copy password directly from Upstash console
- Make sure password is in both URL and REDIS_PASSWORD

### Issue 3: Timeout Errors

**Error:**
```
Redis timeout error
```

**Solution:**
- Increase `REDIS_TIMEOUT` to 15 or 20
- Check your internet connection
- Verify Upstash server is not down

### Issue 4: SSL Certificate Errors

**Error:**
```
SSL certificate verification failed
```

**Solution:**
- The code already handles this with `ssl_cert_reqs = None`
- Make sure you're using `rediss://` (with SSL)

### Issue 5: Free Tier Limit Exceeded

**Error:**
```
ERR max number of clients reached
```

**Solution:**
- Upstash free tier has 10,000 commands/day limit
- Monitor usage in Upstash console
- Consider upgrading if needed
- Implement longer TTLs to reduce requests

---

## 🎯 Best Practices

### 1. Error Handling

The API automatically falls back to file cache if Redis fails:
- No downtime for users
- Degraded performance warning shown
- Alerts visible in `/status` endpoint

### 2. TTL Configuration

Recommended TTLs for free tier:

```properties
# Longer TTLs = fewer Redis commands = stay within free tier
REDIS_TTL=7200  # 2 hours instead of 1 hour

# For specific endpoints (in code):
# - Language detection: 4 hours (very stable)
# - Translation: 48 hours (very stable)
# - Sentiment: 2 hours (reasonably stable)
```

### 3. Monitoring

Set up alerts based on `/status` endpoint:
- Check `redis.active` status
- Monitor `alerts` array
- Log errors to your monitoring system

### 4. Production Checklist

- [ ] Upstash credentials configured
- [ ] Environment variables secured
- [ ] `/status` endpoint monitored
- [ ] Alerts integrated in frontend
- [ ] Fallback to file cache tested
- [ ] Error logging configured
- [ ] TTLs optimized for free tier

---

## 📈 Performance Expectations

### Upstash Free Tier Limits

- **Daily Requests**: 10,000 commands/day
- **Max DB Size**: 256 MB
- **Bandwidth**: 256 MB/day
- **Latency**: 50-200ms (global)

### Expected Cache Performance

**With Upstash:**
- Cache hit: ~100-200ms (including network)
- Cache miss: ~1500-2000ms (model inference)
- **Still 10-15x faster than no cache**

**Compared to Local Redis:**
- Local: ~10-20ms
- Upstash: ~100-200ms
- **Trade-off: Slightly slower but no infrastructure to manage**

---

## 🆘 Support

### API Logs

Check logs for Redis connection status:

```bash
# Local development
tail -f logs/app.log | grep -i redis

# Docker
docker-compose logs -f api | grep -i redis
```

### Upstash Console

Monitor your Redis instance:
- Dashboard: https://console.upstash.com/
- Metrics: Command count, bandwidth, latency
- Commands: View real-time commands

### Test Endpoints

```bash
# Quick health check
curl http://localhost:8000/redis/health | jq

# Full system status
curl http://localhost:8000/status | jq

# Detailed stats
curl http://localhost:8000/redis/stats | jq
```

---

## ✅ Success Checklist

After setup, verify:

1. **Redis Connected**
   ```bash
   curl http://localhost:8000/redis/health
   # Should return: "status": "healthy", "active": true
   ```

2. **Cache Working**
   ```bash
   # Make same request twice
   curl -X POST http://localhost:8000/analyze \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-api-key" \
     -d '{"text": "Hello world"}'
   
   # Second request should be faster and include cache metadata
   ```

3. **Frontend Status Display**
   - Visit your frontend
   - Should show "Cache Active (Upstash Cloud)"
   - No alerts displayed

4. **Graceful Degradation**
   - Temporarily disable Redis: `REDIS_ENABLED=false`
   - API should still work with file cache
   - Alert shown: "Redis caching is disabled"

---

## 🎉 Migration Complete!

Your NLP API is now using **Upstash Cloud Redis** instead of local Redis:

✅ No local Redis server needed  
✅ Free tier (10K commands/day)  
✅ Automatic SSL/TLS  
✅ Global availability  
✅ Frontend status indicators  
✅ Graceful fallback to file cache  
✅ Production-ready error handling  

**Next Steps:**
- Monitor usage in Upstash console
- Integrate status endpoint in your frontend
- Set up alerts for Redis failures
- Optimize TTLs based on usage patterns

---

**Questions?** Check the API docs at `/docs` or test with `/status` endpoint!
