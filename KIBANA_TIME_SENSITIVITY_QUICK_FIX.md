# Quick Fix for Time-Sensitive Bar Visualization

## 🎯 **Immediate Solution**

Your bar visualization is sensitive to time periods because it's affected by:
- Incomplete current data
- Varying completion patterns over time
- Different work types in different periods

## 🛠️ **Quick Implementation Steps**

### **Step 1: Update Your Bar Chart Query**
Replace your current query filter with this stable version:

```json
{
  "bool": {
    "must": [
      {
        "term": {
          "issue.status.name_lower": "done"
        }
      },
      {
        "range": {
          "from_selected_for_development.working_minutes": {
            "gte": 60,
            "lte": 14400
          }
        }
      },
      {
        "range": {
          "issue.created": {
            "gte": "now-6M",
            "lte": "now-1w"
          }
        }
      }
    ]
  }
}
```

### **Step 2: Set Fixed Time Range in Kibana**
1. **Open your bar visualization**
2. **Click the time picker (top right)**
3. **Select "Absolute" tab**
4. **Set range: 6 months ago to 1 week ago**
5. **Click "Apply"**

### **Step 3: Adjust Histogram Buckets**
```json
{
  "histogram": {
    "field": "from_selected_for_development.working_minutes",
    "interval": 480,
    "min_doc_count": 1,
    "extended_bounds": {
      "min": 60,
      "max": 14400
    }
  }
}
```

## 📊 **What These Changes Do**

### **Filter by Creation Date (not completion)**
- **`issue.created: [now-6M TO now-1w]`** 
- Focuses on issues that had time to complete
- Avoids bias from current incomplete work

### **Exclude Outliers**
- **Min: 60 minutes** - Removes very quick fixes
- **Max: 14400 minutes (10 days)** - Removes extremely long cycles

### **Fixed Time Window**
- **6-month rolling window** - Consistent sample size
- **Exclude last week** - Avoids incomplete current data

## ✅ **Expected Results**

After applying these changes:
- **Stable bars** that don't change dramatically when you adjust time periods
- **Consistent patterns** across different time selections
- **Reliable throughput insights** for team performance analysis

## 🔧 **Alternative: Use the New Stable Configuration**

I've created a complete stable configuration in:
`kibana_stable_throughput_config.json`

This includes:
- Multiple time-insensitive visualizations
- Rolling averages for trend analysis
- Proper outlier filtering
- Comprehensive stability features

Choose either the quick fix above or implement the full stable configuration!
