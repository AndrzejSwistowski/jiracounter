"""
Simplified Elasticsearch mappings for JIRA data with basic Polish language support.
This mapping uses only built-in analyzers to ensure compatibility.
"""

# Simple changelog index mapping with basic Polish support
CHANGELOG_MAPPING_SIMPLE = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "filter": {
                "polish_stop": {
                    "type": "stop",
                    "stopwords": [
                        "a", "aby", "albo", "ale", "am", "an", "and", "any", "are", "as", "at",
                        "be", "been", "będzie", "by", "być", "czy", "dla", "do", "from", "go", "have",
                        "i", "in", "is", "it", "jak", "jako", "je", "jego", "jej", "lub", "ma", "może",
                        "na", "nie", "of", "or", "po", "się", "są", "te", "that", "the", "to", "w", "we",
                        "with", "z", "za", "ze"
                    ]
                }
            },
            "analyzer": {
                "polish_basic": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "polish_stop"
                    ]
                }
            }
        }
    },    "mappings": {
        "properties": {
            "_id": {"type": "keyword"},  # Will use issue_data.issueId
            "@timestamp": {"type": "date"},  # Will use issue_data.updated
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
                            "name": {"type": "keyword"},
                            "change_at": {"type": "date"},
                            "working_minutes": {"type": "integer"},
                            "working_days": {"type": "integer"},    
                            "period": {"type": "text"}
                        }
                    },
                    "created_at": {"type": "date"},
                    "working_minutes": {"type": "integer"},
                    "working_days": {"type": "integer"},
                    "period": {"type": "text"}    
                }
            },
            "allocation": {"type": "keyword"},
            "labels": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "components": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "summary": {
                "type": "text", 
                "analyzer": "polish_basic",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "english": {"type": "text", "analyzer": "english"},
                    "standard": {"type": "text", "analyzer": "standard"}
                }
            },
            "project": {
                "properties": {
                    "key": {"type": "keyword"}
                }
            },
            "parent_issue": {
                "properties": {
                    "key": {"type": "keyword"},
                    "summary": {
                        "type": "text", 
                        "analyzer": "polish_basic",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    }
                }
            },
            "epic_issue": {
                "properties": {
                    "key": {"type": "keyword"},
                    "summary": {
                        "type": "text", 
                        "analyzer": "polish_basic",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    }
                }
            },
            "reporter": {
                "properties": {
                    "displayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                }
            },
            "assignee": {
                "properties": {
                    "displayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                }
            },
            "author": {
                "properties": {
                    "displayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                }
            },            "todo_exit_at": {"type": "alias", "path": "selected_for_development_at"},
            # Content fields with basic Polish text analysis
            "description": {
                "type": "text",
                "analyzer": "polish_basic",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 32766},
                    "english": {"type": "text", "analyzer": "english"},
                    "standard": {"type": "text", "analyzer": "standard"}
                }            },            "comment": {
                "type": "text",  # Changed from nested to simple text for concatenated comments
                "analyzer": "polish_basic",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 32766},
                    "english": {"type": "text", "analyzer": "english"},
                    "standard": {"type": "text", "analyzer": "standard"}
                }
            },
            "selected_for_development_at": {"type": "date"},
            "backlog": {
                "properties": {
                    "working_minutes": {"type": "integer"},
                    "working_days": {"type": "integer"},
                    "period": {"type": "text"},
                }
            },
            "processing": {
                "properties": {
                    "working_minutes": {"type": "integer"},
                    "working_days": {"type": "integer"},
                    "period": {"type": "text"}
                }
            },
            "waiting": {
                "properties": {
                    "working_minutes": {"type": "integer"},
                    "working_days": {"type": "integer"},
                    "period": {"type": "text"}
                }
            },            "from_selected_for_development": {
                "properties": {
                    "working_minutes": {"type": "integer"},
                    "working_days": {"type": "integer"},
                    "period": {"type": "text"}
                }
            },
            "total_transitions": {"type": "integer"},
            "backflow_count": {"type": "integer"},
            "unique_statuses_visited": {"type": "keyword"},
            "status_transitions": {
                "type": "nested",  # Keep as nested for multiple transitions                "properties": {
                    "from_status": {"type": "keyword"},
                    "to_status": {"type": "keyword"},
                    "transition_date": {"type": "date"},
                    "minutes_in_previous_status": {"type": "integer"},
                    "days_in_previous_status": {"type": "integer"},
                    "period_in_previous_status": {"type": "text"},
                    "is_forward_transition": {"type": "boolean"},
                    "is_backflow": {"type": "boolean"},
                    "author": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                }
            },
            "field_changes": {
                "type": "nested",  # New field for non-status changes
                "properties": {
                    "change_date": {"type": "date"},
                    "author": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "changes": {
                        "type": "nested",
                        "properties": {
                            "field": {"type": "keyword"},
                            "fieldtype": {"type": "keyword"},
                            "from": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                            "to": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                        }
                    }
                }
            }
        }
    }

# Settings index mapping (unchanged)
SETTINGS_MAPPING_SIMPLE = {
    "mappings": {
        "properties": {
            "setting_key": {"type": "keyword"},
            "setting_value": {"type": "text"},
            "updated_at": {"type": "date"}
        }
    }
}
