#!/usr/bin/env python3
"""
Test script to verify cron environment variable fix.
This script checks if environment variables are properly loaded for ETL execution.
"""

import os
import sys
import logging
from datetime import datetime

# Add current directory to path to import config
sys.path.insert(0, '/app')

import config
from es_populate import JiraElasticsearchPopulator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_environment_variables():
    """Test if critical environment variables are properly set."""
    print("=" * 60)
    print(f"Environment Variable Test - {datetime.now()}")
    print("=" * 60)
    
    # Critical environment variables
    env_vars = {
        'DOCKER_ENV': os.environ.get('DOCKER_ENV'),
        'ELASTIC_URL': os.environ.get('ELASTIC_URL'), 
        'ELASTIC_APIKEY': os.environ.get('ELASTIC_APIKEY'),
        'JIRA_BASE_URL': os.environ.get('JIRA_BASE_URL'),
        'JIRA_API_TOKEN': os.environ.get('JIRA_API_TOKEN'),
        'PYTHONPATH': os.environ.get('PYTHONPATH'),
        'TZ': os.environ.get('TZ')
    }
    
    success = True
    for var_name, var_value in env_vars.items():
        if var_value:
            if 'TOKEN' in var_name or 'KEY' in var_name:
                print(f"✓ {var_name}: ***SET***")
            else:
                print(f"✓ {var_name}: {var_value}")
        else:
            print(f"✗ {var_name}: NOT SET")
            if var_name in ['DOCKER_ENV', 'ELASTIC_URL', 'JIRA_BASE_URL']:
                success = False
    
    return success

def test_config_values():
    """Test configuration values from config.py."""
    print("\n" + "=" * 60)
    print("Configuration Values Test")
    print("=" * 60)
    
    # Get Elasticsearch config
    es_config = config.get_elasticsearch_config()
    
    print(f"✓ ES Host: {es_config['host']}")
    print(f"✓ ES Port: {es_config['port']}")
    print(f"✓ ES URL: {es_config['url'] or 'Not set'}")
    print(f"✓ ES SSL: {es_config['use_ssl']}")
    print(f"✓ ES API Key: {'***SET***' if es_config['api_key'] else 'Not set'}")
    
    # Check if we're using the correct host for Docker environment
    expected_host = 'elastic.voyager.pl' if es_config['url'] else 'elasticsearch'
    actual_host = es_config['host']
    
    if 'localhost' in actual_host:
        print(f"⚠  WARNING: Using localhost ({actual_host}) - this suggests environment variables are not loaded correctly")
        return False
    else:
        print(f"✓ Using correct host: {actual_host}")
        return True

def test_elasticsearch_connection():
    """Test actual connection to Elasticsearch."""
    print("\n" + "=" * 60)
    print("Elasticsearch Connection Test")
    print("=" * 60)
    
    try:
        # Create populator instance
        populator = JiraElasticsearchPopulator(agent_name="TestAgent")
        
        # Try to connect
        populator.connect()
        
        print("✓ Successfully connected to Elasticsearch!")
        print(f"✓ Connection URL: {populator.base_url}")
        
        # Try a simple health check
        health_info = populator.get_cluster_health()
        if health_info:
            print(f"✓ Cluster status: {health_info.get('status', 'unknown')}")
            return True
        else:
            print("⚠  Could not get cluster health info")
            return False
            
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Starting Cron Environment Fix Validation...")
    
    # Test 1: Environment variables
    env_success = test_environment_variables()
    
    # Test 2: Configuration values  
    config_success = test_config_values()
    
    # Test 3: Actual connection
    connection_success = test_elasticsearch_connection()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    tests = [
        ("Environment Variables", env_success),
        ("Configuration Values", config_success), 
        ("Elasticsearch Connection", connection_success)
    ]
    
    all_passed = True
    for test_name, passed in tests:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Cron environment fix is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
