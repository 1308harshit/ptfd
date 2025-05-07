#!/usr/bin/env python3
"""
Issue Reproduction Service

This service handles data retrieval and processing for the issue reproduction system,
providing mock or real data for visualizing and debugging payment misallocation and
enrollment issues.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from typing import Dict, List, Any, Optional, Tuple, Union
import logging

class IssueReproductionService:
    """
    Service for generating and retrieving data for the issue reproduction system.
    """
    
    def __init__(self):
        """Initialize the issue reproduction service."""
        self.logger = logging.getLogger(__name__)
    
    def get_reported_issues(self, issue_type: str = None) -> pd.DataFrame:
        """Get list of reported issues, optionally filtered by type.
        
        Args:
            issue_type: Optional filter for issue type
            
        Returns:
            DataFrame with reported issues
        """
        # In a real implementation, this would query a database
        # Here we're using hardcoded examples
        reported_issues = pd.DataFrame([
            {
                "customer_id": 123,
                "customer_name": "Mason Pereira",
                "issue_type": "Payment Misallocation",
                "reported_date": "2025-04-10",
                "notes": "Monthly payments: April 17th lesson payment applied to May 1st lesson"
            },
            {
                "customer_id": 456,
                "customer_name": "Irene Bassó",
                "issue_type": "Enrollment Status Issue",
                "reported_date": "2025-04-03",
                "notes": "Enrollment unexpectedly ended, marked inactive despite future lessons"
            },
            {
                "customer_id": 789,
                "customer_name": "Leo Williams",
                "issue_type": "Both Issues",
                "reported_date": "2025-04-15",
                "notes": "Payment misapplied and enrollment auto-renew disabled unexpectedly"
            }
        ])
        
        # Filter by issue type if specified
        if issue_type and issue_type != "Both Issues":
            reported_issues = reported_issues[reported_issues["issue_type"] == issue_type]
        
        return reported_issues
    
    def get_payment_issue_data(self, customer_id: int) -> Dict[str, Any]:
        """Get data for a reported payment issue.
        
        Args:
            customer_id: ID of the customer with the reported issue
            
        Returns:
            Dictionary with payment issue data
        """
        # This would normally retrieve real data based on the issue report
        payment_data = {
            "payment_id": 12345,
            "payment_date": "2025-04-05",
            "payment_amount": 100.00,
            "misallocated": True,
            "applied_to_future": True,
            "earlier_lessons_skipped": 2,
            "customer_id": customer_id
        }
        
        return payment_data
    
    def get_enrollment_issue_data(self, customer_id: int) -> Dict[str, Any]:
        """Get data for a reported enrollment issue.
        
        Args:
            customer_id: ID of the customer with the reported issue
            
        Returns:
            Dictionary with enrollment issue data
        """
        # This would normally retrieve real data based on the issue report
        enrollment_data = {
            "enrollment_id": 7890,
            "end_date_changed": True,
            "auto_renew_disabled": True,
            "future_lessons_scheduled": 8,
            "customer_id": customer_id
        }
        
        return enrollment_data
    
    def simulate_payment_issue(self, 
                              customer_id: int, 
                              payment_date: str, 
                              payment_amount: float) -> Dict[str, Any]:
        """Simulate a payment issue with the given parameters.
        
        Args:
            customer_id: ID of the customer
            payment_date: Date of the payment
            payment_amount: Amount of the payment
            
        Returns:
            Dictionary with simulated payment issue data
        """
        # Generate simulated payment issue data
        payment_data = {
            "payment_id": random.randint(10000, 99999),
            "payment_date": payment_date,
            "payment_amount": payment_amount,
            "misallocated": True,
            "applied_to_future": True,
            "earlier_lessons_skipped": random.randint(1, 3),
            "customer_id": customer_id
        }
        
        return payment_data
    
    def get_enrollment_issue_data(self, customer_id: int) -> Dict[str, Any]:
        """Get data for a reported enrollment issue.
        
        Args:
            customer_id: ID of the customer with the reported issue
            
        Returns:
            Dictionary with enrollment issue data
        """
        # This would normally retrieve real data based on the issue report
        enrollment_data = {
            "enrollment_id": 7890,
            "end_date_changed": True,
            "auto_renew_disabled": True,
            "future_lessons_scheduled": 8,
            "customer_id": customer_id
        }
        
        return enrollment_data
