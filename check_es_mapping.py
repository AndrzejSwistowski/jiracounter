"""
Simple script to check Elasticsearch index mappings.
"""
import json
import logging
from elasticsearch import Elasticsearch
import config

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Check Elasticsearch index mappings."""
    # Connect to Elasticsearch
    try:
        if config.ELASTIC_APIKEY:
            es = Elasticsearch(
                config.ELASTIC_URL,
                api_key=config.ELASTIC_APIKEY,
                verify_certs=False
            )
        else:
            es = Elasticsearch(
                config.ELASTIC_URL,
                basic_auth=(config.ELASTIC_USER, config.ELASTIC_PASSWORD),
                verify_certs=False
            )
        logger.info("Connected to Elasticsearch successfully")
        
        try:
            # Get mappings for jira-changelog index
            mappings = es.indices.get_mapping(index="jira-changelog")
            
            # Pretty print the mappings for readable output
            print("\n=== Mapping for jira-changelog index ===")
            print(json.dumps(mappings["jira-changelog"]["mappings"]["properties"].get("comments", {}), indent=2))
            
            # Get a sample document to check comments structure
            search_result = es.search(
                index="jira-changelog",
                body={
                    "query": {"match_all": {}},
                    "_source": ["issue.key", "comments"],
                    "size": 1
                }
            )
            
            # Check if we have results
            if search_result["hits"]["total"]["value"] > 0:
                print("\n=== Sample document with comments ===")
                doc = search_result["hits"]["hits"][0]["_source"]
                print(f"Issue Key: {doc.get('issue', {}).get('key', 'N/A')}")
                print("Comments:")
                comments = doc.get("comments", [])
                if comments:
                    print(json.dumps(comments, indent=2))
                else:
                    print("No comments found in this document")
            else:
                print("\nNo documents found in the index")
        except Exception as e:
            logger.error(f"Error retrieving data from Elasticsearch: {str(e)}")
    except Exception as e:
        logger.error(f"Error connecting to Elasticsearch: {str(e)}")

if __name__ == "__main__":
    main()
