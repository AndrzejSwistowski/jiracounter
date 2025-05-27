# Working Time Calculation Functions

This document describes the new working time calculation functions added to `time_utils.py`.

## Overview

The working time calculation functions provide precise calculation of working minutes between dates, taking into account:
- Working week: Monday to Friday
- Working hours: 9:00 AM to 5:00 PM (8 hours = 480 minutes per day)
- Polish holidays (automatically excluded)
- Weekend exclusion

## Functions

### `calculate_working_minutes_between(start_date, end_date)`

Calculates the number of working minutes between two dates.

**Parameters:**
- `start_date`: Start datetime (datetime object or string)
- `end_date`: End datetime (datetime object or string)

**Returns:**
- `int`: Number of working minutes between the dates
- `None`: If input is invalid

**Example:**
```python
from time_utils import calculate_working_minutes_between

# Same day calculation
minutes = calculate_working_minutes_between("2025-05-27 10:00:00", "2025-05-27 14:00:00")
print(f"Working minutes: {minutes}")  # Output: 240

# Multiple days
minutes = calculate_working_minutes_between("2025-05-27 09:00:00", "2025-05-29 17:00:00")
print(f"Working minutes: {minutes}")  # Output: 1440 (3 days × 480 minutes)
```

### `calculate_working_minutes_since_date(date_string)`

Calculates the number of working minutes between a given date and now.

**Parameters:**
- `date_string`: Date string in any reasonable format

**Returns:**
- `int`: Number of working minutes since the given date
- `None`: If date_string is None or invalid

**Example:**
```python
from time_utils import calculate_working_minutes_since_date

minutes = calculate_working_minutes_since_date("2025-05-26 10:00:00")
print(f"Working minutes since date: {minutes}")
```

### `is_polish_holiday(date_obj)`

Checks if a given date is a Polish holiday.

**Parameters:**
- `date_obj`: datetime object to check

**Returns:**
- `bool`: True if the date is a Polish holiday, False otherwise

**Example:**
```python
from time_utils import is_polish_holiday, parse_date

date = parse_date("2025-01-01")  # New Year's Day
is_holiday = is_polish_holiday(date)
print(f"Is holiday: {is_holiday}")  # Output: True
```

### `is_working_day(date_obj)`

Checks if a given date is a working day (Monday-Friday, not a Polish holiday).

**Parameters:**
- `date_obj`: datetime object to check

**Returns:**
- `bool`: True if it's a working day, False otherwise

**Example:**
```python
from time_utils import is_working_day, parse_date

date = parse_date("2025-05-27")  # Tuesday
is_work_day = is_working_day(date)
print(f"Is working day: {is_work_day}")  # Output: True
```

## Configuration

The working hours are configurable through constants:

```python
WORK_START_HOUR = 9      # 9:00 AM
WORK_END_HOUR = 17       # 5:00 PM
MINUTES_PER_WORK_DAY = 480  # 8 hours × 60 minutes
```

## Polish Holidays

The functions automatically handle Polish holidays using the `holidays` library. Supported holidays include:
- New Year's Day (Nowy Rok)
- Epiphany (Święto Trzech Króli)
- Easter Monday (Poniedziałek Wielkanocny)
- Labour Day (Święto Pracy)
- Constitution Day (Święto Konstytucji 3 Maja)
- Corpus Christi (Boże Ciało)
- Assumption Day (Wniebowzięcie Najświętszej Maryi Panny)
- All Saints' Day (Wszystkich Świętych)
- Independence Day (Narodowe Święto Niepodległości)
- Christmas Day (Boże Narodzenie)
- Boxing Day (Drugi dzień Bożego Narodzenia)

## Edge Cases Handled

1. **Time outside working hours**: Only time within 9:00-17:00 is counted
2. **Weekends**: Saturday and Sunday are excluded
3. **Holidays**: Polish holidays are automatically excluded
4. **Cross-day calculations**: Properly handles calculations spanning multiple days
5. **Invalid inputs**: Returns None for invalid or missing dates

## Dependencies

The functions require the `holidays` library:

```bash
pip install holidays
```

This dependency has been added to `requirements/requirements.txt`.

## Testing

Use the provided test script to verify functionality:

```bash
python test_working_time.py
```

The test script covers:
- Basic working time calculations
- Weekend exclusion
- Polish holiday detection
- Edge cases (outside working hours)
- Since-date calculations
