"""
Elasticsearch mappings for JIRA data.
"""

# Changelog index mapping with improved handling of the changes field
CHANGELOG_MAPPING = {
    "mappings": {
        "properties": {
            "historyId": {"type": "keyword"},
            "historyDate": {"type": "date"},
            "@timestamp": {"type": "date"},
            "factType": {"type": "integer"},
            "issue": {
                "properties": {
                    "id": {"type": "keyword"},
                    "key": {"type": "keyword"},
                    "type": {
                        "properties": {
                            "name": {"type": "keyword"}
                        }
                    },
                    "status": {
                        "properties": {
                            "name": {"type": "keyword"}
                        }
                    }
                }
            },
            "project": {
                "properties": {
                    "key": {"type": "keyword"},
                    "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                }
            },
            "author": {
                "properties": {
                    "username": {"type": "keyword"},
                    "displayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                }
            },
            "reporter": {
                "properties": {
                    "username": {"type": "keyword"},
                    "displayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                }
            },
            "summary": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "workingDaysFromCreation": {"type": "float"},
            "changes": {
                "type": "nested",
                "properties": {
                    "field": {"type": "keyword"},
                    "from": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "to": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                }
            },
            # Add specific fields for common changes to make them easily searchable
            "description_text": {"type": "text"},  # Extracted description text
            "comment_text": {"type": "text"},      # Extracted comment text
            "status_change": {"type": "keyword"},  # Status transitions
            "assignee_change": {"type": "keyword"} # Assignee changes
        }
    }
}

# Settings index mapping (same as original)
SETTINGS_MAPPING = {
    "mappings": {
        "properties": {
            "setting_key": {"type": "keyword"},
            "setting_value": {"type": "text"},
            "updated_at": {"type": "date"}
        }
    }
}
```
