# Elasticsearch Case Sensitivity Fix for Status Fields

## Problem
Elasticsearch's default behavior treats `keyword` fields as case-sensitive. This means:
- Searching for `issue.status.name : HOLD` works
- Searching for `issue.status.name : hold` doesn't work

## Solution
Added case-insensitive versions of all status-related fields using Elasticsearch normalizers and analyzers.

### Updated Fields

#### Main Status Fields
- `issue.status.name_lower` - Case-insensitive version of `issue.status.name` using `keyword` with `lowercase` normalizer
- `issue.type.name_lower` - Case-insensitive version of `issue.type.name` using `keyword` with `lowercase` normalizer

#### Status Transitions
- `status_transitions.from_status_lower` - Case-insensitive version of `status_transitions.from_status`
- `status_transitions.to_status_lower` - Case-insensitive version of `status_transitions.to_status`

#### Unique Statuses
- `unique_statuses_visited_lower` - Case-insensitive version of `unique_statuses_visited`

### Mapping Configuration
The mapping now includes:

```json
{
  "settings": {
    "analysis": {
      "normalizer": {
        "lowercase": {
          "type": "custom",
          "filter": ["lowercase"]
        }
      }
    }
  }
}
```

### Usage in Kibana

#### Case-Sensitive (Original Fields)
```
issue.status.name : "HOLD"
issue.status.name : "IN PROGRESS" 
status_transitions.from_status : "TODO"
```

#### Case-Insensitive (New Fields)
```
issue.status.name_lower : "hold"
issue.status.name_lower : "in progress"
issue.status.name_lower : "HOLD"  // Also works
status_transitions.from_status_lower : "todo"
status_transitions.to_status_lower : "done"
unique_statuses_visited_lower : "hold"
```

### Implementation
1. All mapping files updated:
   - `es_mapping.py` (main mapping)
   - `es_mapping_polish.py` (Polish language support)
   - `es_mapping_simple.py` (simplified mapping)

2. **Recreate Index**: Use the `update_es_mapping_case_insensitive.py` script to recreate the index with new mappings

3. **Populate Data**: The ETL process automatically populates both original and lowercase versions

### Running the Update

```powershell
# Recreate the index with case-insensitive fields
python update_es_mapping_case_insensitive.py

# Then repopulate the data
python es_populate.py
```

### Technical Details
- Uses Elasticsearch `normalizer` with `lowercase` filter for exact case-insensitive matching
- Maintains backward compatibility - original fields remain unchanged
- Optimized for performance with `keyword` fields instead of `text` fields where possible
- The ETL process will automatically populate both the original and `_lower` variants when data is indexed
