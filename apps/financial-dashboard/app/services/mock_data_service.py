#!/usr/bin/env python3
"""
Mock Data Service

Generates realistic mock data for the financial dashboards to allow
testing without a real database connection.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from typing import Dict, List, Any, Optional, Tuple

class MockDataService:
    """
    Generates mock data for financial dashboards testing.
    """
    
    def __init__(self):
        """Initialize the mock data service with base data."""
        self.customers = self._generate_mock_customers(50)
        self.students = self._generate_mock_students(100)
        self.enrollments = self._generate_mock_enrollments(200)
        self.payments = self._generate_mock_payments(300)
        self.lessons = self._generate_mock_lessons(500)
        self.payment_applications = self._generate_mock_payment_applications()
        
    def _generate_mock_customers(self, count: int) -> pd.DataFrame:
        """Generate mock customer data."""
        customer_ids = list(range(1, count + 1))
        first_names = ["John", "Jane", "Michael", "Emily", "David", "Sarah", "Robert", "Lisa",
                      "William", "Jessica", "James", "Jennifer", "Richard", "Elizabeth"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis",
                     "Garcia", "Rodriguez", "Wilson", "Martinez", "Anderson", "Taylor", "Thomas"]
        
        data = []
        for i in range(count):
            customer_id = customer_ids[i]
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            data.append({
                'user_id': customer_id,
                'firstname': first_name,
                'lastname': last_name,
                'email': f"{first_name.lower()}.{last_name.lower()}@example.com",
                'balance': round(random.uniform(-500, 2000), 2),
                'payment_frequency': random.choice(['Monthly', 'Quarterly', 'Annual']),
                'risk_score': random.randint(1, 10)
            })
        
        return pd.DataFrame(data)
    
    def _generate_mock_students(self, count: int) -> pd.DataFrame:
        """Generate mock student data."""
        student_ids = list(range(1, count + 1))
        first_names = ["Alex", "Jamie", "Taylor", "Jordan", "Casey", "Riley", "Avery", "Quinn",
                      "Morgan", "Skyler", "Blake", "Reese", "Dakota", "Cameron"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis",
                     "Garcia", "Rodriguez", "Wilson", "Martinez", "Anderson", "Taylor", "Thomas"]
        
        data = []
        for i in range(count):
            student_id = student_ids[i]
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            customer_id = random.choice(self.customers['user_id'].tolist())
            
            data.append({
                'student_id': student_id,
                'first_name': first_name,
                'last_name': last_name,
                'customer_id': customer_id
            })
        
        return pd.DataFrame(data)
    
    def _generate_mock_enrollments(self, count: int) -> pd.DataFrame:
        """Generate mock enrollment data."""
        enrollment_ids = list(range(1, count + 1))
        course_names = ["Piano Lessons", "Guitar Basics", "Violin for Beginners", "Drum Fundamentals",
                       "Voice Training", "Music Theory", "Saxophone 101", "Cello Techniques"]
        
        data = []
        for i in range(count):
            enrollment_id = enrollment_ids[i]
            student_id = random.choice(self.students['student_id'].tolist())
            course_name = random.choice(course_names)
            
            # Start date between 2 years ago and 6 months ago
            start_date = datetime.now() - timedelta(days=random.randint(180, 730))
            
            # End date between 6 months after start date and 1 year after start date
            # Some enrollments will be in the past, some current, some future
            end_date = start_date + timedelta(days=random.randint(180, 365))
            
            # Payment frequency matches the customer's preference
            student_row = self.students[self.students['student_id'] == student_id].iloc[0]
            customer_id = student_row['customer_id']
            customer_row = self.customers[self.customers['user_id'] == customer_id].iloc[0]
            payment_frequency = customer_row['payment_frequency']
            
            # Auto-renew is true for about 70% of enrollments
            is_auto_renew = random.choices([0, 1], weights=[30, 70])[0]
            
            data.append({
                'enrolment_id': enrollment_id,
                'student_id': student_id,
                'course_name': course_name,
                'payment_frequency': payment_frequency,
                'startDateTime': start_date,
                'endDateTime': end_date,
                'isAutoRenew': is_auto_renew
            })
        
        return pd.DataFrame(data)
    
    def _generate_mock_payments(self, count: int) -> pd.DataFrame:
        """Generate mock payment data."""
        payment_ids = list(range(1, count + 1))
        payment_methods = ["Credit Card", "Bank Transfer", "Cash", "Check", "PayPal"]
        payment_statuses = ["Completed", "Pending", "Failed", "Refunded"]
        
        data = []
        for i in range(count):
            payment_id = payment_ids[i]
            customer_id = random.choice(self.customers['user_id'].tolist())
            
            # Payment date between 1 year ago and today
            payment_date = datetime.now() - timedelta(days=random.randint(0, 365))
            
            # Amount between $50 and $500
            amount = round(random.uniform(50, 500), 2)
            
            # Balance is the amount remaining to be applied
            # Most payments are fully applied (balance=0)
            # Some have partial balance remaining
            balance = round(random.uniform(0, amount * 0.2), 2) if random.random() < 0.1 else 0
            
            payment_method = random.choice(payment_methods)
            status = random.choices(payment_statuses, weights=[85, 10, 3, 2])[0]
            
            data.append({
                'payment_id': payment_id,
                'user_id': customer_id,
                'payment_date': payment_date,
                'amount': amount,
                'balance': balance,
                'payment_method': payment_method,
                'status': status
            })
        
        return pd.DataFrame(data)
    
    def _generate_mock_lessons(self, count: int) -> pd.DataFrame:
        """Generate mock lesson data."""
        lesson_ids = list(range(1, count + 1))
        
        data = []
        for i in range(count):
            lesson_id = lesson_ids[i]
            
            # Select a random enrollment
            enrollment_row = self.enrollments.iloc[random.randint(0, len(self.enrollments) - 1)]
            enrollment_id = enrollment_row['enrolment_id']
            
            # Lesson date is between enrollment start date and end date
            start_date = enrollment_row['startDateTime']
            end_date = enrollment_row['endDateTime']
            lesson_date = start_date + (end_date - start_date) * random.random()
            
            # Due date is typically 2 weeks before lesson date
            # For some lessons, we'll simulate the due date shift issue
            due_date_normal = lesson_date - timedelta(days=14)
            
            # Simulate due date shift for ~10% of lessons (the bug we're investigating)
            has_due_date_shift = random.random() < 0.1
            due_date = due_date_normal
            if has_due_date_shift:
                # Shift due date to the past by 7-21 days from normal due date
                due_date = due_date_normal - timedelta(days=random.randint(7, 21))
            
            # Lesson amount between $30 and $100
            lesson_amount = round(random.uniform(30, 100), 2)
            
            # Paid status is random, but more likely to be paid for past lessons
            # and unpaid for future lessons
            is_past_lesson = lesson_date < datetime.now()
            paid_status_prob = 0.9 if is_past_lesson else 0.3
            paid_status = 1 if random.random() < paid_status_prob else 0
            
            # If we're simulating a due date shift, the lesson is more likely to be unpaid
            if has_due_date_shift:
                paid_status = 0
            
            data.append({
                'lesson_id': lesson_id,
                'enrolment_id': enrollment_id,
                'lesson_date': lesson_date,
                'due_date': due_date,
                'original_due_date': due_date_normal if has_due_date_shift else due_date,
                'has_due_date_shift': has_due_date_shift,
                'lesson_amount': lesson_amount,
                'paid_status': paid_status
            })
        
        return pd.DataFrame(data)
    
    def _generate_mock_payment_applications(self) -> pd.DataFrame:
        """Generate mock payment application data (lesson_payment)."""
        data = []
        
        # Process each payment
        for _, payment in self.payments.iterrows():
            payment_id = payment['payment_id']
            customer_id = payment['user_id']
            payment_date = payment['payment_date']
            payment_amount = payment['amount'] - payment['balance']
            
            # Find all students for this customer
            student_ids = self.students[self.students['customer_id'] == customer_id]['student_id'].tolist()
            
            # Find all enrollments for these students
            enrollment_ids = []
            for student_id in student_ids:
                enrollment_ids.extend(self.enrollments[self.enrollments['student_id'] == student_id]['enrolment_id'].tolist())
            
            # Find all lessons for these enrollments
            relevant_lessons = self.lessons[self.lessons['enrolment_id'].isin(enrollment_ids)].copy()
            
            # Sort lessons by due date and date (typical payment application logic)
            relevant_lessons = relevant_lessons.sort_values(['due_date', 'lesson_date'])
            
            # For some payments (~20%), we'll simulate the misapplication issue
            has_misapplication = random.random() < 0.2
            
            remaining_amount = payment_amount
            applications = []
            
            if has_misapplication:
                # Simulate misapplication by prioritizing future lessons over past lessons
                # Sort by reverse due date - this is the bug we're investigating
                misapplied_lessons = relevant_lessons.sort_values(['due_date', 'lesson_date'], ascending=False)
                
                # Apply to a few future lessons first
                future_lessons = misapplied_lessons[misapplied_lessons['lesson_date'] > payment_date]
                
                if not future_lessons.empty:
                    for _, lesson in future_lessons.iterrows():
                        if remaining_amount <= 0:
                            break
                            
                        # Apply part of the payment to this lesson
                        applied_amount = min(remaining_amount, lesson['lesson_amount'])
                        remaining_amount -= applied_amount
                        
                        applications.append({
                            'payment_id': payment_id,
                            'lesson_id': lesson['lesson_id'],
                            'applied_amount': applied_amount,
                            'is_problematic': True
                        })
                        
                        # Stop after applying to 1-3 future lessons
                        if random.random() < 0.5:
                            break
            
            # Apply remaining amount to lessons in the normal order
            for _, lesson in relevant_lessons.iterrows():
                if remaining_amount <= 0:
                    break
                    
                # Skip lessons that already have applications
                if any(app['lesson_id'] == lesson['lesson_id'] for app in applications):
                    continue
                    
                # Apply part of the payment to this lesson
                applied_amount = min(remaining_amount, lesson['lesson_amount'])
                remaining_amount -= applied_amount
                
                applications.append({
                    'payment_id': payment_id,
                    'lesson_id': lesson['lesson_id'],
                    'applied_amount': applied_amount,
                    'is_problematic': False
                })
            
            # Add all applications to the data
            data.extend(applications)
        
        return pd.DataFrame(data)
    
    # Methods to access mock data
    
    def get_customers_with_misapplied_payments(self) -> pd.DataFrame:
        """Get customers with misapplied payments."""
        # Find customers with problematic payment applications
        problematic_apps = self.payment_applications[self.payment_applications['is_problematic'] == True]
        
        if problematic_apps.empty:
            return pd.DataFrame()
            
        # Get the payment IDs
        payment_ids = problematic_apps['payment_id'].unique()
        
        # Get the corresponding customers
        customers_with_issues = self.payments[self.payments['payment_id'].isin(payment_ids)]['user_id'].unique()
        
        # Create result dataframe
        result = []
        for customer_id in customers_with_issues:
            customer_row = self.customers[self.customers['user_id'] == customer_id].iloc[0]
            customer_payments = self.payments[self.payments['user_id'] == customer_id]
            customer_problematic_payments = customer_payments[customer_payments['payment_id'].isin(payment_ids)]
            
            result.append({
                'user_id': customer_id,
                'firstname': customer_row['firstname'],
                'lastname': customer_row['lastname'],
                'num_suspicious_payments': len(customer_problematic_payments)
            })
        
        return pd.DataFrame(result)
    
    def get_customer_details(self, customer_id: str) -> Dict[str, Any]:
        """Get customer details."""
        if int(customer_id) not in self.customers['user_id'].values:
            return {}
            
        customer_row = self.customers[self.customers['user_id'] == int(customer_id)].iloc[0]
        return {
            'user_id': customer_row['user_id'],
            'customer_name': f"{customer_row['firstname']} {customer_row['lastname']}",
            'email': customer_row['email'],
            'balance': customer_row['balance'],
            'payment_frequency': customer_row['payment_frequency']
        }
    
    def get_customer_payments(self, customer_id: str) -> pd.DataFrame:
        """Get customer payments."""
        customer_payments = self.payments[self.payments['user_id'] == int(customer_id)]
        return customer_payments
