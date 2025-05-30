#!/usr/bin/env python3
"""
Script to initialize Elasticsearch with Polish language support.
This script creates indices with proper Polish analyzers for full-text search.
"""

import requests
import json
import time
import sys
import os
try:
    from es_mapping_polish import CHANGELOG_MAPPING_POLISH, SETTINGS_MAPPING_POLISH
    from es_mapping_simple import CHANGELOG_MAPPING_SIMPLE, SETTINGS_MAPPING_SIMPLE
    POLISH_MAPPING_AVAILABLE = True
except ImportError:
    from es_mapping_simple import CHANGELOG_MAPPING_SIMPLE, SETTINGS_MAPPING_SIMPLE
    POLISH_MAPPING_AVAILABLE = False
import config

def wait_for_elasticsearch(host="localhost", port=9200, timeout=300):
    """Wait for Elasticsearch to be ready."""
    print(f"Waiting for Elasticsearch at {host}:{port}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"http://{host}:{port}/_cluster/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                print(f"Elasticsearch is ready! Cluster status: {health.get('status', 'unknown')}")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(".", end="", flush=True)
        time.sleep(2)
    
    print(f"\nTimeout waiting for Elasticsearch after {timeout} seconds")
    return False

def install_plugins(host="localhost", port=9200):
    """Check if required plugins are installed."""
    try:
        response = requests.get(f"http://{host}:{port}/_nodes/plugins", timeout=10)
        if response.status_code == 200:
            plugins_data = response.json()
            installed_plugins = []
            
            for node_id, node_data in plugins_data.get("nodes", {}).items():
                for plugin in node_data.get("plugins", []):
                    installed_plugins.append(plugin.get("name"))
            
            required_plugins = ["analysis-stempel", "analysis-icu"]
            missing_plugins = [p for p in required_plugins if p not in installed_plugins]
            
            if missing_plugins:
                print(f"Warning: Missing plugins: {missing_plugins}")
                print("Please install them in the Elasticsearch container:")
                for plugin in missing_plugins:
                    print(f"  elasticsearch-plugin install {plugin}")
                return False
            else:
                print("All required plugins are installed!")
                return True
                
    except Exception as e:
        print(f"Error checking plugins: {e}")
        return False

def create_index_with_mapping(host, port, index_name, mapping):
    """Create an index with the specified mapping."""
    url = f"http://{host}:{port}/{index_name}"
    
    # Delete index if it exists
    try:
        delete_response = requests.delete(url, timeout=10)
        if delete_response.status_code in [200, 404]:
            print(f"Index {index_name} deleted (or didn't exist)")
    except Exception as e:
        print(f"Warning: Could not delete index {index_name}: {e}")
    
    # Create index with mapping
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.put(url, json=mapping, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print(f"✓ Index {index_name} created successfully")
            return True
        else:
            print(f"✗ Failed to create index {index_name}: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error creating index {index_name}: {e}")
        return False

def create_index_with_fallback(host, port, index_name):
    """Create an index with Polish mapping, falling back to simple mapping if needed."""
    # Try Polish mapping first (if available)
    if POLISH_MAPPING_AVAILABLE:
        print(f"Attempting to create {index_name} with Polish Stempel analyzer...")
        if index_name == config.INDEX_CHANGELOG:
            if create_index_with_mapping(host, port, index_name, CHANGELOG_MAPPING_POLISH):
                return True
        else:
            if create_index_with_mapping(host, port, index_name, SETTINGS_MAPPING_POLISH):
                return True
    
    # Fall back to simple mapping
    print(f"Falling back to simple Polish mapping for {index_name}...")
    if index_name == config.INDEX_CHANGELOG:
        return create_index_with_mapping(host, port, index_name, CHANGELOG_MAPPING_SIMPLE)
    else:
        return create_index_with_mapping(host, port, index_name, SETTINGS_MAPPING_SIMPLE)

def test_polish_analyzer(host, port, index_name):
    """Test the Polish analyzer with sample text."""
    url = f"http://{host}:{port}/{index_name}/_analyze"
    
    test_texts = [
        "Aplikacja działa poprawnie",
        "Błąd w systemie zostanie naprawiony",
        "Zadanie wykonane przez programistę"
    ]
    
    print(f"\nTesting Polish analyzer on index {index_name}:")
    
    # Try to test the stempel analyzer first
    for text in test_texts:
        try:
            payload = {
                "analyzer": "polish_stempel",
                "text": text
            }
            
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                tokens = response.json()
                analyzed_tokens = [token["token"] for token in tokens.get("tokens", [])]
                print(f"  '{text}' → {analyzed_tokens}")
            else:
                # Fall back to basic analyzer if stempel fails
                payload = {
                    "analyzer": "polish_basic",
                    "text": text
                }
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    tokens = response.json()
                    analyzed_tokens = [token["token"] for token in tokens.get("tokens", [])]
                    print(f"  '{text}' → {analyzed_tokens} (basic)")
                else:
                    print(f"  Error analyzing '{text}': {response.status_code}")
                
        except Exception as e:
            print(f"  Error testing text '{text}': {e}")

def main():
    """Main function to initialize Elasticsearch with Polish support."""
    # Get Elasticsearch configuration
    es_config = config.get_elasticsearch_config()
    host = es_config.get('host', 'localhost')
    port = es_config.get('port', 9200)
    
    print("Initializing Elasticsearch with Polish language support...")
    print(f"Target: {host}:{port}")
    
    # Wait for Elasticsearch to be ready
    if not wait_for_elasticsearch(host, port):
        print("Failed to connect to Elasticsearch")
        return 1
    
    # Check plugins
    if not install_plugins(host, port):
        print("Warning: Some required plugins may be missing")
      # Create changelog index
    print(f"\nCreating index: {config.INDEX_CHANGELOG}")
    if not create_index_with_fallback(host, port, config.INDEX_CHANGELOG):
        print("Failed to create changelog index")
        return 1
    
    # Create settings index
    print(f"\nCreating index: {config.INDEX_SETTINGS}")
    if not create_index_with_fallback(host, port, config.INDEX_SETTINGS):
        print("Failed to create settings index")
        return 1
    
    # Test Polish analyzer
    test_polish_analyzer(host, port, config.INDEX_CHANGELOG)
    
    print(f"\n✓ Elasticsearch initialization completed!")
    print(f"Access Kibana at: http://localhost:5601")
    print(f"Access Elasticsearch at: http://{host}:{port}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
