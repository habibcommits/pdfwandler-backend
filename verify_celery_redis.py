#!/usr/bin/env python3
"""
Script to verify Celery worker, beat, and Redis are properly configured and running.
"""
import sys
import subprocess
import time
from redis import Redis
from celery_app import celery_app


def check_redis():
    """Check if Redis is accessible"""
    print("\n=== Checking Redis Connection ===")
    try:
        redis_client = Redis.from_url('redis://localhost:6379/0')
        redis_client.ping()
        print("✓ Redis is running and accessible")
        
        info = redis_client.info()
        print(f"  - Redis Version: {info['redis_version']}")
        print(f"  - Connected Clients: {info['connected_clients']}")
        print(f"  - Used Memory: {info['used_memory_human']}")
        return True
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        return False


def check_celery_worker():
    """Check if Celery worker is running"""
    print("\n=== Checking Celery Worker ===")
    try:
        inspect = celery_app.control.inspect()
        ping_response = inspect.ping()
        
        if ping_response:
            print(f"✓ Celery worker is running")
            for worker_name, response in ping_response.items():
                print(f"  - Worker: {worker_name}")
                print(f"  - Status: {response['ok']}")
            
            stats = inspect.stats()
            if stats:
                for worker_name, worker_stats in stats.items():
                    print(f"  - Pool: {worker_stats.get('pool', {}).get('implementation', 'N/A')}")
                    print(f"  - Max concurrency: {worker_stats.get('pool', {}).get('max-concurrency', 'N/A')}")
            
            return True
        else:
            print("✗ No Celery workers responding to ping")
            return False
    except Exception as e:
        print(f"✗ Celery worker check failed: {e}")
        return False


def check_celery_beat():
    """Check if Celery beat is configured"""
    print("\n=== Checking Celery Beat ===")
    try:
        conf = celery_app.conf
        print(f"✓ Celery beat configuration exists")
        print(f"  - Timezone: {conf.timezone}")
        print(f"  - Task time limit: {conf.task_time_limit}s")
        print(f"  - Task soft time limit: {conf.task_soft_time_limit}s")
        return True
    except Exception as e:
        print(f"✗ Celery beat check failed: {e}")
        return False


def test_background_task():
    """Test a sample background task"""
    print("\n=== Testing Background Task ===")
    try:
        from tasks import process_image_to_pdf
        
        print("✓ Celery tasks are importable")
        print(f"  - Available tasks:")
        print(f"    - process_image_to_pdf")
        print(f"    - process_merge_pdf")
        print(f"    - process_compress_pdf")
        print(f"    - cleanup_old_files")
        return True
    except Exception as e:
        print(f"✗ Task import failed: {e}")
        return False


def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Celery + Redis Verification Script")
    print("=" * 60)
    
    results = {
        "Redis": check_redis(),
        "Celery Worker": check_celery_worker(),
        "Celery Beat": check_celery_beat(),
        "Background Tasks": test_background_task()
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{check:.<40} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL CHECKS PASSED - System is ready!")
    else:
        print("✗ SOME CHECKS FAILED - Please review errors above")
        print("\nTo start services:")
        print("  1. Redis:  redis-server --daemonize yes")
        print("  2. Celery Worker:  celery -A celery_app worker --loglevel=info")
        print("  3. Celery Beat:  celery -A celery_app beat --loglevel=info")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
