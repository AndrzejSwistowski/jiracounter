# filepath: e:\Zrodla\jiracounter\jiracouter\es_mapping_polish_fixed.py
"""
Elasticsearch mappings for JIRA data with Polish language support.
This mapping includes proper Polish analyzers for full-text search.
"""

# Enhanced changelog index mapping with Polish language support
CHANGELOG_MAPPING_POLISH = {
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
                },
                "polish_stemmer": {
                    "type": "stemmer",
                    "language": "minimal_polish"
                },
                "polish_keywords": {
                    "type": "keyword_marker",
                    "keywords": ["jira", "bug", "task", "story", "epic"]
                }
            },
            "analyzer": {
                "polish_standard": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "asciifolding",
                        "polish_stop"
                    ]
                },
                "polish_light": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "asciifolding", 
                        "polish_keywords",
                        "polish_stop",
                        "polish_stemmer"
                    ]
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
                "analyzer": "polish_standard",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "english": {"type": "text", "analyzer": "english"},
                    "polish": {"type": "text", "analyzer": "polish_light"},
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
                        "analyzer": "polish_standard",
                        "fields": {
                            "keyword": {"type": "keyword"},
                            "polish": {"type": "text", "analyzer": "polish_light"}
                        }
                    }
                }
            },
            "epic_issue": {
                "properties": {
                    "key": {"type": "keyword"},
                    "summary": {
                        "type": "text", 
                        "analyzer": "polish_standard",
                        "fields": {
                            "keyword": {"type": "keyword"},
                            "polish": {"type": "text", "analyzer": "polish_light"}
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
            },
            "todo_exit_at": {"type": "alias", "path": "selected_for_development_at"},
            "changes": {
                "type": "nested",
                "properties": {
                    "field": {"type": "keyword"},
                    "to": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
                }
            },
            # Content fields with comprehensive text analysis for Polish searching
            "description": {
                "type": "text",
                "analyzer": "polish_standard",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 32766},
                    "english": {"type": "text", "analyzer": "english"},
                    "polish": {"type": "text", "analyzer": "polish_light"},
                    "standard": {"type": "text", "analyzer": "standard"}
                }
            },
            "comment": {
                "type": "text", 
                "analyzer": "polish_standard",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 32766},
                    "english": {"type": "text", "analyzer": "english"},
                    "polish": {"type": "text", "analyzer": "polish_light"},
                    "standard": {"type": "text", "analyzer": "standard"}
                }
            },
            "selected_for_development_at": {"type": "date"},
            "backlog": {
                "properties": {
                    "working_minutes": {"type": "integer"},
                    "working_days": {"type": "integer"},
                    "period": {"type": "text"}
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
            },
            "from_selected_for_development": {
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
                "properties": {
                    "from_status": {"type": "keyword"},
                    "to_status": {"type": "keyword"},
                    "transition_date": {"type": "date"},
                    "minutes_in_previous_status": {"type": "integer"},
                    "is_forward_transition": {"type": "boolean"},
                    "is_backflow": {"type": "boolean"}
                }
            }
        }
    }
}

# Settings index mapping (unchanged)
SETTINGS_MAPPING_POLISH = {
    "mappings": {
        "properties": {
            "setting_key": {"type": "keyword"},
            "setting_value": {"type": "text"},
            "updated_at": {"type": "date"}
        }
    }
}
