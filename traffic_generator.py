import requests
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor
import sys

BASE_URL = "http://localhost:8000"

endpoints = [
    "/",
    "/slow", 
    "/error",
    "/health",
    "/cpu-intensive"
]

# Weight different endpoints to create realistic traffic patterns
endpoint_weights = {
    "/": 0.4,           # Most common - root endpoint
    "/health": 0.3,     # Health checks are frequent
    "/slow": 0.1,       # Occasional slow operations
    "/error": 0.1,      # Some error scenarios
    "/cpu-intensive": 0.1  # CPU intensive operations
}

def weighted_choice(choices):
    """Choose endpoint based on weights"""
    total = sum(choices.values())
    r = random.uniform(0, total)
    upto = 0
    for choice, weight in choices.items():
        if upto + weight >= r:
            return choice
        upto += weight
    return list(choices.keys())[-1]

def make_request():
    endpoint = weighted_choice(endpoint_weights)
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        duration = time.time() - start_time
        
        status_emoji = "✅" if response.status_code < 400 else "❌"
        print(f"{status_emoji} GET {endpoint} - Status: {response.status_code} - Duration: {duration:.3f}s")
        
        return response.status_code, duration
    except requests.exceptions.Timeout:
        print(f"⏰ GET {endpoint} - TIMEOUT")
        return 408, 10.0
    except Exception as e:
        print(f"💥 GET {endpoint} - ERROR: {e}")
        return 500, 0.0

def generate_burst_traffic():
    """Generate burst traffic to simulate real-world patterns"""
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(20)]
        for future in futures:
            try:
                future.result(timeout=15)
            except Exception as e:
                print(f"Request failed: {e}")

def generate_steady_traffic(duration=300, requests_per_minute=30):
    """Generate steady background traffic"""
    start_time = time.time()
    request_count = 0
    
    print(f"🚀 Starting steady traffic generation for {duration}s at {requests_per_minute} req/min")
    
    while time.time() - start_time < duration:
        make_request()
        request_count += 1
        
        # Calculate sleep time to maintain desired rate
        elapsed = time.time() - start_time
        expected_requests = (elapsed / 60) * requests_per_minute
        
        if request_count > expected_requests:
            sleep_time = (request_count - expected_requests) * (60 / requests_per_minute)
            time.sleep(sleep_time)
        
        # Add some randomness to avoid perfectly regular patterns
        time.sleep(random.uniform(0.5, 2.0))

def generate_mixed_traffic(duration=180):
    """Generate mixed traffic patterns"""
    start_time = time.time()
    
    print(f"🎯 Starting mixed traffic generation for {duration}s")
    print("This includes:")
    print("- Steady background traffic")
    print("- Periodic burst traffic")
    print("- Random spikes")
    
    # Start background steady traffic
    steady_thread = threading.Thread(
        target=generate_steady_traffic, 
        args=(duration, 20)
    )
    steady_thread.daemon = True
    steady_thread.start()
    
    # Generate periodic bursts
    while time.time() - start_time < duration:
        # Wait for next burst
        time.sleep(random.uniform(15, 30))
        
        if time.time() - start_time < duration:
            print("💥 Generating traffic burst...")
            generate_burst_traffic()
    
    print("✨ Traffic generation completed!")

def test_endpoints():
    """Test all endpoints to ensure they're working"""
    print("🔍 Testing all endpoints...")
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            status_emoji = "✅" if response.status_code < 400 else "❌"
            print(f"{status_emoji} {endpoint} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
    
    print()

if __name__ == "__main__":
    # Check if service is available
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Service not healthy. Please start the FastAPI service first.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to service at {BASE_URL}")
        print("Please ensure the FastAPI service is running with: docker-compose up -d")
        sys.exit(1)
    
    print("🌟 FastAPI Monitoring Traffic Generator")
    print("=" * 50)
    
    # Test all endpoints first
    test_endpoints()
    
    # Generate traffic based on command line argument or default
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 180
    generate_mixed_traffic(duration)