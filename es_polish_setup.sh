#!/bin/bash
# Script to set up Polish language analyzer in Elasticsearch

# Color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}====== Elasticsearch Polish Language Support Setup ======${NC}"
echo "This script will check and configure Polish language support"

# Elasticsearch connection parameters (adjust as needed)
ES_HOST=${ES_HOST:-"elastic.voyager.pl"}
ES_PORT=${ES_PORT:-"9200"}
ES_URL="http://${ES_HOST}:${ES_PORT}"
ES_AUTH="" # Add -u username:password if needed

# Function to check if Elasticsearch is running
check_elasticsearch() {
  echo -e "\n${YELLOW}Checking Elasticsearch connection...${NC}"
  
  if curl -s "${ES_URL}" > /dev/null; then
    echo -e "${GREEN}✓ Connected to Elasticsearch at ${ES_URL}${NC}"
    return 0
  else
    echo -e "${RED}✗ Cannot connect to Elasticsearch at ${ES_URL}${NC}"
    echo "Please check if Elasticsearch is running and the connection details are correct."
    return 1
  fi
}

# Function to check if the Polish plugin is installed
check_polish_plugin() {
  echo -e "\n${YELLOW}Checking for Polish language plugins...${NC}"
  
  PLUGINS=$(curl -s "${ES_URL}/_cat/plugins")
  
  if echo "$PLUGINS" | grep -q "analysis-stempel"; then
    echo -e "${GREEN}✓ Polish Stempel analyzer plugin found${NC}"
    return 0
  else
    echo -e "${YELLOW}! Polish Stempel analyzer plugin not found${NC}"
    echo "Consider installing the plugin with: elasticsearch-plugin install analysis-stempel"
    return 1
  fi
}

# Function to test creating a simplified Polish analyzer
test_polish_analyzer() {
  echo -e "\n${YELLOW}Testing simplified Polish analyzer configuration...${NC}"
  
  # Define a test index with simplified Polish analyzer
  TEST_INDEX_NAME="test_polish_analyzer"
  
  # Delete test index if it exists
  curl -s -X DELETE "${ES_URL}/${TEST_INDEX_NAME}" > /dev/null
  
  # Create test index with simplified Polish analyzer
  echo "Creating test index with Polish analyzer..."
  CREATE_RESPONSE=$(curl -s -X PUT "${ES_URL}/${TEST_INDEX_NAME}" -H 'Content-Type: application/json' -d '{
    "settings": {
      "analysis": {
        "analyzer": {
          "polish": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": ["lowercase", "polish_stop"]
          }
        },
        "filter": {
          "polish_stop": {
            "type": "stop",
            "stopwords": "_polish_"
          }
        }
      }
    },
    "mappings": {
      "properties": {
        "text": {
          "type": "text",
          "analyzer": "polish"
        }
      }
    }
  }')
  
  if echo "$CREATE_RESPONSE" | grep -q "acknowledged\":true"; then
    echo -e "${GREEN}✓ Successfully created test index with Polish analyzer${NC}"
    
    # Test the analyzer
    echo "Testing analyzer with Polish text..."
    TEST_RESPONSE=$(curl -s -X POST "${ES_URL}/${TEST_INDEX_NAME}/_analyze" -H 'Content-Type: application/json' -d '{
      "analyzer": "polish",
      "text": "Testowy tekst w języku polskim"
    }')
    
    if echo "$TEST_RESPONSE" | grep -q "tokens"; then
      echo -e "${GREEN}✓ Polish analyzer is working!${NC}"
      echo "Sample analysis result:"
      echo "$TEST_RESPONSE" | grep -Eo '"token":"[^"]+"' | sed 's/"token":"//g' | sed 's/"//g'
      return 0
    else
      echo -e "${RED}✗ Failed to test Polish analyzer${NC}"
      echo "$TEST_RESPONSE"
      return 1
    fi
  else
    echo -e "${RED}✗ Failed to create test index${NC}"
    echo "$CREATE_RESPONSE"
    return 1
  fi
}

# Function to create the actual jira-changelog index
create_jira_changelog_index() {
  echo -e "\n${YELLOW}Creating jira-changelog index with proper mapping...${NC}"
  
  # Delete existing index
  echo "Deleting existing jira-changelog index if it exists..."
  curl -s -X DELETE "${ES_URL}/jira-changelog" > /dev/null
  
  # Create the index with the proper mapping
  echo "Creating jira-changelog index with correct mapping..."
  CREATE_RESPONSE=$(curl -s -X PUT "${ES_URL}/jira-changelog" -H 'Content-Type: application/json' -d '{
    "settings": {
      "analysis": {
        "analyzer": {
          "polish": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": ["lowercase", "polish_stop"]
          }
        },
        "filter": {
          "polish_stop": {
            "type": "stop",
            "stopwords": "_polish_"
          }
        }
      }
    },
    "mappings": {
      "properties": {
        "historyId": {"type": "keyword"},
        "historyDate": {"type": "date"},
        "@timestamp": {"type": "date"},
        "factType": {"type": "integer"},
        "issue": {
          "properties": {
            "key": {"type": "keyword"},
            "type": {
              "properties": {
                "name": {"type": "keyword"}
              }
            },
            "status": {
              "properties": {
                "name": {"type": "keyword"},
                "change_date": {"type": "date"}
              }
            },
            "created_at": {"type": "date"}
          }
        },
        "allocation": {"type": "keyword"},
        "labels": {"type": "keyword"},
        "components": {"type": "keyword"},
        "summary": {
          "type": "text",
          "analyzer": "standard",
          "fields": {
            "keyword": {"type": "keyword"},
            "polish": {"type": "text", "analyzer": "polish"}
          }
        },
        "description_text": {
          "type": "text",
          "analyzer": "standard",
          "fields": {
            "keyword": {"type": "keyword", "ignore_above": 32766},
            "english": {"type": "text", "analyzer": "english"},
            "polish": {"type": "text", "analyzer": "polish"}
          }
        },
        "comment_text": {
          "type": "text",
          "analyzer": "standard",
          "fields": {
            "keyword": {"type": "keyword", "ignore_above": 32766},
            "english": {"type": "text", "analyzer": "english"},
            "polish": {"type": "text", "analyzer": "polish"}
          }
        }
      }
    }
  }')
  
  if echo "$CREATE_RESPONSE" | grep -q "acknowledged\":true"; then
    echo -e "${GREEN}✓ Successfully created jira-changelog index!${NC}"
    return 0
  else
    echo -e "${RED}✗ Failed to create jira-changelog index${NC}"
    echo "$CREATE_RESPONSE"
    return 1
  fi
}

# Main script execution
check_elasticsearch || exit 1
check_polish_plugin
test_polish_analyzer || {
  echo -e "\n${YELLOW}Polish analyzer test failed, but we'll try creating the index anyway${NC}"
}

# Ask if user wants to create the jira-changelog index
echo -e "\n${YELLOW}Do you want to create the jira-changelog index with Polish analyzer?${NC} (y/n)"
read -r ANSWER
if [[ "$ANSWER" =~ ^[Yy]$ ]]; then
  create_jira_changelog_index
else
  echo -e "${YELLOW}Skipping jira-changelog index creation${NC}"
fi

echo -e "\n${GREEN}Script completed. See results above.${NC}"
