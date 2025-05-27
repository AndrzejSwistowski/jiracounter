#!/usr/bin/env python3
"""
Example integration of working time calculations with JIRA issues.
This demonstrates how to use the new working time functions in a real JIRA application.
"""

import sys
import os
from datetime import datetime

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from time_utils import (
    calculate_working_minutes_between,
    calculate_working_minutes_since_date,
    is_working_day,
    parse_date,
    MINUTES_PER_WORK_DAY
)

class JiraIssueWorkingTimeAnalyzer:
    """
    Analyzer for calculating working time metrics for JIRA issues.
    """
    
    def __init__(self):
        self.metrics = {}
    
    def analyze_issue_working_time(self, issue_data):
        """
        Analyze working time metrics for a JIRA issue.
        
        Args:
            issue_data: Dictionary containing issue information with keys:
                       - key: Issue key (e.g., "PROJ-123")
                       - created: Creation date
                       - updated: Last updated date
                       - status: Current status
                       - resolved: Resolution date (if resolved)
                       - status_history: List of status changes
        
        Returns:
            Dictionary with working time metrics
        """
        issue_key = issue_data.get('key', 'Unknown')
        created = issue_data.get('created')
        updated = issue_data.get('updated')
        resolved = issue_data.get('resolved')
        status = issue_data.get('status', 'Unknown')
        
        metrics = {
            'issue_key': issue_key,
            'current_status': status,
            'created_date': created,
            'updated_date': updated,
            'resolved_date': resolved
        }
        
        # Calculate time since creation
        if created:
            metrics['working_minutes_since_creation'] = calculate_working_minutes_since_date(created)
            metrics['working_days_since_creation'] = self._minutes_to_days(metrics['working_minutes_since_creation'])
        
        # Calculate time since last update
        if updated:
            metrics['working_minutes_since_update'] = calculate_working_minutes_since_date(updated)
            metrics['working_days_since_update'] = self._minutes_to_days(metrics['working_minutes_since_update'])
        
        # Calculate resolution time (if resolved)
        if created and resolved:
            metrics['working_minutes_to_resolve'] = calculate_working_minutes_between(created, resolved)
            metrics['working_days_to_resolve'] = self._minutes_to_days(metrics['working_minutes_to_resolve'])
        
        # Calculate time in current status
        status_history = issue_data.get('status_history', [])
        if status_history:
            last_status_change = max(status_history, key=lambda x: x.get('date', ''))
            status_change_date = last_status_change.get('date')
            if status_change_date:
                metrics['working_minutes_in_current_status'] = calculate_working_minutes_since_date(status_change_date)
                metrics['working_days_in_current_status'] = self._minutes_to_days(metrics['working_minutes_in_current_status'])
        
        return metrics
    
    def _minutes_to_days(self, minutes):
        """Convert working minutes to working days."""
        if minutes is None:
            return None
        return round(minutes / MINUTES_PER_WORK_DAY, 2)
    
    def format_working_time_report(self, metrics):
        """
        Format working time metrics into a readable report.
        
        Args:
            metrics: Dictionary returned by analyze_issue_working_time
            
        Returns:
            String containing formatted report
        """
        lines = []
        lines.append(f"=== Working Time Analysis for {metrics['issue_key']} ===")
        lines.append(f"Current Status: {metrics['current_status']}")
        lines.append(f"Created: {metrics['created_date']}")
        
        if metrics.get('working_minutes_since_creation') is not None:
            days = metrics['working_days_since_creation']
            minutes = metrics['working_minutes_since_creation']
            lines.append(f"Time since creation: {days} working days ({minutes} minutes)")
        
        if metrics.get('working_minutes_since_update') is not None:
            days = metrics['working_days_since_update']
            minutes = metrics['working_minutes_since_update']
            lines.append(f"Time since last update: {days} working days ({minutes} minutes)")
        
        if metrics.get('working_minutes_to_resolve') is not None:
            days = metrics['working_days_to_resolve']
            minutes = metrics['working_minutes_to_resolve']
            lines.append(f"Time to resolve: {days} working days ({minutes} minutes)")
        
        if metrics.get('working_minutes_in_current_status') is not None:
            days = metrics['working_days_in_current_status']
            minutes = metrics['working_minutes_in_current_status']
            lines.append(f"Time in current status: {days} working days ({minutes} minutes)")
        
        return '\n'.join(lines)

def demo_jira_integration():
    """Demonstrate working time analysis with sample JIRA data."""
    print("=== JIRA Working Time Integration Demo ===\n")
    
    analyzer = JiraIssueWorkingTimeAnalyzer()
    
    # Sample JIRA issues data
    sample_issues = [
        {
            'key': 'PROJ-123',
            'created': '2025-05-20 10:30:00',
            'updated': '2025-05-26 15:20:00',
            'status': 'In Progress',
            'status_history': [
                {'status': 'Open', 'date': '2025-05-20 10:30:00'},
                {'status': 'In Progress', 'date': '2025-05-22 09:15:00'}
            ]
        },
        {
            'key': 'PROJ-124',
            'created': '2025-05-15 14:00:00',
            'updated': '2025-05-25 11:30:00',
            'resolved': '2025-05-25 11:30:00',
            'status': 'Done',
            'status_history': [
                {'status': 'Open', 'date': '2025-05-15 14:00:00'},
                {'status': 'In Progress', 'date': '2025-05-16 09:00:00'},
                {'status': 'Done', 'date': '2025-05-25 11:30:00'}
            ]
        },
        {
            'key': 'PROJ-125',
            'created': '2025-05-26 16:45:00',
            'updated': '2025-05-27 09:30:00',
            'status': 'Open',
            'status_history': [
                {'status': 'Open', 'date': '2025-05-26 16:45:00'}
            ]
        }
    ]
    
    # Analyze each issue
    for issue in sample_issues:
        metrics = analyzer.analyze_issue_working_time(issue)
        report = analyzer.format_working_time_report(metrics)
        print(report)
        print()

def demo_sla_monitoring():
    """Demonstrate SLA monitoring using working time calculations."""
    print("=== SLA Monitoring Demo ===\n")
    
    # Define SLA thresholds in working days
    sla_thresholds = {
        'Critical': 0.5,    # 4 hours
        'High': 1.0,        # 1 working day
        'Medium': 3.0,      # 3 working days
        'Low': 5.0          # 5 working days
    }
    
    # Sample issues with priorities
    issues_with_priorities = [
        {'key': 'CRIT-001', 'priority': 'Critical', 'created': '2025-05-27 08:00:00'},
        {'key': 'HIGH-002', 'priority': 'High', 'created': '2025-05-26 14:00:00'},
        {'key': 'MED-003', 'priority': 'Medium', 'created': '2025-05-23 10:00:00'},
        {'key': 'LOW-004', 'priority': 'Low', 'created': '2025-05-20 15:00:00'},
    ]
    
    print("SLA Breach Analysis:")
    print("Priority | Issue    | Days Elapsed | SLA Limit | Status")
    print("-" * 55)
    
    for issue in issues_with_priorities:
        minutes_elapsed = calculate_working_minutes_since_date(issue['created'])
        days_elapsed = minutes_elapsed / MINUTES_PER_WORK_DAY if minutes_elapsed else 0
        sla_limit = sla_thresholds[issue['priority']]
        
        status = "❌ BREACH" if days_elapsed > sla_limit else "✅ OK"
        
        print(f"{issue['priority']:<8} | {issue['key']:<8} | {days_elapsed:>11.2f} | {sla_limit:>9.1f} | {status}")

if __name__ == "__main__":
    print("JIRA Working Time Integration Examples")
    print("=" * 50)
    
    demo_jira_integration()
    demo_sla_monitoring()
    
    print("=" * 50)
    print("Integration examples completed!")
    print("\nNext steps:")
    print("1. Import the working time functions into your JIRA service")
    print("2. Add working time calculations to your issue analysis")
    print("3. Implement SLA monitoring based on working time")
    print("4. Create reports using working time metrics")
    print("5. Configure alerts for SLA breaches")
