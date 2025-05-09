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
                    "from": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 8191}}},
                    "to": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 8191}}}
                }
            },
            # Fields for specific content to make them searchable
            "description_text": {
                "type": "text",
                "analyzer": "standard", 
                "index_options": "positions",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 32766}
                }
            },
            "comment_text": {
                "type": "text",
                "analyzer": "standard",
                "index_options": "positions",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 32766}
                }
            },
            "status_changes": {"type": "keyword"},
            "assignee_changes": {"type": "keyword"},
            "created": {"type": "date"},
            "updated": {"type": "date"},
            "status_change_date": {"type": "date"}
        },
        "dynamic_templates": [
            {
                "text_fields": {
                    "match_mapping_type": "string",
                    "mapping": {
                        "type": "text",
                        "index_options": "positions",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 8191
                            }
                        }
                    }
                }
            }
        ]
    }
}

# Settings index mapping
SETTINGS_MAPPING = {
    "mappings": {
        "properties": {
            "setting_key": {"type": "keyword"},
            "setting_value": {"type": "text"},
            "updated_at": {"type": "date"}
        }
    }
}
