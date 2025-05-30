#!/usr/bin/env python3
"""
Test script to check if the stempel plugin is working correctly.
"""

import requests
import json

def test_stempel_plugin(host="localhost", port=9200):
    """Test if the stempel plugin is working."""
    
    # First, let's test a simple index with just the stempel analyzer
    test_mapping = {
        "settings": {
            "analysis": {
                "analyzer": {
                    "simple_stempel": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "stempel"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "text": {"type": "text", "analyzer": "simple_stempel"}
            }
        }
    }
    
    index_name = "test-stempel"
    url = f"http://{host}:{port}/{index_name}"
    
    try:
        # Delete test index if exists
        requests.delete(url, timeout=5)
        
        # Create test index
        headers = {"Content-Type": "application/json"}
        response = requests.put(url, json=test_mapping, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✓ Test index with stempel analyzer created successfully")
            
            # Test the analyzer
            analyze_url = f"{url}/_analyze"
            test_text = "programowanie aplikacji"
            
            payload = {
                "analyzer": "simple_stempel",
                "text": test_text
            }
            
            analyze_response = requests.post(analyze_url, json=payload, timeout=5)
            
            if analyze_response.status_code == 200:
                tokens = analyze_response.json()
                analyzed_tokens = [token["token"] for token in tokens.get("tokens", [])]
                print(f"✓ Stempel analyzer working: '{test_text}' → {analyzed_tokens}")
                
                # Clean up
                requests.delete(url, timeout=5)
                return True
            else:
                print(f"✗ Stempel analyzer test failed: {analyze_response.status_code}")
                print(f"Response: {analyze_response.text}")
        else:
            print(f"✗ Failed to create test index: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Error testing stempel plugin: {e}")
    
    # Clean up
    try:
        requests.delete(url, timeout=5)
    except:
        pass
    
    return False

if __name__ == "__main__":
    print("Testing stempel plugin functionality...")
    if test_stempel_plugin():
        print("✓ Stempel plugin is working correctly!")
    else:
        print("✗ Stempel plugin test failed!")
