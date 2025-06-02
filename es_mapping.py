"""
Elasticsearch mappings for JIRA data.
"""

# Changelog index mapping with improved handling of the changes field
CHANGELOG_MAPPING = {    "settings": {
        "analysis": {
            "normalizer": {
                "lowercase": {
                    "type": "custom",
                    "filter": ["lowercase"]
                }
            },
            "analyzer": {
                # Polish analyzer removed temporarily until proper support is added
                "case_insensitive": {
                    "tokenizer": "keyword",
                    "filter": ["lowercase"]
                }
            }
        }
    },    "mappings": {
        "properties": {
            "@timestamp": {"type": "date"},  # Will use issue_data.updated
            "issue": {
                "properties": {
                  "id": {"type": "keyword"},
                  "key": {"type": "keyword"},                  "type": { 
                      "properties": {
                          "name": {"type": "keyword"},
                          "name_lower": {"type": "keyword", "normalizer": "lowercase"}
                      }
                  },                  "status": {
                      "properties": {
                          "name": {"type": "keyword"},
                          "name_lower": {"type": "keyword", "normalizer": "lowercase"},
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
            "author": {
              "properties": {
                  "displayName": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                }
            },            
            "todo_exit_at": {"type": "alias", "path": "selected_for_development_at"},
            # Content fields with comprehensive text analysis for searching
            "description": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 32766},
                    "english": {"type": "text", "analyzer": "english"}
                    # Polish field removed temporarily
                }            },            "comment": {
                "type": "text",  # Used for backward compatibility
                "analyzer": "standard",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 32766},
                    "english": {"type": "text", "analyzer": "english"}
                }
            },
            "comments": {
                "type": "nested",  # Nested array of comment objects
                "properties": {
                    "body": {"type": "text", "analyzer": "standard"},
                    "author": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "created_at": {"type": "date"}
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
            }},            "total_transitions": {"type": "integer"},
            "backflow_count": {"type": "integer"},
            "unique_statuses_visited": {"type": "keyword"},            "unique_statuses_visited_lower": {"type": "keyword", "normalizer": "lowercase"},
            "status_transitions": {
                "type": "nested",
                "properties": {
                    "from_status": {"type": "keyword"},
                    "from_status_lower": {"type": "keyword", "normalizer": "lowercase"},
                    "to_status": {"type": "keyword"},
                    "to_status_lower": {"type": "keyword", "normalizer": "lowercase"},
                    "transition_date": {"type": "date"},
                    "minutes_in_previous_status": {"type": "integer"},
                    "days_in_previous_status": {"type": "integer"},
                    "period_in_previous_status": {"type": "text"},
                    "is_forward_transition": {"type": "boolean"},
                    "is_backflow": {"type": "boolean"},
                    "author": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                }
            },            "field_changes": {
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
