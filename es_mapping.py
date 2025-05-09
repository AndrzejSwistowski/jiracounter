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
                    "key": {"type": "keyword"},
                    "type ": { "properties": {										
												"name": {"type": "keyword"}
										}},
                    "status": {
                        "properties": {
                            "name": {"type": "keyword"},
                            "change_date": {"type": "date"}
                        }
                    },
										"created_at": {"type": "date"},
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
						"labels": {"type": "keyword"}, 
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
            "days_since_creation": {"type": "float"},
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
