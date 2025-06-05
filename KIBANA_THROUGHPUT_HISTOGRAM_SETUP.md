# Kibana Throughput Time Histogram Setup - Development Cycle Time

## Focus: True Development Throughput (Excluding Backlog Time)

This guide focuses on creating a throughput histogram that measures actual development time from `todo_exit_date` to completion, excluding time spent in backlog.

## Key Fields for Development Throughput

- `from_selected_for_development.working_minutes` - **Primary metric**: Development cycle time from selected for development to done
- `processing.working_minutes` - Time in active processing statuses
- `waiting.working_minutes` - Time in waiting/review statuses
- Combined: `processing + waiting` represents total development effort

## Step-by-Step: Create Development Throughput Histogram

### 1. Create Bar Chart Visualization

1. Navigate to **Kibana** → **Visualize** → **Create visualization**
2. Select **Bar chart** (not histogram - Bar chart is better for this analysis)
3. Choose index pattern: `jira-changelog`

### 2. Add Filters

Add these filters to focus on completed development work:

```
issue.status.name_lower : "done"
```

**Optional**: Add date range filter for recent analysis:
```
@timestamp : [now-30d TO now]
```

**Optional**: Exclude issues without development time:
```
from_selected_for_development.working_minutes : >0
```

### 3. Configure X-Axis (Buckets)

- **Aggregation**: Histogram
- **Field**: `from_selected_for_development.working_minutes`
- **Interval**: 480 (represents 8-hour/1-day buckets)
- **Label**: "Development Time (8-hour buckets)"

### 4. Configure Y-Axis (Metrics)

- **Aggregation**: Count
- **Label**: "Number of Issues"

### 5. Advanced Options

In **Options** tab:
- **Chart title**: "Development Throughput Time Distribution"
- **Y-axis title**: "Number of Issues"
- **X-axis title**: "Development Time (8-hour increments)"

### 6. Save Visualization

- **Title**: "Development Throughput Time Distribution"
- **Description**: "Distribution of development time from selected for development to done"

## Alternative: Processing + Waiting Time Histogram

If you prefer to focus on the sum of processing and waiting time, you can:

### Option A: Use Scripted Field

1. Go to **Management** → **Index Patterns** → `jira-changelog`
2. Create scripted field:
   - **Name**: `development_total_minutes`
   - **Type**: Number
   - **Script**: 
   ```javascript
   (doc['processing.working_minutes'].size() > 0 ? doc['processing.working_minutes'].value : 0) + 
   (doc['waiting.working_minutes'].size() > 0 ? doc['waiting.working_minutes'].value : 0)
   ```

### Option B: Use Direct Elasticsearch Query

Execute this query in **Dev Tools** to see the data:

```json
GET jira-changelog/_search
{
  "query": {
    "bool": {
      "filter": [
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
    "development_time_distribution": {
      "histogram": {
        "field": "from_selected_for_development.working_minutes",
        "interval": 480,
        "min_doc_count": 1
      },
      "aggs": {
        "avg_processing_time": {
          "avg": {
            "field": "processing.working_minutes"
          }
        },
        "avg_waiting_time": {
          "avg": {
            "field": "waiting.working_minutes"
          }
        }
      }
    }
  },
  "size": 0
}
```

## Understanding the Results

### Throughput Buckets (8-hour intervals):
- **0-480 minutes**: Issues completed in 1 work day or less
- **480-960 minutes**: Issues taking 1-2 work days
- **960-1440 minutes**: Issues taking 2-3 work days
- **1440+ minutes**: Issues taking more than 3 work days

### Key Insights to Look For:
1. **Peak bucket**: Most common development time
2. **Long tail**: Issues taking exceptionally long
3. **Distribution shape**: Normal, skewed, or bimodal
4. **Outliers**: Issues significantly above average

## Additional Development Metrics

### Create Supporting Visualizations:

1. **Development Time by Project** (Data Table)
   - Group by: `project.key`
   - Metrics: Avg, Min, Max of `from_selected_for_development.working_minutes`

2. **Processing vs Waiting Time** (Line Chart)
   - X-axis: Date histogram on `@timestamp`
   - Y-axis: Avg of `processing.working_minutes` and `waiting.working_minutes`

3. **Development Efficiency** (Gauge)
   - Metric: Average of `from_selected_for_development.working_minutes`
   - Goal: Set based on your team's target cycle time

## Sample Dashboard Layout

```
Row 1: [Development Throughput Distribution] [Development Time by Project]
Row 2: [Processing vs Waiting Time] [Development Efficiency Gauge]
Row 3: [Issues Over Time] [Backflow Impact Analysis]
```

## Key Filters for Analysis

### Quick Filters:
- **Last month**: `@timestamp : [now-30d TO now]`
- **Specific project**: `project.key : "YOUR_PROJECT"`
- **No backlog time**: `from_selected_for_development.working_minutes : >0`
- **High performers**: `from_selected_for_development.working_minutes : [0 TO 960]`
- **Struggling issues**: `from_selected_for_development.working_minutes : >2880`

This setup will give you a clear view of actual development throughput, excluding the time issues spend in backlog, which aligns with your focus on true development cycle time!
