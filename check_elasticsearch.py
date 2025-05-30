#!/usr/bin/env python3
"""
Quick script to check if Elasticsearch is running and plugins are installed.
"""

import requests
import json
import sys

def check_elasticsearch(host="localhost", port=9200):
    """Check if Elasticsearch is running and what plugins are installed."""
    try:
        # Check cluster health
        health_response = requests.get(f"http://{host}:{port}/_cluster/health", timeout=5)
        if health_response.status_code == 200:
            health = health_response.json()
            print(f"✓ Elasticsearch is running")
            print(f"  Cluster: {health.get('cluster_name')}")
            print(f"  Status: {health.get('status')}")
            print(f"  Nodes: {health.get('number_of_nodes')}")
        else:
            print(f"✗ Elasticsearch health check failed: {health_response.status_code}")
            return False

        # Check installed plugins
        plugins_response = requests.get(f"http://{host}:{port}/_nodes/plugins", timeout=5)
        if plugins_response.status_code == 200:
            plugins_data = plugins_response.json()
            print(f"\n✓ Installed plugins:")
            
            for node_id, node_data in plugins_data.get("nodes", {}).items():
                node_name = node_data.get("name", node_id)
                print(f"  Node: {node_name}")
                
                plugins = node_data.get("plugins", [])
                if plugins:
                    for plugin in plugins:
                        print(f"    - {plugin.get('name')} ({plugin.get('version')})")
                else:
                    print(f"    - No plugins installed")
            
            # Check for required plugins
            required_plugins = ["analysis-stempel", "analysis-icu"]
            installed_plugin_names = []
            
            for node_data in plugins_data.get("nodes", {}).values():
                for plugin in node_data.get("plugins", []):
                    installed_plugin_names.append(plugin.get("name"))
            
            missing_plugins = [p for p in required_plugins if p not in installed_plugin_names]
            
            if missing_plugins:
                print(f"\n⚠ Missing required plugins: {missing_plugins}")
                return False
            else:
                print(f"\n✓ All required plugins are installed!")
                return True
        else:
            print(f"✗ Failed to check plugins: {plugins_response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to connect to Elasticsearch: {e}")
        return False

def main():
    """Main function."""
    print("Checking Elasticsearch status and plugins...")
    
    if check_elasticsearch():
        print(f"\n✓ Elasticsearch is ready for Polish full-text search!")
        return 0
    else:
        print(f"\n✗ Elasticsearch is not ready or missing required plugins")
        return 1

if __name__ == "__main__":
    sys.exit(main())
