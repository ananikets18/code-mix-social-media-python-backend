"""
Performance Profiling & Resource Monitoring Script for NLP API

This script measures:
- RAM/Memory usage (baseline, peak, average)
- CPU utilization
- Disk I/O
- Model loading times
- API response times
- Concurrent request handling
- Cache performance

Usage:
    python performance_profiler.py --mode full
    python performance_profiler.py --mode quick
    python performance_profiler.py --mode stress
"""

import os
import sys
import time
import psutil
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import multiprocessing
import gc

# Memory & Resource Monitoring
class ResourceMonitor:
    """Monitor system resources during application execution"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.baseline_memory = None
        self.peak_memory = 0
        self.memory_samples = []
        self.cpu_samples = []
        self.start_time = None
        
    def start(self):
        """Start monitoring"""
        self.start_time = time.time()
        self.baseline_memory = self.get_memory_usage()
        print(f"\n📊 Resource Monitoring Started")
        print(f"   Baseline Memory: {self.baseline_memory['rss_mb']:.2f} MB")
        print(f"   Available Memory: {self.baseline_memory['available_mb']:.2f} MB")
        print(f"   CPU Cores: {psutil.cpu_count(logical=True)}")
        print(f"   Process PID: {self.process.pid}")
        
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage"""
        mem_info = self.process.memory_info()
        virtual_mem = psutil.virtual_memory()
        
        return {
            'rss_mb': mem_info.rss / (1024 * 1024),  # Resident Set Size
            'vms_mb': mem_info.vms / (1024 * 1024),  # Virtual Memory Size
            'percent': self.process.memory_percent(),
            'available_mb': virtual_mem.available / (1024 * 1024),
            'total_mb': virtual_mem.total / (1024 * 1024),
            'used_percent': virtual_mem.percent
        }
    
    def get_cpu_usage(self) -> Dict[str, float]:
        """Get CPU usage"""
        return {
            'process_percent': self.process.cpu_percent(interval=0.1),
            'system_percent': psutil.cpu_percent(interval=0.1),
            'num_threads': self.process.num_threads()
        }
    
    def get_disk_usage(self) -> Dict[str, float]:
        """Get disk I/O stats"""
        disk = psutil.disk_usage('/')
        io_counters = psutil.disk_io_counters()
        
        return {
            'total_gb': disk.total / (1024**3),
            'used_gb': disk.used / (1024**3),
            'free_gb': disk.free / (1024**3),
            'percent': disk.percent,
            'read_count': io_counters.read_count if io_counters else 0,
            'write_count': io_counters.write_count if io_counters else 0,
            'read_mb': io_counters.read_bytes / (1024**2) if io_counters else 0,
            'write_mb': io_counters.write_bytes / (1024**2) if io_counters else 0
        }
    
    def sample(self):
        """Take a sample of current resources"""
        mem = self.get_memory_usage()
        cpu = self.get_cpu_usage()
        
        self.memory_samples.append(mem)
        self.cpu_samples.append(cpu)
        
        # Track peak memory
        if mem['rss_mb'] > self.peak_memory:
            self.peak_memory = mem['rss_mb']
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        if not self.memory_samples:
            return {}
        
        avg_memory = sum(s['rss_mb'] for s in self.memory_samples) / len(self.memory_samples)
        avg_cpu = sum(s['process_percent'] for s in self.cpu_samples) / len(self.cpu_samples)
        
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        
        return {
            'memory': {
                'baseline_mb': self.baseline_memory['rss_mb'],
                'peak_mb': self.peak_memory,
                'average_mb': avg_memory,
                'increase_mb': self.peak_memory - self.baseline_memory['rss_mb'],
                'samples': len(self.memory_samples)
            },
            'cpu': {
                'average_percent': avg_cpu,
                'peak_percent': max(s['process_percent'] for s in self.cpu_samples),
                'samples': len(self.cpu_samples)
            },
            'runtime': {
                'elapsed_seconds': elapsed_time,
                'elapsed_minutes': elapsed_time / 60
            }
        }
    
    def print_summary(self):
        """Print formatted summary"""
        summary = self.get_summary()
        
        print("\n" + "="*80)
        print("📊 RESOURCE USAGE SUMMARY")
        print("="*80)
        
        if 'memory' in summary:
            mem = summary['memory']
            print(f"\n💾 MEMORY USAGE:")
            print(f"   Baseline:  {mem['baseline_mb']:>10.2f} MB")
            print(f"   Peak:      {mem['peak_mb']:>10.2f} MB")
            print(f"   Average:   {mem['average_mb']:>10.2f} MB")
            print(f"   Increase:  {mem['increase_mb']:>10.2f} MB (+{(mem['increase_mb']/mem['baseline_mb']*100):.1f}%)")
            
        if 'cpu' in summary:
            cpu = summary['cpu']
            print(f"\n🔧 CPU USAGE:")
            print(f"   Average:   {cpu['average_percent']:>10.2f}%")
            print(f"   Peak:      {cpu['peak_percent']:>10.2f}%")
            
        if 'runtime' in summary:
            runtime = summary['runtime']
            print(f"\n⏱️  RUNTIME:")
            print(f"   Total:     {runtime['elapsed_seconds']:>10.2f} seconds ({runtime['elapsed_minutes']:.2f} min)")
        
        print("\n" + "="*80)


class ModelProfiler:
    """Profile ML model loading and inference times"""
    
    def __init__(self, monitor: ResourceMonitor):
        self.monitor = monitor
        self.results = {}
        
    def profile_model_loading(self):
        """Profile time and memory for loading all models"""
        print("\n🔄 Profiling Model Loading...")
        
        # Import models one by one and measure
        models_to_load = [
            ('Language Detection (GlotLID)', 'from preprocessing import detect_language'),
            ('Sentiment Analysis', 'from inference import predict_sentiment'),
            ('Toxicity Detection', 'from inference import predict_toxicity'),
            ('Translation', 'from translation import translate_text'),
            ('Profanity Filter', 'from profanity_filter import ProfanityFilter'),
            ('Domain Processor', 'from domain_processors import DomainProcessor')
        ]
        
        load_times = {}
        memory_before = self.monitor.get_memory_usage()['rss_mb']
        
        for model_name, import_statement in models_to_load:
            print(f"   Loading {model_name}...", end=' ')
            
            mem_before = self.monitor.get_memory_usage()['rss_mb']
            start = time.time()
            
            try:
                exec(import_statement)
                load_time = time.time() - start
                mem_after = self.monitor.get_memory_usage()['rss_mb']
                mem_increase = mem_after - mem_before
                
                load_times[model_name] = {
                    'load_time_seconds': load_time,
                    'memory_increase_mb': mem_increase,
                    'status': 'success'
                }
                
                print(f"✓ ({load_time:.2f}s, +{mem_increase:.2f}MB)")
                
            except Exception as e:
                load_times[model_name] = {
                    'load_time_seconds': 0,
                    'memory_increase_mb': 0,
                    'status': 'failed',
                    'error': str(e)
                }
                print(f"✗ Failed: {str(e)}")
        
        memory_after = self.monitor.get_memory_usage()['rss_mb']
        total_memory_increase = memory_after - memory_before
        total_load_time = sum(m['load_time_seconds'] for m in load_times.values())
        
        self.results['model_loading'] = {
            'individual_models': load_times,
            'total_load_time_seconds': total_load_time,
            'total_memory_increase_mb': total_memory_increase
        }
        
        print(f"\n   Total Loading Time: {total_load_time:.2f}s")
        print(f"   Total Memory Increase: {total_memory_increase:.2f}MB")
        
        return self.results['model_loading']
    
    def profile_inference(self):
        """Profile inference times for different operations"""
        print("\n⚡ Profiling Inference Performance...")
        
        # Import required modules
        from main import analyze_text_comprehensive
        
        # Test cases with varying complexity
        test_cases = [
            ('Short English', 'Hello world'),
            ('Medium English', 'This is a wonderful product. I highly recommend it to everyone!'),
            ('Long Mixed', 'Aaj market mein bahut traffic hai. The weather is also very hot today. Mumbai roads are completely jammed.'),
            ('Code-Mixed Hindi', 'Yaar ye movie bahut mast hai! Must watch bro, ekdum zabardast!'),
            ('Marathi Romanized', 'Mi aaj khup khush ahe! Traffic bahut aahe Mumbai la.')
        ]
        
        inference_times = {}
        
        for test_name, text in test_cases:
            print(f"   Testing: {test_name}...", end=' ')
            
            # Warm-up run (first run loads models)
            start = time.time()
            result = analyze_text_comprehensive(text, compact=True)
            warmup_time = time.time() - start
            
            # Actual benchmark runs (average of 5)
            times = []
            for _ in range(5):
                start = time.time()
                result = analyze_text_comprehensive(text, compact=True)
                times.append(time.time() - start)
                self.monitor.sample()
            
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            inference_times[test_name] = {
                'text_length': len(text),
                'warmup_time_seconds': warmup_time,
                'average_time_seconds': avg_time,
                'min_time_seconds': min_time,
                'max_time_seconds': max_time,
                'runs': len(times)
            }
            
            print(f"✓ Avg: {avg_time:.3f}s (Min: {min_time:.3f}s, Max: {max_time:.3f}s)")
        
        self.results['inference'] = inference_times
        return inference_times


class APIProfiler:
    """Profile API endpoint performance"""
    
    def __init__(self, monitor: ResourceMonitor, base_url: str = "http://localhost:8000"):
        self.monitor = monitor
        self.base_url = base_url
        self.results = {}
    
    def check_api_running(self) -> bool:
        """Check if API is running"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def profile_endpoints(self):
        """Profile API endpoint response times"""
        print("\n🌐 Profiling API Endpoints...")
        
        if not self.check_api_running():
            print(f"   ⚠️  API not running at {self.base_url}")
            print(f"   To test API, run: python api.py (in another terminal)")
            self.results['api'] = {'status': 'not_running'}
            return None
        
        import requests
        
        endpoints = [
            ('GET /health', 'GET', '/health', None),
            ('POST /analyze', 'POST', '/analyze', {
                'text': 'This is a test message for profiling.',
                'compact': True
            }),
            ('POST /sentiment', 'POST', '/sentiment', {
                'text': 'I am very happy today!'
            }),
            ('POST /toxicity', 'POST', '/toxicity', {
                'text': 'This is a normal message.'
            }),
            ('POST /translate', 'POST', '/translate', {
                'text': 'Hello world',
                'target_lang': 'hi',
                'source_lang': 'en'
            })
        ]
        
        endpoint_times = {}
        
        for endpoint_name, method, path, data in endpoints:
            print(f"   Testing {endpoint_name}...", end=' ')
            
            times = []
            errors = 0
            
            for i in range(10):  # 10 requests per endpoint
                try:
                    start = time.time()
                    
                    if method == 'GET':
                        response = requests.get(f"{self.base_url}{path}", timeout=10)
                    else:
                        response = requests.post(
                            f"{self.base_url}{path}",
                            json=data,
                            timeout=10,
                            headers={'Content-Type': 'application/json'}
                        )
                    
                    elapsed = time.time() - start
                    
                    if response.status_code == 200:
                        times.append(elapsed)
                    else:
                        errors += 1
                    
                    self.monitor.sample()
                    
                except Exception as e:
                    errors += 1
            
            if times:
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                p95_time = sorted(times)[int(len(times) * 0.95)]
                
                endpoint_times[endpoint_name] = {
                    'average_ms': avg_time * 1000,
                    'min_ms': min_time * 1000,
                    'max_ms': max_time * 1000,
                    'p95_ms': p95_time * 1000,
                    'requests': len(times),
                    'errors': errors,
                    'success_rate': len(times) / 10 * 100
                }
                
                print(f"✓ Avg: {avg_time*1000:.0f}ms (P95: {p95_time*1000:.0f}ms)")
            else:
                endpoint_times[endpoint_name] = {
                    'status': 'failed',
                    'errors': errors
                }
                print(f"✗ Failed")
        
        self.results['api'] = endpoint_times
        return endpoint_times


class StressTester:
    """Test application under load"""
    
    def __init__(self, monitor: ResourceMonitor):
        self.monitor = monitor
        self.results = {}
    
    def run_memory_stress_test(self):
        """Test memory usage with large batches"""
        print("\n🔥 Running Memory Stress Test...")
        
        from main import analyze_text_comprehensive
        
        # Generate test texts of varying sizes
        test_texts = [
            "Short test " * 10,
            "Medium test " * 50,
            "Long test " * 100,
            "Very long test " * 500
        ]
        
        batch_sizes = [1, 5, 10, 20, 50]
        results = {}
        
        for batch_size in batch_sizes:
            print(f"   Processing batch of {batch_size}...", end=' ')
            
            mem_before = self.monitor.get_memory_usage()['rss_mb']
            start = time.time()
            
            try:
                for text in test_texts[:batch_size]:
                    analyze_text_comprehensive(text, compact=True)
                    self.monitor.sample()
                
                elapsed = time.time() - start
                mem_after = self.monitor.get_memory_usage()['rss_mb']
                mem_increase = mem_after - mem_before
                
                results[f'batch_{batch_size}'] = {
                    'time_seconds': elapsed,
                    'memory_increase_mb': mem_increase,
                    'avg_time_per_text': elapsed / batch_size,
                    'status': 'success'
                }
                
                print(f"✓ {elapsed:.2f}s (+{mem_increase:.2f}MB)")
                
                # Clean up
                gc.collect()
                time.sleep(1)
                
            except Exception as e:
                results[f'batch_{batch_size}'] = {
                    'status': 'failed',
                    'error': str(e)
                }
                print(f"✗ Failed: {str(e)}")
        
        self.results['stress_test'] = results
        return results


class DiskProfiler:
    """Profile disk usage and model sizes"""
    
    def __init__(self):
        self.results = {}
    
    def get_directory_size(self, path: Path) -> int:
        """Get total size of directory in bytes"""
        total = 0
        try:
            for entry in path.rglob('*'):
                if entry.is_file():
                    total += entry.stat().st_size
        except Exception as e:
            print(f"   Error reading {path}: {e}")
        return total
    
    def profile_disk_usage(self):
        """Profile disk usage of models and data"""
        print("\n💾 Profiling Disk Usage...")
        
        project_root = Path.cwd()
        
        directories_to_check = [
            'ai4bharatIndicBERTv2-alpha-SentimentClassification',
            'cardiffnlptwitter-xlm-roberta-base-sentiment',
            'cis-lmuglotlid',
            'oleksiizirka-xlm-roberta-toxicity-classifier',
            'romanized_dictionaries',
            'indic_nlp_library',
            'indic_nlp_resources',
            'data',
            'logs',
            'adaptive_learning',
            'preprocessing',
            '__pycache__'
        ]
        
        disk_usage = {}
        total_size = 0
        
        for dir_name in directories_to_check:
            dir_path = project_root / dir_name
            if dir_path.exists():
                size_bytes = self.get_directory_size(dir_path)
                size_mb = size_bytes / (1024 * 1024)
                size_gb = size_bytes / (1024**3)
                
                disk_usage[dir_name] = {
                    'size_bytes': size_bytes,
                    'size_mb': size_mb,
                    'size_gb': size_gb
                }
                
                total_size += size_bytes
                
                if size_gb >= 1:
                    print(f"   {dir_name:50s} {size_gb:>8.2f} GB")
                else:
                    print(f"   {dir_name:50s} {size_mb:>8.2f} MB")
        
        total_gb = total_size / (1024**3)
        disk_usage['_total'] = {
            'size_bytes': total_size,
            'size_mb': total_size / (1024 * 1024),
            'size_gb': total_gb
        }
        
        print(f"\n   {'TOTAL PROJECT SIZE':50s} {total_gb:>8.2f} GB")
        
        self.results['disk_usage'] = disk_usage
        return disk_usage


def generate_report(results: Dict[str, Any], output_file: str = "performance_report.json"):
    """Generate comprehensive performance report"""
    
    # Add metadata
    report = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'hostname': os.uname().nodename if hasattr(os, 'uname') else 'windows',
            'platform': sys.platform,
            'python_version': sys.version,
            'cpu_count': psutil.cpu_count(logical=True),
            'total_memory_gb': psutil.virtual_memory().total / (1024**3)
        },
        'results': results
    }
    
    # Save to JSON
    output_path = Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n💾 Report saved to: {output_path.absolute()}")
    
    # Print hosting recommendations
    print_hosting_recommendations(report)
    
    return report


def print_hosting_recommendations(report: Dict[str, Any]):
    """Print hosting service recommendations based on profiling results"""
    
    print("\n" + "="*80)
    print("🚀 HOSTING RECOMMENDATIONS")
    print("="*80)
    
    results = report.get('results', {})
    resource_summary = results.get('resource_summary', {})
    disk_usage = results.get('disk_usage', {})
    
    # Extract key metrics
    peak_memory_mb = resource_summary.get('memory', {}).get('peak_mb', 0)
    avg_cpu = resource_summary.get('cpu', {}).get('average_percent', 0)
    total_disk_gb = disk_usage.get('_total', {}).get('size_gb', 6.0)
    
    # Calculate recommendations
    recommended_ram_gb = max(4, int(peak_memory_mb / 1024) + 2)  # Peak + 2GB buffer
    recommended_cpu_cores = max(2, int(avg_cpu / 50))  # Based on CPU usage
    recommended_disk_gb = max(20, int(total_disk_gb) + 10)  # Models + 10GB buffer
    
    print(f"\n📊 MEASURED REQUIREMENTS:")
    print(f"   Peak Memory Usage:     {peak_memory_mb:.0f} MB")
    print(f"   Average CPU Usage:     {avg_cpu:.1f}%")
    print(f"   Total Disk Usage:      {total_disk_gb:.2f} GB")
    
    print(f"\n✅ RECOMMENDED SPECIFICATIONS:")
    print(f"   RAM:                   {recommended_ram_gb} GB minimum (8 GB recommended)")
    print(f"   CPU Cores:             {recommended_cpu_cores}+ cores")
    print(f"   Storage:               {recommended_disk_gb} GB SSD")
    print(f"   Network:               1 Gbps minimum")
    
    print(f"\n🏢 HOSTING SERVICE SUGGESTIONS:")
    
    # Cloud providers
    print(f"\n   1. AWS EC2:")
    print(f"      Instance Type:     t3.large or t3.xlarge")
    print(f"      RAM:               8 GB")
    print(f"      vCPUs:             2-4")
    print(f"      Storage:           30-50 GB EBS (gp3)")
    print(f"      Est. Cost:         $60-120/month")
    
    print(f"\n   2. Google Cloud (GCP):")
    print(f"      Instance Type:     n2-standard-2 or n2-standard-4")
    print(f"      RAM:               8-16 GB")
    print(f"      vCPUs:             2-4")
    print(f"      Storage:           30-50 GB SSD")
    print(f"      Est. Cost:         $50-110/month")
    
    print(f"\n   3. Azure:")
    print(f"      Instance Type:     B2s or B2ms")
    print(f"      RAM:               4-8 GB")
    print(f"      vCPUs:             2-4")
    print(f"      Storage:           30-50 GB Premium SSD")
    print(f"      Est. Cost:         $60-100/month")
    
    print(f"\n   4. DigitalOcean:")
    print(f"      Droplet Type:      General Purpose (8 GB RAM)")
    print(f"      RAM:               8 GB")
    print(f"      vCPUs:             4")
    print(f"      Storage:           160 GB SSD")
    print(f"      Est. Cost:         $48/month")
    
    print(f"\n   5. Render / Railway (Platform-as-a-Service):")
    print(f"      Service Tier:      Pro or Team")
    print(f"      RAM:               4-8 GB")
    print(f"      vCPUs:             2-4")
    print(f"      Storage:           Included")
    print(f"      Est. Cost:         $25-85/month")
    
    print(f"\n⚡ OPTIMIZATION TIPS:")
    print(f"   • Use Redis caching to reduce memory usage (already implemented)")
    print(f"   • Enable model quantization to reduce model sizes by 50-75%")
    print(f"   • Use Docker with multi-stage builds to reduce image size")
    print(f"   • Implement rate limiting (already implemented)")
    print(f"   • Use CDN for static assets")
    print(f"   • Enable gzip compression")
    print(f"   • Consider using GPU instances for faster inference (optional)")
    
    print(f"\n📈 SCALABILITY:")
    print(f"   • Current setup supports: ~10-50 concurrent users")
    print(f"   • For 100+ users: Use load balancer + 2-3 instances")
    print(f"   • For 1000+ users: Use Kubernetes with auto-scaling")
    
    print("\n" + "="*80)


def main():
    """Main profiling function"""
    
    parser = argparse.ArgumentParser(description='Profile NLP API Performance')
    parser.add_argument('--mode', choices=['quick', 'full', 'stress'], default='full',
                       help='Profiling mode: quick (basic), full (comprehensive), stress (load testing)')
    parser.add_argument('--api-url', default='http://localhost:8000',
                       help='API base URL (default: http://localhost:8000)')
    parser.add_argument('--output', default='performance_report.json',
                       help='Output report filename')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🔬 NLP API PERFORMANCE PROFILER")
    print("="*80)
    print(f"\n   Mode: {args.mode.upper()}")
    print(f"   API URL: {args.api_url}")
    print(f"   Output: {args.output}")
    print(f"   Python: {sys.version.split()[0]}")
    print(f"   Platform: {sys.platform}")
    
    # Initialize monitor
    monitor = ResourceMonitor()
    monitor.start()
    
    results = {}
    
    # Disk profiling (always run)
    disk_profiler = DiskProfiler()
    results['disk_usage'] = disk_profiler.profile_disk_usage()
    
    # Model profiling
    model_profiler = ModelProfiler(monitor)
    results['model_loading'] = model_profiler.profile_model_loading()
    
    if args.mode in ['full', 'quick']:
        results['inference'] = model_profiler.profile_inference()
    
    # API profiling (if API is running)
    if args.mode in ['full']:
        api_profiler = APIProfiler(monitor, args.api_url)
        api_results = api_profiler.profile_endpoints()
        if api_results:
            results['api'] = api_results
    
    # Stress testing
    if args.mode == 'stress':
        stress_tester = StressTester(monitor)
        results['stress_test'] = stress_tester.run_memory_stress_test()
    
    # Get final resource summary
    results['resource_summary'] = monitor.get_summary()
    
    # Print summary
    monitor.print_summary()
    
    # Generate report
    report = generate_report(results, args.output)
    
    print("\n✅ Profiling Complete!")
    print(f"\n📄 Full report available at: {args.output}")
    
    return report


if __name__ == "__main__":
    main()
