# Same-Day Logic Modification for Working Time Calculation

## Summary

The `calculate_working_minutes_between` function in `time_utils.py` has been modified to include a special case for when the start and end dates are on the same day.

## What Changed

### Before
When start_date and end_date were on the same day:
- If the times were outside working hours (9:00-17:00), the function would return 0 minutes
- Only working hours were counted on weekends and holidays

### After
When start_date and end_date are on the same day:
- **ALL minutes between the two times are counted**, regardless of:
  - Working hours (9:00-17:00)
  - Weekends (Saturday/Sunday)
  - Polish holidays

## Code Changes

1. **Modified function**: `calculate_working_minutes_between()` in `time_utils.py`
2. **Added special case**: Check if `start_date.date() == end_date.date()`
3. **Updated docstring**: Added explanation of the special behavior
4. **Updated tests**: Modified existing tests to reflect new expectations

## Examples

### Same Day - Outside Working Hours (NEW BEHAVIOR)
```python
# Evening hours (after work)
minutes = calculate_working_minutes_between("2025-05-27 18:00:00", "2025-05-27 19:30:00")
# Result: 90 minutes (previously would have been 0)

# Early morning (before work)
minutes = calculate_working_minutes_between("2025-05-27 07:00:00", "2025-05-27 08:00:00")
# Result: 60 minutes (previously would have been 0)
```

### Same Day - Weekends (NEW BEHAVIOR)
```python
# Saturday
minutes = calculate_working_minutes_between("2025-05-24 10:00:00", "2025-05-24 14:00:00")
# Result: 240 minutes (previously would have been 0)
```

### Same Day - Holidays (NEW BEHAVIOR)
```python
# Christmas Day
minutes = calculate_working_minutes_between("2025-12-25 09:00:00", "2025-12-25 17:00:00")
# Result: 480 minutes (previously would have been 0)
```

### Multi-Day - Unchanged Behavior
```python
# Multiple days still respect working hours
minutes = calculate_working_minutes_between("2025-05-27 18:00:00", "2025-05-28 10:00:00")
# Result: 60 minutes (only the working portion on the second day)
```

## Testing

### Running Tests
```bash
# Basic tests
python test_working_time.py

# Comprehensive tests
python test_working_time_comprehensive.py

# Specific same-day logic tests
python test_same_day_logic.py
```

### Test Results
All tests pass with the new behavior:
- ✅ Same-day calculations within working hours
- ✅ Same-day calculations outside working hours
- ✅ Same-day calculations on weekends
- ✅ Same-day calculations on holidays
- ✅ Multi-day calculations (unchanged behavior)
- ✅ Edge cases and error handling

## Use Cases

This modification is particularly useful for:
1. **Meeting duration tracking** - Count actual meeting time even if outside work hours
2. **Incident response** - Track time spent on issues regardless of when they occur
3. **Overtime tracking** - Account for work done outside normal hours
4. **Flexible work arrangements** - Support non-standard working hours

## Backward Compatibility

⚠️ **Breaking Change**: This modification changes the behavior for same-day calculations. Code that relies on the previous behavior (returning 0 for same-day non-working hours) will need to be reviewed.

## Migration Notes

If you need the old behavior for specific use cases, you can check if the dates are on the same day and handle accordingly:

```python
from time_utils import calculate_working_minutes_between
from datetime import datetime

def calculate_working_minutes_old_behavior(start_date, end_date):
    """Calculate working minutes with the old same-day behavior."""
    start = parse_date(start_date) if isinstance(start_date, str) else start_date
    end = parse_date(end_date) if isinstance(end_date, str) else end_date
    
    # If same day and outside working hours, return 0 (old behavior)
    if start.date() == end.date():
        if not is_working_day(start):
            return 0
        # Check if both times are outside working hours
        if (start.hour < 9 and end.hour < 9) or (start.hour >= 17 and end.hour >= 17):
            return 0
    
    return calculate_working_minutes_between(start_date, end_date)
```
