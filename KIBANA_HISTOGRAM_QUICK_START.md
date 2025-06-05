# Quick Start: Development Throughput Histogram in Kibana

## Step-by-Step Instructions

### 1. Access Kibana
- Navigate to: http://elastic.voyager.pl:5601
- Go to **Visualize** → **Create visualization**

### 2. Create Bar Chart
- Select **Bar chart** (vertical bars work best for this analysis)
- Choose index pattern: `jira-changelog`

### 3. Add Filters
Click **Add Filter** and add these one by one:

**Filter 1 - Done Issues Only:**
```
Field: issue.status.name_lower
Operator: is
Value: done
```

**Filter 2 - Has Development Time:**
```
Field: from_selected_for_development.working_minutes
Operator: is between
From: 1
To: 999999
```

**Filter 3 - Recent Issues (Optional):**
```
Field: @timestamp
Operator: is between
From: now-30d
To: now
```

### 4. Configure X-Axis (Data Buckets)
- Click **Add** under "Buckets"
- Select **X-Axis**
- **Aggregation**: Histogram
- **Field**: `from_selected_for_development.working_minutes`
- **Interval**: 480
- **Custom Label**: "Development Time (Days)"

### 5. Configure Y-Axis (Metrics)
- The default **Count** metric is perfect
- **Custom Label**: "Number of Issues"

### 6. Run and Analyze
- Click the **Play** button (▶) to generate the chart
- You should see bars showing how many issues fall into each time bucket:
  - 0-480 minutes = 1 day or less
  - 480-960 minutes = 1-2 days  
  - 960-1440 minutes = 2-3 days
  - 1440+ minutes = More than 3 days

### 7. Customize Display
In the **Options** tab:
- **Chart title**: "Development Throughput Time Distribution"
- **Chart mode**: Normal
- **Show Tooltip**: Enabled
- **Show Legend**: Enabled

### 8. Save Visualization
- Click **Save**
- **Title**: "Development Throughput Distribution"
- **Description**: "Distribution of development cycle time from selected for development to done"

## Expected Results

### What You Should See:
- **X-axis**: Time buckets (0, 480, 960, 1440, etc.)
- **Y-axis**: Count of issues in each bucket
- **Bars**: Height shows how many issues took that amount of development time

### Typical Patterns:
- **Left-skewed**: Most issues complete quickly (good throughput)
- **Right-skewed**: Many issues take longer (potential bottlenecks)
- **Bimodal**: Two peaks may indicate different types of work
- **Long tail**: Few very long-running issues (outliers to investigate)

## Advanced: Add Split Series

To see throughput by project:

1. Click **Add** under "Buckets"
2. Select **Split Series**
3. **Sub Aggregation**: Terms
4. **Field**: `project.key.keyword`
5. **Size**: 5
6. **Custom Label**: "Project"

This will create separate colored bars for each project.

## Troubleshooting

### No Data Showing?
- Check your filters are correct
- Verify `from_selected_for_development.working_minutes` field exists
- Try expanding the time range

### Too Many Buckets?
- Increase interval to 960 (2-day buckets) or 1440 (3-day buckets)
- Add upper limit filter: `from_selected_for_development.working_minutes : <10000`

### Want Different Time Units?
- **Hourly buckets**: interval = 60
- **Half-day buckets**: interval = 240  
- **Daily buckets**: interval = 480
- **2-day buckets**: interval = 960

This histogram will give you a clear picture of your team's development throughput, focusing on actual work time rather than total lead time including backlog!
