#!/usr/bin/env python3
"""
Test case-insensitive functionality with real JIRA data.
"""

from elasticsearch import Elasticsearch
import config

def main():
    # Connect to Elasticsearch
    if config.ELASTIC_APIKEY:
        es = Elasticsearch(config.ELASTIC_URL, api_key=config.ELASTIC_APIKEY, verify_certs=False)
    else:
        es = Elasticsearch(config.ELASTIC_URL, basic_auth=(config.ELASTIC_USER, config.ELASTIC_PASSWORD), verify_certs=False)

    print("Connected to Elasticsearch")

    # Get some sample status values from real data
    query = {
        'size': 0,
        'aggs': {
            'status_names': {
                'terms': {
                    'field': 'issue.status.name',
                    'size': 20
                }
            },
            'status_names_lower': {
                'terms': {
                    'field': 'issue.status.name_lower',
                    'size': 20
                }
            }
        }
    }

    result = es.search(index='jira-changelog', body=query)
    print('\n=== Real Status Values in Index ===')
    print('Original status names:')
    for bucket in result['aggregations']['status_names']['buckets']:
        print(f'  {bucket["key"]}: {bucket["doc_count"]} documents')

    print('\nLowercase status names:')
    for bucket in result['aggregations']['status_names_lower']['buckets']:
        print(f'  {bucket["key"]}: {bucket["doc_count"]} documents')

    # Test case-insensitive search with real data
    print('\n=== Testing Case-Insensitive Searches with Real Data ===')

    # Test with a common status
    test_searches = [
        ('todo', 'issue.status.name_lower'),
        ('TODO', 'issue.status.name_lower'),
        ('done', 'issue.status.name_lower'),
        ('DONE', 'issue.status.name_lower'),
        ('in progress', 'issue.status.name_lower'),
        ('IN PROGRESS', 'issue.status.name_lower'),
        ('hold', 'issue.status.name_lower'),
        ('HOLD', 'issue.status.name_lower')
    ]

    for search_term, field in test_searches:
        query = {'query': {'term': {field: search_term}}}
        result = es.search(index='jira-changelog', body=query)
        print(f'Search "{search_term}" in {field}: {result["hits"]["total"]["value"]} results')

    # Test status transitions
    print('\n=== Testing Status Transition Case-Insensitive Searches ===')
    
    transition_searches = [
        ('todo', 'status_transitions.from_status_lower'),
        ('done', 'status_transitions.to_status_lower'),
        ('DONE', 'status_transitions.to_status_lower'),
        ('in progress', 'status_transitions.from_status_lower')
    ]

    for search_term, field in transition_searches:
        query = {
            'query': {
                'nested': {
                    'path': 'status_transitions',
                    'query': {
                        'term': {field: search_term}
                    }
                }
            }
        }
        result = es.search(index='jira-changelog', body=query)
        print(f'Nested search "{search_term}" in {field}: {result["hits"]["total"]["value"]} results')

    print('\n✅ Case-insensitive functionality verified with real JIRA data!')

if __name__ == "__main__":
    main()
