# Advanced Elasticsearch Queries for Throughput Analysis

## 1. Basic Done Issues Statistics
```json
GET jira-changelog/_search
{
  "query": {
    "term": {
      "issue.status.name_lower": "done"
    }
  },
  "aggs": {
    "total_done_issues": {
      "value_count": {
        "field": "issue.key.keyword"
      }
    },
    "avg_throughput_time": {
      "avg": {
        "field": "issue.working_minutes"
      }
    },
    "throughput_percentiles": {
      "percentiles": {
        "field": "issue.working_minutes",
        "percents": [50, 75, 90, 95, 99]
      }
    }
  },
  "size": 0
}
```

## 2. Throughput Time by Project
```json
GET jira-changelog/_search
{
  "query": {
    "term": {
      "issue.status.name_lower": "done"
    }
  },
  "aggs": {
    "by_project": {
      "terms": {
        "field": "project.key.keyword",
        "size": 10
      },
      "aggs": {
        "avg_throughput": {
          "avg": {
            "field": "issue.working_minutes"
          }
        },
        "median_throughput": {
          "percentiles": {
            "field": "issue.working_minutes",
            "percents": [50]
          }
        },
        "issue_count": {
          "value_count": {
            "field": "issue.key.keyword"
          }
        }
      }
    }
  },
  "size": 0
}
```

## 3. Daily Throughput Trend (Issues completed per day)
```json
GET jira-changelog/_search
{
  "query": {
    "bool": {
      "must": [
        {
          "term": {
            "issue.status.name_lower": "done"
          }
        },
        {
          "range": {
            "@timestamp": {
              "gte": "now-30d"
            }
          }
        }
      ]
    }
  },
  "aggs": {
    "completion_by_day": {
      "date_histogram": {
        "field": "@timestamp",
        "calendar_interval": "1d",
        "format": "yyyy-MM-dd"
      },
      "aggs": {
        "unique_issues": {
          "cardinality": {
            "field": "issue.key.keyword"
          }
        },
        "avg_throughput_time": {
          "avg": {
            "field": "issue.working_minutes"
          }
        }
      }
    }
  },
  "size": 0
}
```

## 4. Status Flow Analysis for Done Issues
```json
GET jira-changelog/_search
{
  "query": {
    "term": {
      "issue.status.name_lower": "done"
    }
  },
  "aggs": {
    "status_time_breakdown": {
      "nested": {
        "path": "status_transitions"
      },
      "aggs": {
        "by_from_status": {
          "terms": {
            "field": "status_transitions.from_status_lower",
            "size": 20
          },
          "aggs": {
            "avg_time_in_status": {
              "avg": {
                "field": "status_transitions.minutes_in_previous_status"
              }
            },
            "total_transitions": {
              "value_count": {
                "field": "status_transitions.transition_date"
              }
            }
          }
        }
      }
    }
  },
  "size": 0
}
```

## 5. Cycle Time vs Lead Time Analysis
```json
GET jira-changelog/_search
{
  "query": {
    "bool": {
      "must": [
        {
          "term": {
            "issue.status.name_lower": "done"
          }
        },
        {
          "exists": {
            "field": "from_selected_for_development.working_minutes"
          }
        }
      ]
    }
  },
  "aggs": {
    "cycle_vs_lead_time": {
      "date_histogram": {
        "field": "@timestamp",
        "calendar_interval": "1w",
        "format": "yyyy-MM-dd"
      },
      "aggs": {
        "avg_lead_time": {
          "avg": {
            "field": "issue.working_minutes"
          }
        },
        "avg_cycle_time": {
          "avg": {
            "field": "from_selected_for_development.working_minutes"
          }
        },
        "issue_count": {
          "value_count": {
            "field": "issue.key.keyword"
          }
        }
      }
    }
  },
  "size": 0
}
```

## 6. Issues with Backflow Analysis
```json
GET jira-changelog/_search
{
  "query": {
    "bool": {
      "must": [
        {
          "term": {
            "issue.status.name_lower": "done"
          }
        },
        {
          "range": {
            "backflow_count": {
              "gt": 0
            }
          }
        }
      ]
    }
  },
  "aggs": {
    "backflow_impact": {
      "terms": {
        "field": "backflow_count",
        "size": 10
      },
      "aggs": {
        "avg_throughput_time": {
          "avg": {
            "field": "issue.working_minutes"
          }
        },
        "avg_transitions": {
          "avg": {
            "field": "total_transitions"
          }
        }
      }
    }
  },
  "size": 20,
  "_source": ["issue.key", "issue.working_minutes", "backflow_count", "total_transitions"]
}
```

## 7. Throughput by Issue Type and Allocation
```json
GET jira-changelog/_search
{
  "query": {
    "term": {
      "issue.status.name_lower": "done"
    }
  },
  "aggs": {
    "by_issue_type": {
      "terms": {
        "field": "issue.type.name.keyword",
        "size": 10
      },
      "aggs": {
        "by_allocation": {
          "terms": {
            "field": "allocation.keyword",
            "size": 10
          },
          "aggs": {
            "avg_throughput": {
              "avg": {
                "field": "issue.working_minutes"
              }
            },
            "count": {
              "value_count": {
                "field": "issue.key.keyword"
              }
            }
          }
        }
      }
    }
  },
  "size": 0
}
```

## 8. Top 10 Longest Running Done Issues
```json
GET jira-changelog/_search
{
  "query": {
    "term": {
      "issue.status.name_lower": "done"
    }
  },
  "sort": [
    {
      "issue.working_minutes": {
        "order": "desc"
      }
    }
  ],
  "size": 10,
  "_source": [
    "issue.key",
    "issue.working_minutes",
    "issue.working_days",
    "issue.period",
    "project.key",
    "issue.type.name",
    "assignee.displayName",
    "summary"
  ]
}
```

## 9. Time Distribution in Different Workflow Stages
```json
GET jira-changelog/_search
{
  "query": {
    "term": {
      "issue.status.name_lower": "done"
    }
  },
  "aggs": {
    "backlog_time": {
      "avg": {
        "field": "backlog.working_minutes"
      }
    },
    "processing_time": {
      "avg": {
        "field": "processing.working_minutes"
      }
    },
    "waiting_time": {
      "avg": {
        "field": "waiting.working_minutes"
      }
    },
    "development_time": {
      "avg": {
        "field": "from_selected_for_development.working_minutes"
      }
    }
  },
  "size": 0
}
```

## 10. Monthly Throughput Performance
```json
GET jira-changelog/_search
{
  "query": {
    "bool": {
      "must": [
        {
          "term": {
            "issue.status.name_lower": "done"
          }
        },
        {
          "range": {
            "@timestamp": {
              "gte": "now-6M"
            }
          }
        }
      ]
    }
  },
  "aggs": {
    "monthly_performance": {
      "date_histogram": {
        "field": "@timestamp",
        "calendar_interval": "1M",
        "format": "yyyy-MM"
      },
      "aggs": {
        "issues_completed": {
          "cardinality": {
            "field": "issue.key.keyword"
          }
        },
        "avg_throughput": {
          "avg": {
            "field": "issue.working_minutes"
          }
        },
        "throughput_percentiles": {
          "percentiles": {
            "field": "issue.working_minutes",
            "percents": [50, 90]
          }
        }
      }
    }
  },
  "size": 0
}
```

## How to Use These Queries

1. Open Kibana Dev Tools: http://elastic.voyager.pl:5601/app/dev_tools#/console
2. Copy and paste any of the above queries
3. Click the "Play" button (triangle) to execute
4. Analyze the results in the response panel

## Key Metrics to Track

- **Lead Time**: Total time from issue creation to completion (`issue.working_minutes`)
- **Cycle Time**: Time from "Selected for Development" to completion (`from_selected_for_development.working_minutes`)
- **Throughput**: Number of issues completed per time period
- **Work in Progress**: Issues currently in active development
- **Backflow Rate**: Percentage of issues that move backwards in the workflow
- **Time in Status**: Average time spent in each workflow status
