import elasticsearch
from elasticsearch import Elasticsearch
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Connect to Elasticsearch
    try:
        es = Elasticsearch("http://localhost:9200")
        info = es.info()
        logger.info(f"Connected to Elasticsearch successfully: {info['version']['number']}")
    except Exception as e:
        logger.error(f"Failed to connect to Elasticsearch: {str(e)}")
        return
    
    # Testing different search queries on the comments field
    test_queries = [
        {
            "name": "Basic search for Polish characters in comments",
            "query": {
                "nested": {
                    "path": "comments",
                    "query": {
                        "match": {
                            "comments.body": "ąęćłń"
                        }
                    }
                }
            }
        },
        {
            "name": "Search for specific comment by author",
            "query": {
                "nested": {
                    "path": "comments",
                    "query": {
                        "bool": {
                            "must": [
                                {"match": {"comments.author": "test_user3"}},
                                {"match": {"comments.body": "Polish"}}
                            ]
                        }
                    }
                }
            }
        },
        {
            "name": "Search for comments with multi-word phrase",
            "query": {
                "nested": {
                    "path": "comments",
                    "query": {
                        "match_phrase": {
                            "comments.body": "longer comment with some specific"
                        }
                    }
                }
            }
        },
        {
            "name": "Combined search with issue fields and comments",
            "query": {
                "bool": {
                    "must": [
                        {"match": {"issue_type": "Task"}},
                        {
                            "nested": {
                                "path": "comments",
                                "query": {
                                    "match": {
                                        "comments.body": "reply"
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }
    ]
    
    # Run each test query
    for test in test_queries:
        try:
            logger.info(f"\nExecuting test: {test['name']}")
            response = es.search(index="jira-changelog", query=test["query"])
            
            if response["hits"]["total"]["value"] > 0:
                logger.info(f"Found {response['hits']['total']['value']} matching documents")
                
                for hit in response["hits"]["hits"]:
                    logger.info(f"Issue key: {hit['_source']['issue_key']}")
                    
                    # Extract matched comments if available in inner_hits
                    if "inner_hits" in hit:
                        for comment_hit in hit["inner_hits"]["comments"]["hits"]["hits"]:
                            comment = comment_hit["_source"]
                            logger.info(f"Matched comment: {comment['body'][:50]}... by {comment['author']}")
            else:
                logger.warning(f"No matches found for test: {test['name']}")
                
        except Exception as e:
            logger.error(f"Error executing test '{test['name']}': {str(e)}")
    
    logger.info("\nRetrieving a sample document with all comments:")
    try:
        response = es.search(
            index="jira-changelog", 
            query={"match": {"issue_key": "TEST-123"}},
            _source_includes=["issue_key", "comments"]
        )
        
        if response["hits"]["total"]["value"] > 0:
            doc = response["hits"]["hits"][0]["_source"]
            logger.info(f"Document: {doc['issue_key']}")
            
            if "comments" in doc:
                logger.info(f"Found {len(doc['comments'])} comments")
                for i, comment in enumerate(doc["comments"]):
                    logger.info(f"Comment {i+1}: {comment['body'][:50]}...")
                    logger.info(f"  Author: {comment['author']}")
                    logger.info(f"  Created: {comment['created_at']}")
            else:
                logger.warning("No comments found in document")
                
    except Exception as e:
        logger.error(f"Error retrieving sample document: {str(e)}")

if __name__ == "__main__":
    main()
