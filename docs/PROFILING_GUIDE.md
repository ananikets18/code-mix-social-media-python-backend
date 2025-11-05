# 🔬 Performance Profiling Guide

## Quick Start - Test Your NLP Application

### Prerequisites

1. **Install required package** (if not already installed):
```powershell
pip install psutil
```

## 🚀 Testing Methods

### Method 1: Basic Profiling (Recommended for First Test)

This profiles model loading and inference without needing the API running.

```powershell
# Quick test (2-3 minutes)
python performance_profiler.py --mode quick

# Full test (5-10 minutes) - RECOMMENDED
python performance_profiler.py --mode full

# Stress test (heavy load testing)
python performance_profiler.py --mode stress
```

**What it measures:**
- ✅ Model loading times and memory usage
- ✅ Inference performance (5 test cases)
- ✅ Total disk usage (~6 GB)
- ✅ Peak/Average RAM consumption
- ✅ CPU utilization
- ⚠️ API endpoints (only if API is running)

### Method 2: Full API Profiling (With Live API)

Test API performance with live server.

**Step 1: Start the API** (in one terminal)
```powershell
# Terminal 1
python api.py
```

**Step 2: Run profiler** (in another terminal)
```powershell
# Terminal 2
python performance_profiler.py --mode full --api-url http://localhost:8000
```

### Method 3: Docker Container Profiling

Test resource usage inside Docker.

**Step 1: Build and run Docker container**
```powershell
docker-compose up -d
```

**Step 2: Profile the container**
```powershell
# Monitor for 5 minutes (300 seconds)
python docker_profiler.py --container nlp-api --duration 300 --interval 5

# Or let it auto-detect the container
python docker_profiler.py --duration 300
```

## 📊 Understanding the Output

### Console Output
```
📊 RESOURCE USAGE SUMMARY
================================================================================

💾 MEMORY USAGE:
   Baseline:      XX.XX MB    <- Starting memory
   Peak:          XXXX.XX MB  <- Maximum memory used
   Average:       XXX.XX MB   <- Average during test
   Increase:      XXX.XX MB   <- Memory consumed by models

🔧 CPU USAGE:
   Average:       XX.XX%      <- Average CPU utilization
   Peak:          XX.XX%      <- Maximum CPU spike

⏱️  RUNTIME:
   Total:         XX.XX seconds
```

### JSON Report (`performance_report.json`)
```json
{
  "metadata": {
    "timestamp": "2025-11-04T...",
    "cpu_count": 8,
    "total_memory_gb": 16.0
  },
  "results": {
    "disk_usage": { ... },
    "model_loading": { ... },
    "inference": { ... },
    "resource_summary": { ... }
  }
}
```

### Hosting Recommendations
```
🚀 HOSTING RECOMMENDATIONS
================================================================================

📊 MEASURED REQUIREMENTS:
   Peak Memory Usage:     XXXX MB
   Average CPU Usage:     XX.X%
   Total Disk Usage:      X.XX GB

✅ RECOMMENDED SPECIFICATIONS:
   RAM:                   8 GB minimum
   CPU Cores:             2+ cores
   Storage:               20-30 GB SSD

🏢 HOSTING SERVICE SUGGESTIONS:
   1. AWS EC2: t3.large ($60-120/month)
   2. Google Cloud: n2-standard-2 ($50-110/month)
   3. DigitalOcean: 8GB Droplet ($48/month)
   ...
```

## 🧪 Example Test Scenarios

### Scenario 1: Quick Local Test (No API)
```powershell
# Install psutil if needed
pip install psutil

# Run quick profiling
python performance_profiler.py --mode quick --output quick_test.json
```

**Expected time:** 2-3 minutes  
**Measures:** Model loading + basic inference

---

### Scenario 2: Comprehensive Analysis
```powershell
# Full profiling with all tests
python performance_profiler.py --mode full --output full_report.json
```

**Expected time:** 5-10 minutes  
**Measures:** Everything except API (if not running)

---

### Scenario 3: API Performance Testing
```powershell
# Terminal 1: Start API
python api.py

# Terminal 2: Profile API
python performance_profiler.py --mode full --api-url http://localhost:8000
```

**Expected time:** 5-10 minutes  
**Measures:** Models + Inference + API endpoints

---

### Scenario 4: Stress Testing
```powershell
# Test with heavy load
python performance_profiler.py --mode stress --output stress_test.json
```

**Expected time:** 3-5 minutes  
**Measures:** Memory usage under batch processing

---

### Scenario 5: Docker Container Monitoring
```powershell
# Start container
docker-compose up -d

# Monitor for 5 minutes
python docker_profiler.py --container nlp-api --duration 300

# View running containers
python docker_profiler.py --all
```

**Expected time:** 5 minutes (configurable)  
**Measures:** Container CPU, memory, network, disk I/O

## 📁 Output Files

After running, you'll get:

1. **performance_report.json** - Detailed metrics
2. **docker_profiling_report.json** - Docker container stats (if using docker_profiler)
3. **Console output** - Real-time progress and recommendations

## 🎯 What to Look For

### Memory Usage
- **Baseline:** ~50-200 MB (Python + dependencies)
- **After models:** ~2000-4000 MB (models loaded)
- **Peak:** ~3000-5000 MB (during inference)

### CPU Usage
- **Idle:** ~5-10%
- **Model loading:** ~50-100%
- **Inference:** ~30-80%

### Disk Usage
- **Total project:** ~6 GB
- **Models:** ~5-5.5 GB
- **Code + data:** ~500 MB

### API Response Times (if tested)
- **GET /health:** <50ms
- **POST /analyze:** 500-2000ms (first request)
- **POST /analyze:** 200-800ms (cached)
- **POST /sentiment:** 100-500ms

## ⚡ Quick Commands Summary

```powershell
# 1. Basic test (no API needed)
python performance_profiler.py --mode quick

# 2. Full test (recommended)
python performance_profiler.py --mode full

# 3. With API running
python performance_profiler.py --mode full --api-url http://localhost:8000

# 4. Stress test
python performance_profiler.py --mode stress

# 5. Docker monitoring
python docker_profiler.py --duration 300

# 6. Install dependencies if needed
pip install psutil requests
```

## 🐛 Troubleshooting

### Issue: ModuleNotFoundError: No module named 'psutil'
**Solution:**
```powershell
pip install psutil
```

### Issue: ModuleNotFoundError: No module named 'requests'
**Solution:**
```powershell
pip install requests
```

### Issue: API not running (when testing endpoints)
**Solution:**
```powershell
# Start API in separate terminal
python api.py
```

### Issue: Docker container not found
**Solution:**
```powershell
# Check running containers
docker ps

# Start your container
docker-compose up -d

# List all containers
python docker_profiler.py --all
```

## 📈 Next Steps After Profiling

1. **Review the report:** Check `performance_report.json`
2. **Check hosting recommendations:** See console output
3. **Optimize if needed:** Based on memory/CPU usage
4. **Choose hosting provider:** Based on budget and requirements
5. **Deploy:** Use recommended instance type

## 💡 Tips

- Run profiling on the same machine where you plan to develop/test
- Close other heavy applications for accurate results
- Run multiple times to get consistent measurements
- Use `--mode full` for most comprehensive analysis
- Docker profiling gives the most realistic production metrics

---

**Ready to start?** Run this command:
```powershell
python performance_profiler.py --mode full
```
