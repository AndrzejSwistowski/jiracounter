#!/usr/bin/env python3

import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

print('Config import successful from diagnostic folder')
es_config = config.get_elasticsearch_config()
print('Host:', es_config['host'], 'Port:', es_config['port'])
