"""
Elasticsearch mappings for JIRA data.
"""

# Changelog index mapping with improved handling of the changes field
CHANGELOG_MAPPING = {
    "settings": {
        "analysis": {
            "analyzer": {
                # Polish analyzer removed temporarily until proper support is added
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
                            "change_date": {"type": "date"},
                            "working_minutes": {"type": "integer"},
                            "working_days": {"type": "integer"},    
                            "period": {"type": "text"}
                        }
                    },
                    "created_at": {"type": "date"}
                }
            },
            "allocation": {"type": "keyword"},
            "labels": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "components": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "summary": {
                "type": "text", 
                "analyzer": "standard",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "english": {"type": "text", "analyzer": "english"}
                    # Polish field removed temporarily
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
                    "summary": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                }
            },
            "epic_issue": {
                "properties": {
                    "key": {"type": "keyword"},
                    "summary": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
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
            "days_since_creation": {"type": "float"},
            "todo_exit_date": {"type": "alias", "path": "selected_for_development_date"},
            "changes": {
                "type": "nested",
                "properties": {
                    "author": {
                        "properties": {
                            "displayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                            }
                    },
                    "field": {"type": "keyword"},
                    "to": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                }
            },
            # Content fields with comprehensive text analysis for searching
            "description_text": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 32766},
                    "english": {"type": "text", "analyzer": "english"}
                    # Polish field removed temporarily
                }
            },
            "comment_text": {
                "type": "text", 
                "analyzer": "standard",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 32766},
                    "english": {"type": "text", "analyzer": "english"}
                    # Polish field removed temporarily
                }
            },
            "selected_for_development_date": {"type": "date"},
            "backlog": {
                "type": "nested",
                "properties": {
                    "working_minutes": {"type": "integer"},
                    "working_days": {"type": "integer"},
                    "period": {"type": "text"},
                }
            },
            "processing": {"type": "nested", "properties": {
                "working_minutes": {"type": "integer"},
                "working_days": {"type": "integer"},
                "period": {"type": "text"}
           }},
            "waiting": {"type": "nested", "properties": {
                "working_minutes": {"type": "integer"},
                "working_days": {"type": "integer"},
                "period": {"type": "text"}
            }},
            "from_selected_for_development": {"type": "nested", "properties": {
                "working_minutes": {"type": "integer"},
                "working_days": {"type": "integer"},
                "period": {"type": "text"}
            }},
            "total_transitions": {"type": "integer"},
            "backflow_count": {"type": "integer"},
            "unique_statuses_visited": {"type": "keyword"},
            "status_transitions": {
                "type": "nested",
                "properties": {
                    "from_status": {"type": "keyword"},
                    "to_status": {"type": "keyword"},
                    "transition_date": {"type": "date"},
                    "minutes_in_previous_status": {"type": "integer"},
                    "is_forward_transition": {"type": "boolean"},
                    "is_backflow": {"type": "boolean"}
                }
            },
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
