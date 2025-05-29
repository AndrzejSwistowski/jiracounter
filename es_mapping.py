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
                    "created_at": {"type": "date"}
                }
            },
            "allocation": {"type": "keyword"},
            "statusName": {"type": "keyword"},
            "issueId": {"type": "keyword"},
            "issueKey": {"type": "keyword"},
            "typeName": {"type": "keyword"},            
            "assigneeDisplayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "reporterDisplayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "allocationCode": {"type": "keyword"},
            "projectKey": {"type": "keyword"},
            "projectName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "parentKey": {"type": "keyword"},            "authorDisplayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "labels": {"type": "keyword"}, 
            "components": {"type": "keyword"}, 
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
            },              "parent_issue": {
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
            "author": {
                "properties": {
                    "displayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                }
            },
            "reporter": {
                "properties": {
                    "displayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                }
            },
            "minutes_since_creation": {"type": "float"},
            "todo_exit_date": {"type": "date"},
            "changes": {
                "type": "nested",
                "properties": {
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
            "backlog_minutes": {"type": "float"},
            "processing_minutes": {"type": "float"},  
            "waiting_minutes": {"type": "float"},
            
            # Status transition metrics
            "previous_status": {"type": "keyword"},
            "total_transitions": {"type": "integer"},
            "backflow_count": {"type": "integer"},
            "unique_statuses_visited": {"type": "keyword"},
            "current_status_minutes": {"type": "float"},
            "status_transitions": {
                "type": "nested",
                "properties": {
                    "from_status": {"type": "keyword"},
                    "to_status": {"type": "keyword"},
                    "transition_date": {"type": "date"},
                    "minutes_in_previous_status": {"type": "float"},
                    "is_forward_transition": {"type": "boolean"},
                    "is_backflow": {"type": "boolean"}
                }
            },
            
            # Working time metrics
            "working_minutes_from_create": {"type": "float"},
            "working_minutes_in_status": {"type": "float"},
            "working_minutes_from_move_at_point": {"type": "float"},
            "status_change_date": {"type": "date"},
            "created": {"type": "date"},            "updated": {"type": "date"},

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
