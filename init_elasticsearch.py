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
from es_utils import create_index_with_auto_fallback, _setup_es_connection
from es_populate import JiraElasticsearchPopulator
import config

def wait_for_elasticsearch(host="localhost", port=9200, timeout=300, auth=None, api_key=None, use_ssl=False):
    """Wait for Elasticsearch to be ready."""
    print(f"Waiting for Elasticsearch at {host}:{port}...")
    
    # Setup connection using centralized helper
    base_url, headers = _setup_es_connection(
        host=host, port=port, api_key=api_key, use_ssl=use_ssl
    )
    
    if api_key:
        print("Using API key authentication")
    elif auth and len(auth) == 2:
        print(f"Using basic authentication with user: {auth[0]}")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Use basic auth if provided, otherwise rely on headers from helper
            auth_tuple = auth if auth and len(auth) == 2 else None
            response = requests.get(
                f"{base_url}/_cluster/health", 
                headers=headers,
                auth=auth_tuple,
                timeout=5,
                verify=False  # Disable SSL verification for development
            )
            if response.status_code == 200:
                health = response.json()
                print(f"Elasticsearch is ready! Cluster status: {health.get('status', 'unknown')}")
                return True
            elif response.status_code == 401:
                print(f"\nAuthentication failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException:
            pass
        
        print(".", end="", flush=True)
        time.sleep(2)
    
    print(f"\nTimeout waiting for Elasticsearch after {timeout} seconds")
    return False

def install_plugins(host="localhost", port=9200, auth=None, api_key=None, use_ssl=False):
    """Check if required plugins are installed."""
    try:
        # Setup connection using centralized helper
        base_url, headers = _setup_es_connection(
            host=host, port=port, api_key=api_key, use_ssl=use_ssl
        )
        
        # Use basic auth if provided, otherwise rely on headers from helper
        auth_tuple = auth if auth and len(auth) == 2 else None
            
        response = requests.get(
            f"{base_url}/_nodes/plugins", 
            headers=headers,
            auth=auth_tuple,
            timeout=10,
            verify=False
        )
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
        else:
            print(f"Error checking plugins: {response.status_code} - {response.text}")
            return False
                
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

def create_index_unified(populator, index_name):
    """Create an index using the unified approach from es_utils."""
    try:
        success = create_index_with_auto_fallback(
            populator=populator,
            index_name=index_name,
            logger=None  # Function handles its own logging
        )
        if success:
            print(f"✓ Index {index_name} created successfully with unified approach")
        else:
            print(f"✗ Failed to create index {index_name}")
        return success
    except Exception as e:
        print(f"✗ Error creating index {index_name}: {e}")
        return False

def test_polish_analyzer(host, port, index_name, auth=None, api_key=None, use_ssl=False):
    """Test the Polish analyzer with sample text."""
    # Setup connection using centralized helper
    base_url, headers = _setup_es_connection(
        host=host, port=port, api_key=api_key, use_ssl=use_ssl
    )
    url = f"{base_url}/{index_name}/_analyze"
    
    # Use basic auth if provided, otherwise rely on headers from helper
    auth_tuple = auth if auth and len(auth) == 2 else None
    
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
            
            response = requests.post(
                url, 
                json=payload, 
                headers=headers,
                auth=auth_tuple,
                timeout=10,
                verify=False
            )
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
                response = requests.post(
                    url, 
                    json=payload, 
                    headers=headers,
                    auth=auth_tuple,
                    timeout=10,
                    verify=False
                )
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
    api_key = es_config.get('api_key')
    use_ssl = es_config.get('use_ssl', False)
    username = es_config.get('username')
    password = es_config.get('password')
    
    # Set up authentication
    auth = None
    if username and password:
        auth = (username, password)
        print(f"Found Elasticsearch credentials for user: {username}")
    
    print("Initializing Elasticsearch with Polish language support...")
    protocol = "https" if use_ssl else "http"
    print(f"Target: {protocol}://{host}:{port}")
    
    if auth:
        print(f"Authentication: Basic auth with user '{auth[0]}'")
    elif api_key:
        print("Authentication: API Key")
    else:
        print("Authentication: None (assuming no authentication required)")
    
    # Wait for Elasticsearch to be ready
    if not wait_for_elasticsearch(host, port, auth=auth, api_key=api_key, use_ssl=use_ssl):
        print("Failed to connect to Elasticsearch")
        return 1
    
    # Check plugins
    if not install_plugins(host, port, auth=auth, api_key=api_key, use_ssl=use_ssl):
        print("Warning: Some required plugins may be missing")
    
    # Create populator for unified approach
    populator = JiraElasticsearchPopulator(
        agent_name="InitElasticsearch",
        host=host,
        port=port,
        api_key=api_key,
        use_ssl=use_ssl,
        url=es_config.get('url')
    )
    
    try:
        populator.connect()
        
        # Create changelog index
        print(f"\nCreating index: {config.INDEX_CHANGELOG}")
        if not create_index_unified(populator, config.INDEX_CHANGELOG):
            print("Failed to create changelog index")
            return 1
        
        # Create settings index
        print(f"\nCreating index: {config.INDEX_SETTINGS}")
        if not create_index_unified(populator, config.INDEX_SETTINGS):
            print("Failed to create settings index")
            return 1
        
        # Test Polish analyzer
        test_polish_analyzer(host, port, config.INDEX_CHANGELOG, auth=auth, api_key=api_key, use_ssl=use_ssl)
        
    finally:
        populator.close()
    
    print(f"\n✓ Elasticsearch initialization completed!")
    
    # Get Kibana configuration
    kibana_config = config.get_kibana_config()
    kibana_protocol = 'https' if kibana_config['use_ssl'] else 'http'
    kibana_url = kibana_config['url'] or f"{kibana_protocol}://{kibana_config['host']}:{kibana_config['port']}"
    
    print(f"Access Kibana at: {kibana_url}")
    print(f"Access Elasticsearch at: {protocol}://{host}:{port}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
