# Kibana Throughput Time Report Setup Guide

## Prerequisites
- Kibana access: http://elastic.voyager.pl:5601
- Index pattern: jira-changelog (with @timestamp as time field)

## 1. Done Issues Over Time (Line Chart)

### Steps to create:
1. Go to **Visualize** > **Create visualization** > **Line**
2. Select index: `jira-changelog`
3. Add filter: `issue.status.name_lower : "done"`
4. X-axis: Date Histogram on `@timestamp` with interval `1d`
5. Y-axis: Count
6. Save as: "Done Issues Over Time"

## 2. Throughput Time Distribution (Histogram)

### Steps to create:
1. **Visualize** > **Create visualization** > **Histogram**
2. Select index: `jira-changelog`
3. Add filter: `issue.status.name_lower : "done"`
4. X-axis: Histogram on `issue.working_minutes` with interval 480 (8 hours)
5. Y-axis: Count
6. Save as: "Throughput Time Distribution"

## 3. Average Cycle Time by Project (Data Table)

### Steps to create:
1. **Visualize** > **Create visualization** > **Data Table**
2. Select index: `jira-changelog`
3. Add filter: `issue.status.name_lower : "done"`
4. Bucket: Terms aggregation on `project.key.keyword`
5. Metrics:
   - Average of `issue.working_minutes`
   - Max of `issue.working_minutes`
   - Min of `issue.working_minutes`
   - Count
6. Save as: "Cycle Time by Project"

## 4. Status Breakdown Analysis (Data Table)

### Steps to create:
1. **Visualize** > **Create visualization** > **Data Table**
2. Select index: `jira-changelog`
3. Add filter: `issue.status.name_lower : "done"`
4. Split rows by: Terms on `issue.key.keyword`
5. Metrics:
   - Average of `backlog.working_minutes`
   - Average of `processing.working_minutes`
   - Average of `waiting.working_minutes`
   - Average of `from_selected_for_development.working_minutes`
6. Save as: "Status Time Breakdown"

## 5. Throughput by Issue Type (Line Chart)

### Steps to create:
1. **Visualize** > **Create visualization** > **Line**
2. Select index: `jira-changelog`
3. Add filter: `issue.status.name_lower : "done"`
4. X-axis: Date Histogram on `@timestamp` with interval `1w`
5. Y-axis: Average of `issue.working_minutes`
6. Split series: Terms on `issue.type.name.keyword`
7. Save as: "Throughput by Issue Type"

## 6. Lead Time vs Cycle Time (Line Chart)

### Steps to create:
1. **Visualize** > **Create visualization** > **Line**
2. Select index: `jira-changelog`
3. Add filter: `issue.status.name_lower : "done"`
4. X-axis: Date Histogram on `@timestamp` with interval `1w`
5. Y-axis: 
   - Series 1: Average of `issue.working_minutes` (Total Lead Time)
   - Series 2: Average of `from_selected_for_development.working_minutes` (Cycle Time)
6. Save as: "Lead Time vs Cycle Time"

## Key Filters to Use

### For Done Issues Only:
```
issue.status.name_lower : "done"
```

### For Specific Time Ranges:
```
@timestamp : [now-30d TO now]
```

### For Specific Projects:
```
project.key : "S3" OR project.key : "JI"
```

### For Specific Issue Types:
```
issue.type.name : "Task" OR issue.type.name : "Bug"
```

## Important Fields for Analysis

### Time-related fields:
- `issue.working_minutes` - Total time from creation to current status
- `issue.working_days` - Total working days
- `from_selected_for_development.working_minutes` - Cycle time
- `backlog.working_minutes` - Time in backlog
- `processing.working_minutes` - Time in processing
- `waiting.working_minutes` - Time waiting

### Status transition fields:
- `status_transitions` (nested) - All status changes with timing
- `total_transitions` - Number of status changes
- `backflow_count` - Number of backwards movements

### Grouping fields:
- `project.key` - Project
- `issue.type.name` - Issue type
- `assignee.displayName` - Assignee
- `allocation` - Work allocation type

## Sample Dashboard Layout

```
Row 1: [Done Issues Over Time] [Throughput Time Distribution]
Row 2: [Cycle Time by Project] [Status Time Breakdown] 
Row 3: [Throughput by Issue Type] [Lead Time vs Cycle Time]
```

## Advanced Queries

### Issues completed in last 30 days with long cycle time:
```
issue.status.name_lower : "done" AND @timestamp : [now-30d TO now] AND issue.working_minutes : >2880
```

### Issues with backflow (went backwards in workflow):
```
issue.status.name_lower : "done" AND backflow_count : >0
```

### High-performing vs low-performing projects:
Compare average cycle times between projects using the project breakdown table.
