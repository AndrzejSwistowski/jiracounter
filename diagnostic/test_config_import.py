#!/usr/bin/env python3

import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

print('Config import successful from diagnostic folder')

# Test Elasticsearch configuration
es_config = config.get_elasticsearch_config()
print('Elasticsearch configuration:')
print('  Host:', es_config['host'], 'Port:', es_config['port'])
print('  URL:', es_config['url'] or 'Not set')
print('  SSL:', es_config['use_ssl'])

# Test Kibana configuration
kb_config = config.get_kibana_config()
print('Kibana configuration:')
print('  Host:', kb_config['host'], 'Port:', kb_config['port'])
print('  URL:', kb_config['url'] or 'Not set')
print('  SSL:', kb_config['use_ssl'])
print('  Username:', kb_config['username'] or 'Not set')
