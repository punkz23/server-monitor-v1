#!/usr/bin/env python
"""
Performance Test Script
Tests dashboard load time before and after optimizations
"""

import time
import os
import sys

# Add project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')

import django
from django.test import Client
from django.core.cache import cache

# Setup Django
django.setup()

def test_dashboard_performance():
    """Test dashboard loading performance"""
    print("🚀 Dashboard Performance Test")
    print("=" * 50)
    
    # Clear cache to test fresh load
    cache.clear()
    
    client = Client()
    
    # Test 1: Cold cache load
    print("\n📊 Test 1: Cold Cache Load")
    start_time = time.time()
    response = client.get('/')
    end_time = time.time()
    cold_load_time = end_time - start_time
    print(f"   Load Time: {cold_load_time:.3f}s")
    print(f"   Status Code: {response.status_code}")
    
    # Test 2: Warm cache load
    print("\n📊 Test 2: Warm Cache Load")
    start_time = time.time()
    response = client.get('/')
    end_time = time.time()
    warm_load_time = end_time - start_time
    print(f"   Load Time: {warm_load_time:.3f}s")
    print(f"   Status Code: {response.status_code}")
    
    # Test 3: Database query analysis
    print("\n📊 Test 3: Database Query Analysis")
    from django.db import connection
    
    # Reset queries to count dashboard queries
    connection.reset_queries()
    
    start_time = time.time()
    response = client.get('/')
    end_time = time.time()
    
    queries = connection.queries
    query_count = len(queries)
    db_time = end_time - start_time
    
    print(f"   Query Count: {query_count}")
    print(f"   DB Time: {db_time:.3f}s")
    print(f"   Avg Query Time: {db_time/max(query_count, 1)*1000:.2f}ms" if query_count > 0 else "N/A")
    
    # Performance Summary
    print("\n🎯 Performance Summary")
    print("=" * 50)
    improvement = ((cold_load_time - warm_load_time) / cold_load_time) * 100
    print(f"   Cache Improvement: {improvement:.1f}%")
    print(f"   Cold Load: {cold_load_time:.3f}s")
    print(f"   Warm Load: {warm_load_time:.3f}s")
    print(f"   Query Count: {query_count}")
    
    # Recommendations
    print("\n💡 Recommendations:")
    if cold_load_time > 2.0:
        print("   ⚠️  Dashboard load time is slow (>2s)")
        print("   🔧 Consider optimizing database queries")
        print("   🔧 Enable Redis cache for production")
    
    if query_count > 50:
        print("   ⚠️  High number of database queries")
        print("   🔧 Add select_related/prefetch_related")
        print("   🔧 Implement query optimization")
    
    if improvement < 20:
        print("   ⚠️  Low cache effectiveness")
        print("   🔧 Check cache configuration")
    else:
        print("   ✅  Good performance achieved!")

if __name__ == "__main__":
    test_dashboard_performance()
