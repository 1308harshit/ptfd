#!/usr/bin/env python3
"""
Financial Dashboards Service

This service handles data retrieval and processing for various financial analysis
dashboards, pulling real data from the SMW legacy database or generating mock data
for development and testing purposes.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
import logging
import os
import random

from app.repositories.legacy_repository import LegacyDatabaseRepository, DatabaseConfig
from app.services.mock_data_service import MockDataService

class FinancialDashboardsService:
    """
    Service for generating data-driven financial analysis dashboards.
    Supports both real database connections and mock data for development.
    """

    def __init__(self, db_config: Optional[DatabaseConfig] = None, use_mock: Optional[bool] = None):
        """Initialize the service with a database repository or mock data.
        
        Args:
            db_config: Database configuration for real data access
            use_mock: Force using mock data; if None, will use mock data if DATABASE_URL env var is not set
        """
        self.logger = logging.getLogger(__name__)
        
        # Determine whether to use mock data
        if use_mock is None:
            use_mock = os.environ.get('DATABASE_URL') is None or os.environ.get('USE_MOCK_DATA') == '1'
        
        self.use_mock = use_mock
        
        if self.use_mock:
            self.logger.info("Using mock data for financial dashboards")
            self.mock_service = MockDataService()
        else:
            self.logger.info("Using real database connection for financial dashboards")
            if db_config is None:
                db_config = DatabaseConfig()  # Use default config if none provided
            self.repo = LegacyDatabaseRepository(config=db_config)
        
        # Cache for data
        self.raw_payment_data = None
        self.raw_cycle_data = None

    def _fetch_data_if_needed(self):
        """Fetches data from the repository if it hasn't been fetched yet."""
        if self.use_mock:
            # No need to fetch data for mock service
            return
            
        if self.raw_payment_data is None:
            try:
                self.logger.info("Fetching payment data for financial dashboards...")
                self.raw_payment_data = pd.DataFrame(self.repo.fetch_payment_data(limit=10000))
                if not self.raw_payment_data.empty and 'payment_date' in self.raw_payment_data.columns:
                    self.raw_payment_data['payment_date'] = pd.to_datetime(self.raw_payment_data['payment_date'], errors='coerce')
                self.logger.info(f"Successfully fetched {len(self.raw_payment_data)} payment records.")
            except Exception as e:
                self.logger.error(f"Error fetching payment data: {e}")
                self.raw_payment_data = pd.DataFrame() # Ensure it's an empty DataFrame on error

        if self.raw_cycle_data is None:
            try:
                self.logger.info("Fetching payment cycle data for financial dashboards...")
                self.raw_cycle_data = pd.DataFrame(self.repo.fetch_payment_cycle_data())
                if not self.raw_cycle_data.empty:
                    if 'payment_date' in self.raw_cycle_data.columns:
                        self.raw_cycle_data['payment_date'] = pd.to_datetime(self.raw_cycle_data['payment_date'], errors='coerce')
                    if 'invoice_date' in self.raw_cycle_data.columns:
                         self.raw_cycle_data['invoice_date'] = pd.to_datetime(self.raw_cycle_data['invoice_date'], errors='coerce')
                self.logger.info(f"Successfully fetched {len(self.raw_cycle_data)} payment cycle records.")
            except Exception as e:
                self.logger.error(f"Error fetching payment cycle data: {e}")
                self.raw_cycle_data = pd.DataFrame()
                
    # -------------- New Methods for Financial Dashboards --------------
    
    def get_customers_with_misapplied_payments(self) -> pd.DataFrame:
        """Get customers who have potentially misapplied payments."""
        if self.use_mock:
            return self.mock_service.get_customers_with_misapplied_payments()
        
        try:
            return pd.DataFrame(self.repo.get_customers_with_misapplied_payments())
        except Exception as e:
            self.logger.error(f"Error getting customers with misapplied payments: {e}")
            return pd.DataFrame()
    
    def get_customer_details(self, customer_id: str) -> Dict[str, Any]:
        """Get details about a specific customer."""
        if self.use_mock:
            return self.mock_service.get_customer_details(customer_id)
        
        try:
            return self.repo.get_customer_details(customer_id) or {}
        except Exception as e:
            self.logger.error(f"Error getting customer details: {e}")
            return {}
    
    def get_customer_payments(self, customer_id: str) -> pd.DataFrame:
        """Get all payments for a customer."""
        if self.use_mock:
            return self.mock_service.get_customer_payments(customer_id)
        
        try:
            return pd.DataFrame(self.repo.get_customer_payments(customer_id))
        except Exception as e:
            self.logger.error(f"Error getting customer payments: {e}")
            return pd.DataFrame()
    
    def get_payment_details(self, payment_id: str) -> Dict[str, Any]:
        """Get details about a specific payment."""
        if self.use_mock:
            # TODO: Implement in mock service
            return {
                'payment_id': payment_id,
                'payment_date': datetime.now() - timedelta(days=30),
                'amount': 150.00,
                'payment_method': 'Credit Card'
            }
        
        try:
            return self.repo.get_payment_details(payment_id) or {}
        except Exception as e:
            self.logger.error(f"Error getting payment details: {e}")
            return {}
    
    def get_related_enrolment_details(self, payment_id: str) -> Dict[str, Any]:
        """Get details about enrollments related to a payment."""
        if self.use_mock:
            # TODO: Implement in mock service
            return {
                'enrolment_id': 123,
                'payment_frequency': 'Monthly'
            }
        
        try:
            return self.repo.get_related_enrolment_details(payment_id) or {}
        except Exception as e:
            self.logger.error(f"Error getting related enrollment details: {e}")
            return {}
    
    def get_current_payment_applications(self, payment_id: str) -> pd.DataFrame:
        """Get current applications of a payment to lessons."""
        if self.use_mock:
            # TODO: Implement in mock service
            # Generate mock data for demonstration
            data = []
            payment_details = self.get_payment_details(payment_id)
            payment_date = payment_details.get('payment_date')
            
            # Generate some applications to lessons around the payment date
            for i in range(5):
                is_future = i >= 3  # Make some future lessons
                lesson_date = payment_date + timedelta(days=15*i if is_future else -15*i)
                due_date = lesson_date - timedelta(days=14)
                
                data.append({
                    'lesson_id': 1000 + i,
                    'lesson_date': lesson_date,
                    'lesson_due_date': due_date,
                    'lesson_amount': 50.00,
                    'applied_amount': 30.00,
                    'is_future_lesson': is_future
                })
            
            return pd.DataFrame(data)
        
        try:
            return pd.DataFrame(self.repo.get_current_payment_applications(payment_id))
        except Exception as e:
            self.logger.error(f"Error getting current payment applications: {e}")
            return pd.DataFrame()
    
    def get_expected_payment_applications(self, payment_id: str) -> pd.DataFrame:
        """Get expected applications of a payment to lessons (simulated correct behavior)."""
        # This is our simulated correct behavior
        # In a real implementation, this would apply business rules for correct payment application
        if self.use_mock:
            # Generate mock data for the expected (correct) payment application
            data = []
            payment_details = self.get_payment_details(payment_id)
            payment_date = payment_details.get('payment_date')
            
            # Generate expected applications - always to lessons due on or before payment date
            for i in range(5):
                lesson_date = payment_date - timedelta(days=7*i)
                due_date = lesson_date - timedelta(days=14)
                
                data.append({
                    'lesson_id': 2000 + i,
                    'lesson_date': lesson_date,
                    'lesson_due_date': due_date,
                    'lesson_amount': 50.00,
                    'applied_amount': 30.00,
                    'is_future_lesson': False  # Correct behavior never applies to future lessons
                })
            
            return pd.DataFrame(data)
        
        # For a real database, we would simulate the correct application logic
        # This is a simplified example - a real implementation would include complex business rules
        try:
            # Get the payment details
            payment = self.repo.get_payment_details(payment_id)
            if not payment:
                return pd.DataFrame()
                
            payment_date = payment.get('payment_date')
            user_id = payment.get('user_id')
            
            # Find all owing lessons for this customer on or before the payment date
            # Ordered by due date then lesson date
            # This is the simulated correct behavior
            
            # This would be a complex database query in practice
            # For now, we'll return an empty DataFrame
            return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Error simulating expected payment applications: {e}")
            return pd.DataFrame()
    
    def get_payment_application_discrepancies(self, payment_id: str) -> Dict[str, Any]:
        """Get discrepancies between current and expected payment applications."""
        current = self.get_current_payment_applications(payment_id)
        expected = self.get_expected_payment_applications(payment_id)
        
        if current.empty and expected.empty:
            return {'discrepancy_found': False}
        
        # Find lessons that were paid but shouldn't be
        incorrectly_paid = pd.DataFrame()
        if not current.empty:
            current_lesson_ids = set(current['lesson_id'].tolist())
            expected_lesson_ids = set() if expected.empty else set(expected['lesson_id'].tolist())
            
            incorrect_ids = current_lesson_ids - expected_lesson_ids
            if incorrect_ids:
                incorrectly_paid = current[current['lesson_id'].isin(incorrect_ids)]
        
        # Find lessons that should be paid but weren't
        should_be_paid = pd.DataFrame()
        if not expected.empty:
            current_lesson_ids = set() if current.empty else set(current['lesson_id'].tolist())
            expected_lesson_ids = set(expected['lesson_id'].tolist())
            
            missing_ids = expected_lesson_ids - current_lesson_ids
            if missing_ids:
                should_be_paid = expected[expected['lesson_id'].isin(missing_ids)]
        
        # For due date shifts, we would need historical data
        # This is a simplified mock for demonstration
        due_date_shifts = pd.DataFrame()
        if self.use_mock:
            # Create mock due date shifts
            data = []
            if not current.empty:
                for i in range(min(2, len(current))):
                    row = current.iloc[i]
                    lesson_date = row['lesson_date']
                    new_due_date = row['lesson_due_date']
                    original_due_date = new_due_date + timedelta(days=random.randint(7, 14))
                    
                    data.append({
                        'lesson_id': row['lesson_id'],
                        'lesson_date': lesson_date,
                        'original_due_date': original_due_date,
                        'new_due_date': new_due_date
                    })
            
            due_date_shifts = pd.DataFrame(data)
        
        return {
            'discrepancy_found': not incorrectly_paid.empty or not should_be_paid.empty or not due_date_shifts.empty,
            'discrepancy_data': {
                'incorrectly_paid': incorrectly_paid,
                'should_be_paid': should_be_paid,
                'due_date_shifts': due_date_shifts
            }
        }
    
    def get_affected_customers(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Get customers affected by payment misapplication issues in the given date range."""
        if self.use_mock:
            # Return our mock data of affected customers
            return self.mock_service.get_customers_with_misapplied_payments()
        
        try:
            # In a real implementation, we would filter by date range
            return pd.DataFrame(self.repo.get_customers_with_misapplied_payments())
        except Exception as e:
            self.logger.error(f"Error getting affected customers: {e}")
            return pd.DataFrame()
    
    def get_affected_enrollments(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Get enrollments potentially affected by issues in the given date range."""
        if self.use_mock:
            # TODO: Implement in mock service
            # Generate some mock affected enrollments
            data = []
            for i in range(10):
                end_date_val = datetime.now() - timedelta(days=random.randint(-30, 30))
                
                data.append({
                    'enrolment_id': 3000 + i,
                    'first_name': f"Student{i}",
                    'last_name': f"Lastname{i}",
                    'endDateTime': end_date_val,
                    'isAutoRenew': 0  # These are problematic because auto-renew is off
                })
            
            return pd.DataFrame(data)
        
        try:
            return pd.DataFrame(self.repo.get_affected_enrollments(start_date, end_date))
        except Exception as e:
            self.logger.error(f"Error getting affected enrollments: {e}")
            return pd.DataFrame()
    
    def get_customer_enrollments(self, customer_id: str) -> pd.DataFrame:
        """Get all enrollments for a customer."""
        if self.use_mock:
            # TODO: Implement in mock service
            # Generate some mock enrollments
            data = []
            for i in range(3):
                start_date = datetime.now() - timedelta(days=180 + 30*i)
                end_date = start_date + timedelta(days=365)
                
                data.append({
                    'enrolment_id': 4000 + i,
                    'student_name': f"Student {i+1}",
                    'course_name': f"Course {i+1}",
                    'payment_frequency': random.choice(['Monthly', 'Quarterly', 'Annual']),
                    'startDateTime': start_date,
                    'endDateTime': end_date,
                    'isAutoRenew': random.choice([0, 1])
                })
            
            return pd.DataFrame(data)
        
        try:
            return pd.DataFrame(self.repo.get_customer_enrollments(customer_id))
        except Exception as e:
            self.logger.error(f"Error getting customer enrollments: {e}")
            return pd.DataFrame()
    
    def get_customer_payment_statistics(self, customer_id: str) -> Dict[str, Any]:
        """Get payment statistics for a customer."""
        customer_payments = self.get_customer_payments(customer_id)
        
        if customer_payments.empty:
            return {
                'total_payments': 0,
                'total_amount_paid': 0,
                'avg_payment_amount': 0
            }
        
        return {
            'total_payments': len(customer_payments),
            'total_amount_paid': customer_payments['amount'].sum(),
            'avg_payment_amount': customer_payments['amount'].mean()
        }
    
    def get_customer_risk_indicators(self, customer_id: str) -> Dict[str, Any]:
        """Get risk indicators for a customer."""
        if self.use_mock:
            # Generate mock risk indicators
            return {
                'payment_issue_risk_score': random.randint(1, 10),
                'payment_issue_risk_delta': random.choice([-2, -1, 0, 1, 2]),
                'missed_payments_count': random.randint(0, 5),
                'missed_payments_delta': random.choice([-1, 0, 1]),
                'misapplied_payments_count': random.randint(0, 3),
                'misapplied_payments_delta': random.choice([-1, 0, 1]),
                'due_date_shifts_count': random.randint(0, 4),
                'due_date_shifts_delta': random.choice([-1, 0, 1])
            }
        
        # In a real implementation, we would calculate these from historical data
        return {
            'payment_issue_risk_score': 0,
            'payment_issue_risk_delta': 0,
            'missed_payments_count': 0,
            'missed_payments_delta': 0,
            'misapplied_payments_count': 0,
            'misapplied_payments_delta': 0,
            'due_date_shifts_count': 0,
            'due_date_shifts_delta': 0
        }
    
    def get_customer_timeline_data(self, customer_id: str, start_date: str, end_date: str) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[int, List[Dict[str, Any]]]]:
        """Get timeline data for customer's lessons and payments."""
        if self.use_mock:
            # Generate mock timeline data
            lessons_data = []
            start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Generate lessons spanning the date range
            for i in range(20):
                lesson_date = start_date_dt + (end_date_dt - start_date_dt) * random.random()
                due_date = lesson_date - timedelta(days=14)
                paid_status = random.choice([0, 1])  # 0=unpaid, 1=paid
                
                lessons_data.append({
                    'lesson_id': 5000 + i,
                    'lesson_date': lesson_date,
                    'due_date': due_date,
                    'student_name': f"Student {random.randint(1, 3)}",
                    'lesson_amount': random.uniform(30, 100),
                    'paid_status': paid_status
                })
            
            # Generate payments
            payments_data = []
            for i in range(5):
                payment_date = start_date_dt + (end_date_dt - start_date_dt) * random.random()
                amount = random.uniform(100, 500)
                
                payments_data.append({
                    'payment_id': 6000 + i,
                    'payment_date': payment_date,
                    'amount': amount,
                    'payment_method': random.choice(['Credit Card', 'Bank Transfer', 'Cash'])
                })
            
            # Generate payment allocations
            payment_allocations = {}
            for payment in payments_data:
                payment_id = payment['payment_id']
                allocations = []
                
                # Allocate to random lessons
                for _ in range(random.randint(2, 5)):
                    if not lessons_data:
                        continue
                        
                    lesson = random.choice(lessons_data)
                    
                    # Determine if this allocation is problematic
                    is_problematic = (payment['payment_date'] - lesson['lesson_date']).days > 14
                    
                    allocations.append({
                        'lesson_id': lesson['lesson_id'],
                        'lesson_date': lesson['lesson_date'],
                        'applied_amount': min(lesson['lesson_amount'], payment['amount'] / 3),
                        'is_problematic': is_problematic
                    })
                
                payment_allocations[payment_id] = allocations
            
            return pd.DataFrame(lessons_data), pd.DataFrame(payments_data), payment_allocations
        
        # In a real implementation, we would query the database for this data
        return pd.DataFrame(), pd.DataFrame(), {}
    
    def get_payment_lesson_allocations(self, payment_id: str) -> pd.DataFrame:
        """Get lesson allocations for a payment."""
        if self.use_mock:
            # Generate mock lesson allocations
            data = []
            payment_details = self.get_payment_details(payment_id)
            payment_date = payment_details.get('payment_date')
            payment_amount = payment_details.get('amount', 100)
            
            for i in range(random.randint(2, 5)):
                lesson_date = payment_date - timedelta(days=7*i)
                applied_amount = payment_amount / random.randint(2, 4)
                
                data.append({
                    'lesson_id': 7000 + i,
                    'lesson_date': lesson_date,
                    'applied_amount': applied_amount,
                    'student_name': f"Student {random.randint(1, 3)}"
                })
            
            return pd.DataFrame(data)
        
        # In a real implementation, we would query the database for this data
        return pd.DataFrame()
    
    def get_payment_invoice_allocations(self, payment_id: str) -> pd.DataFrame:
        """Get invoice allocations for a payment."""
        if self.use_mock:
            # Generate mock invoice allocations
            data = []
            payment_details = self.get_payment_details(payment_id)
            payment_date = payment_details.get('payment_date')
            payment_amount = payment_details.get('amount', 100)
            
            # Most payments don't have invoice allocations
            if random.random() < 0.7:
                return pd.DataFrame()
            
            for i in range(random.randint(1, 2)):
                invoice_date = payment_date - timedelta(days=14*i)
                applied_amount = payment_amount / random.randint(1, 3)
                
                data.append({
                    'invoice_id': 8000 + i,
                    'invoice_date': invoice_date,
                    'applied_amount': applied_amount
                })
            
            return pd.DataFrame(data)
        
        # In a real implementation, we would query the database for this data
        return pd.DataFrame()
    
    def get_payment_correction_impact(self, payment_id: str) -> Dict[str, Any]:
        """Get the impact of correcting a payment's allocation."""
        if self.use_mock:
            # Generate mock impact metrics
            return {
                'newly_paid_lessons': random.randint(1, 3),
                'no_longer_paid_lessons': random.randint(1, 3),
                'due_date_corrections': random.randint(1, 4),
                'impact_description': """
                Correcting this payment's allocation would result in earlier lessons being 
                paid properly, which aligns with the customer's billing cycle expectations. 
                Due dates would be restored to their original values, and the system would 
                no longer show incorrect past-due amounts.
                """
            }
        
        # In a real implementation, we would calculate the impact from our simulation
        return {}

    def _create_empty_figure(self, title: str, message: str = "No data available to display.") -> go.Figure:
        """Creates an empty Plotly figure with a title and message."""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(title_text=title)
        return fig

    # --- Example Financial Dashboards --- 

    def create_payment_volume_over_time_plot(self, time_period='M') -> go.Figure:
        """1. Payment Volume Over Time (e.g., daily, weekly, monthly)."""
        title = f"Payment Volume Over Time ({'Monthly' if time_period == 'M' else 'Daily' if time_period == 'D' else 'Weekly'})"
        self._fetch_data_if_needed()
        if self.raw_payment_data.empty or 'payment_date' not in self.raw_payment_data.columns or 'amount' not in self.raw_payment_data.columns:
            return self._create_empty_figure(title)
        
        df = self.raw_payment_data.dropna(subset=['payment_date', 'amount'])
        if df.empty:
            return self._create_empty_figure(title)

        df_resampled = df.set_index('payment_date').resample(time_period)['amount'].sum().reset_index()
        if df_resampled.empty:
            return self._create_empty_figure(title)

        fig = px.line(df_resampled, x='payment_date', y='amount', title=title,
                        labels={'payment_date': 'Date', 'amount': 'Total Payment Amount ($)'})
        fig.update_layout(yaxis_tickprefix='$', yaxis_tickformat=',.0f')
        return fig

    def create_payment_status_distribution_plot(self) -> go.Figure:
        """2. Payment Status Distribution (e.g., successful, pending, failed)."""
        title = "Payment Status Distribution"
        self._fetch_data_if_needed()
        if self.raw_payment_data.empty or 'status' not in self.raw_payment_data.columns:
            return self._create_empty_figure(title)
        
        status_counts = self.raw_payment_data['status'].value_counts().reset_index()
        status_counts.columns = ['status', 'count']
        if status_counts.empty:
             return self._create_empty_figure(title)

        fig = px.pie(status_counts, values='count', names='status', title=title,
                     color_discrete_sequence=px.colors.qualitative.Set3)
        return fig

    def create_average_payment_value_plot(self) -> go.Figure:
        """3. Average Payment Value by Payment Method."""
        title = "Average Payment Value by Method"
        self._fetch_data_if_needed()
        if self.raw_payment_data.empty or 'payment_method' not in self.raw_payment_data.columns or 'amount' not in self.raw_payment_data.columns:
            return self._create_empty_figure(title)

        avg_value = self.raw_payment_data.groupby('payment_method')['amount'].mean().reset_index()
        avg_value.columns = ['payment_method', 'average_amount']
        if avg_value.empty:
            return self._create_empty_figure(title)

        fig = px.bar(avg_value, x='payment_method', y='average_amount', title=title,
                     labels={'payment_method': 'Payment Method', 'average_amount': 'Average Payment Amount ($)'},
                     color='payment_method')
        fig.update_layout(yaxis_tickprefix='$', yaxis_tickformat=',.0f')
        return fig

    def create_payment_method_popularity_plot(self) -> go.Figure:
        """4. Payment Method Popularity (count of transactions per method)."""
        title = "Payment Method Popularity"
        self._fetch_data_if_needed()
        if self.raw_payment_data.empty or 'payment_method' not in self.raw_payment_data.columns:
            return self._create_empty_figure(title)

        method_counts = self.raw_payment_data['payment_method'].value_counts().reset_index()
        method_counts.columns = ['payment_method', 'transaction_count']
        if method_counts.empty:
            return self._create_empty_figure(title)

        fig = px.bar(method_counts, x='payment_method', y='transaction_count', title=title,
                     labels={'payment_method': 'Payment Method', 'transaction_count': 'Number of Transactions'},
                     color='payment_method')
        return fig

    def create_revenue_by_month_plot(self) -> go.Figure:
        """5. Revenue by Month (Total amount of successful payments per month)."""
        title = "Total Revenue by Month"
        self._fetch_data_if_needed()
        if self.raw_payment_data.empty or 'payment_date' not in self.raw_payment_data.columns or 'amount' not in self.raw_payment_data.columns or 'status' not in self.raw_payment_data.columns:
            return self._create_empty_figure(title)

        # Assuming 'status' column exists and 'completed', 'succeeded', 'paid' are successful statuses
        # This might need adjustment based on actual status values in your DB
        successful_statuses = ['completed', 'succeeded', 'paid', 'approved', 'processed'] 
        df_successful = self.raw_payment_data[
            self.raw_payment_data['status'].astype(str).str.lower().isin(successful_statuses)
        ]
        if df_successful.empty:
            return self._create_empty_figure(title, "No successful payment data found.")

        df_successful['month_year'] = df_successful['payment_date'].dt.to_period('M').astype(str)
        revenue_by_month = df_successful.groupby('month_year')['amount'].sum().reset_index()
        if revenue_by_month.empty:
            return self._create_empty_figure(title)
            
        revenue_by_month = revenue_by_month.sort_values('month_year')

        fig = px.bar(revenue_by_month, x='month_year', y='amount', title=title,
                     labels={'month_year': 'Month', 'amount': 'Total Revenue ($)'})
        fig.update_layout(yaxis_tickprefix='$', yaxis_tickformat=',.0f')
        return fig

    # --- Advanced Financial Dashboards for Deep Insights ---

    def get_mock_customer_360_data(self, customer_id: int) -> Dict[str, Any]:
        """Generate mock data for Customer 360 when database is unavailable."""
        mock_data = {}
        
        # Mock enrollments - create 3 program enrollments for this customer
        enrolments = []
        programs = ["Piano Lessons", "Guitar Lessons", "Music Theory"]
        for i in range(3):
            start_date = datetime.now() - timedelta(days=180 + i*30)
            enrolments.append({
                'enrolment_id': i + 1,
                'enrolment_date': start_date,
                'program_id': i + 1,
                'program_name': programs[i],
                'customer_id': customer_id,
                'customer_name': f"Student {customer_id}"
            })
        mock_data['enrolments'] = pd.DataFrame(enrolments)
        
        # Mock lessons - create lessons for each enrollment
        lessons = []
        lesson_id = 1
        for enr in enrolments:
            # Create 8 lessons per enrollment
            for i in range(8):
                lesson_date = enr['enrolment_date'] + timedelta(days=7 * (i+1))
                lesson_type = "Private" if i % 3 != 0 else "Group"
                status = "Completed" if lesson_date < datetime.now() else "Scheduled"
                
                lessons.append({
                    'lesson_id': lesson_id,
                    'lesson_date': lesson_date,
                    'lesson_status': status,
                    'lesson_type': lesson_type,
                    'enrolment_id': enr['enrolment_id'],
                    'customer_id': customer_id,
                    'customer_name': f"Student {customer_id}"
                })
                lesson_id += 1
        mock_data['lessons'] = pd.DataFrame(lessons)
        
        # Mock invoices - create monthly invoices
        invoices = []
        invoice_id = 1
        for month in range(6):
            invoice_date = datetime.now() - timedelta(days=30 * (5-month))
            # Link some lessons to this invoice
            month_lessons = [l for l in lessons if 
                              abs((l['lesson_date'] - invoice_date).days) < 30]
            
            if month_lessons:
                amount = len(month_lessons) * 50  # $50 per lesson
                invoices.append({
                    'invoice_id': invoice_id,
                    'invoice_date': invoice_date,
                    'amount': amount,
                    'status': 'Paid' if month < 5 else 'Pending',
                    'account_id': customer_id * 10,
                    'customer_id': customer_id,
                    'customer_name': f"Student {customer_id}",
                    'lesson_id': [l['lesson_id'] for l in month_lessons]
                })
                invoice_id += 1
        mock_data['invoices'] = pd.DataFrame(invoices)
        
        # Mock payments - some payments aligned to cycles, some misaligned
        payments = []
        payment_id = 1
        for inv in invoices:
            # Most payments are on invoice date
            payment_date = inv['invoice_date'] + timedelta(days=2) 
            
            # But some are misaligned across cycle boundaries
            if payment_id % 3 == 0:
                # This payment crosses cycle boundaries (future payment for past invoice)
                payment_date = payment_date + timedelta(days=35)
            
            payments.append({
                'payment_id': payment_id,
                'payment_date': payment_date,
                'amount': inv['amount'],
                'status': 'Completed',
                'invoice_id': inv['invoice_id'],
                'account_id': inv['account_id'],
                'customer_id': customer_id,
                'customer_name': f"Student {customer_id}"
            })
            payment_id += 1
        mock_data['payments'] = pd.DataFrame(payments)
        
        return mock_data

    def get_customer_360_data(self, customer_id: int) -> Dict[str, Any]:
        """
        Returns a dictionary with all relevant data for a customer: enrolments, lessons, invoices, payments.
        """
        self._fetch_data_if_needed()
        try:
            # Fetch data from repository
            enrolments = pd.DataFrame(self.repo.fetch_enrolment_data(customer_id=customer_id))
            lessons = pd.DataFrame(self.repo.fetch_lesson_data(customer_id=customer_id))
            invoices = pd.DataFrame(self.repo.fetch_invoice_data(customer_id=customer_id))
            payments = pd.DataFrame(self.repo.fetch_payment_data(customer_id=customer_id))
            
            # Check if we got any data
            if (enrolments.empty and lessons.empty and invoices.empty and payments.empty):
                self.logger.warning(f"No data found for customer {customer_id}. Using mock data.")
                return self.get_mock_customer_360_data(customer_id)
                
            return {
                'enrolments': enrolments,
                'lessons': lessons,
                'invoices': invoices,
                'payments': payments
            }
        except Exception as e:
            self.logger.error(f"Error fetching customer data: {e}")
            self.logger.info("Falling back to mock data")
            return self.get_mock_customer_360_data(customer_id)

    def create_customer_timeline_plot(self, customer_id: int) -> go.Figure:
        """
        Timeline of enrolments, lessons, invoices, and payments for a customer.
        """
        data = self.get_customer_360_data(customer_id)
        events = []
        for _, row in data['enrolments'].iterrows():
            events.append({'type': 'Enrolment', 'date': row.get('enrolment_date'), 'desc': row.get('program_name')})
        for _, row in data['lessons'].iterrows():
            events.append({'type': 'Lesson', 'date': row.get('lesson_date'), 'desc': row.get('lesson_type')})
        for _, row in data['invoices'].iterrows():
            events.append({'type': 'Invoice', 'date': row.get('invoice_date'), 'desc': f"Amount: {row.get('amount')}"})
        for _, row in data['payments'].iterrows():
            events.append({'type': 'Payment', 'date': row.get('payment_date'), 'desc': f"Amount: {row.get('amount')}"})
        df = pd.DataFrame(events)
        df = df.dropna(subset=['date'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        fig = px.timeline(df, x_start='date', x_end='date', y='type', color='type', hover_data=['desc'])
        fig.update_layout(title=f"Customer {customer_id} Timeline")
        return fig

    def create_workflow_sankey_plot(self, customer_id: int) -> go.Figure:
        """
        Sankey diagram showing flow from enrolments -> lessons -> invoices -> payments for a customer.
        """
        data = self.get_customer_360_data(customer_id)
        sources = []
        targets = []
        values = []
        label_map = {}
        label_list = []
        idx = 0
        # Enrolments -> Lessons
        for _, enr in data['enrolments'].iterrows():
            e_label = f"Enrolment: {enr.get('program_name')}"
            if e_label not in label_map:
                label_map[e_label] = idx
                label_list.append(e_label)
                idx += 1
            for _, les in data['lessons'].iterrows():
                if les.get('enrolment_id') == enr.get('enrolment_id'):
                    l_label = f"Lesson: {les.get('lesson_type')}"
                    if l_label not in label_map:
                        label_map[l_label] = idx
                        label_list.append(l_label)
                        idx += 1
                    sources.append(label_map[e_label])
                    targets.append(label_map[l_label])
                    values.append(1)
        # Lessons -> Invoices
        for _, les in data['lessons'].iterrows():
            l_label = f"Lesson: {les.get('lesson_type')}"
            for _, inv in data['invoices'].iterrows():
                if inv.get('lesson_id') == les.get('lesson_id'):
                    i_label = f"Invoice: {inv.get('invoice_id')}"
                    if i_label not in label_map:
                        label_map[i_label] = idx
                        label_list.append(i_label)
                        idx += 1
                    sources.append(label_map[l_label])
                    targets.append(label_map[i_label])
                    values.append(inv.get('amount', 1))
        # Invoices -> Payments
        for _, inv in data['invoices'].iterrows():
            i_label = f"Invoice: {inv.get('invoice_id')}"
            for _, pay in data['payments'].iterrows():
                if pay.get('invoice_id') == inv.get('invoice_id'):
                    p_label = f"Payment: {pay.get('payment_id')}"
                    if p_label not in label_map:
                        label_map[p_label] = idx
                        label_list.append(p_label)
                        idx += 1
                    sources.append(label_map[i_label])
                    targets.append(label_map[p_label])
                    values.append(pay.get('amount', 1))
        fig = go.Figure(go.Sankey(
            node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5), label=label_list),
            link=dict(source=sources, target=targets, value=values)
        ))
        fig.update_layout(title=f"Customer {customer_id} Business Workflow (Sankey)")
        return fig

    def detect_misapplied_payments(self) -> pd.DataFrame:
        """
        Returns a DataFrame of customers/payments where payments cross billing cycle boundaries (potential misapplication).
        """
        self._fetch_data_if_needed()
        if self.raw_payment_data.empty or self.raw_cycle_data.empty:
            return pd.DataFrame()
        # Example logic: payment_date outside invoice's billing cycle
        merged = pd.merge(self.raw_payment_data, self.raw_cycle_data, on=['invoice_id'], how='left', suffixes=('', '_cycle'))
        misapplied = merged[(merged['payment_date'] < merged['cycle_start']) | (merged['payment_date'] > merged['cycle_end'])]
        return misapplied[['customer_id', 'payment_id', 'payment_date', 'cycle_start', 'cycle_end', 'invoice_id']]

    def simulate_payment_corrections(self, customer_id: int) -> Dict[str, Any]:
        """
        Simulate corrected payment application for a customer (apply only to correct cycle).
        Returns before/after summary.
        """
        data = self.get_customer_360_data(customer_id)
        # This is a stub for demonstration; real logic would reassign payments to correct invoices/cycles
        before = data['payments'].copy()
        after = before.copy()
        # Example: set all payment dates within invoice's cycle
        for idx, row in after.iterrows():
            invoice = data['invoices'][data['invoices']['invoice_id'] == row['invoice_id']]
            if not invoice.empty:
                after.at[idx, 'payment_date'] = invoice.iloc[0].get('invoice_date')
        return {'before': before, 'after': after}

    def get_business_impact_summary(self) -> pd.DataFrame:
        """
        Summarize business impact: e.g., count of misapplied payments, total value, affected customers.
        """
        misapplied = self.detect_misapplied_payments()
        if misapplied.empty:
            return pd.DataFrame({'metric': ['Misapplied Payments', 'Affected Customers', 'Total Value'], 'value': [0, 0, 0]})
        summary = {
            'Misapplied Payments': len(misapplied),
            'Affected Customers': misapplied['customer_id'].nunique(),
            'Total Value': misapplied.get('amount', pd.Series([0]*len(misapplied))).sum()
        }
        return pd.DataFrame({'metric': list(summary.keys()), 'value': list(summary.values())})

    def create_payment_misapplications_summary_dashboard(self) -> Dict[str, Any]:
        """
        Creates a comprehensive summary dashboard showing payment misapplication metrics, 
        affected accounts, and impact.
        """
        try:
            misapplied_payments = self.detect_misapplied_payments()
            
            if misapplied_payments.empty:
                # Use mock data for development
                misapplied_payments = pd.DataFrame({
                    'customer_id': [1, 2, 3, 1, 4, 5, 2, 6, 7, 8],
                    'payment_id': list(range(1, 11)),
                    'payment_date': [(datetime.now() - timedelta(days=x*15)) for x in range(10)],
                    'cycle_start': [(datetime.now() - timedelta(days=30 + x*15)) for x in range(10)],
                    'cycle_end': [(datetime.now() - timedelta(days=x*15)) for x in range(10)],
                    'invoice_id': list(range(101, 111)),
                    'amount': [120, 80, 150, 90, 200, 75, 95, 180, 110, 85],
                })
            
            # Calculate high-level metrics
            metrics = {
                'total_misapplied': len(misapplied_payments),
                'affected_customers': misapplied_payments['customer_id'].nunique(),
                'total_amount': misapplied_payments['amount'].sum() if 'amount' in misapplied_payments.columns else 0,
                'avg_days_misaligned': 0
            }
            
            if 'payment_date' in misapplied_payments.columns and 'cycle_end' in misapplied_payments.columns:
                # Calculate average number of days payments are misaligned
                misapplied_payments['days_misaligned'] = (
                    pd.to_datetime(misapplied_payments['payment_date']) - 
                    pd.to_datetime(misapplied_payments['cycle_end'])
                ).dt.days
                metrics['avg_days_misaligned'] = misapplied_payments['days_misaligned'].mean()
            
            # Top affected customers
            if not misapplied_payments.empty:
                customer_impact = misapplied_payments.groupby('customer_id').agg(
                    payment_count=('payment_id', 'count'),
                    total_amount=('amount', lambda x: x.sum() if 'amount' in misapplied_payments.columns else 0)
                ).reset_index().sort_values('payment_count', ascending=False).head(5)
            else:
                customer_impact = pd.DataFrame()
            
            # Timeline of misapplied payments
            if 'payment_date' in misapplied_payments.columns:
                timeline = misapplied_payments.groupby(
                    pd.to_datetime(misapplied_payments['payment_date']).dt.to_period('M')
                ).size().reset_index()
                timeline.columns = ['month', 'count']
                timeline['month'] = timeline['month'].astype(str)
            else:
                timeline = pd.DataFrame()
            
            # Payment misalignment distribution
            if 'days_misaligned' in misapplied_payments.columns:
                misalignment_bins = [-float('inf'), -30, -15, 0, 15, 30, float('inf')]
                misalignment_labels = ['> 30 days before', '15-30 days before', '0-15 days before', 
                                      '0-15 days after', '15-30 days after', '> 30 days after']
                misapplied_payments['misalignment_category'] = pd.cut(
                    misapplied_payments['days_misaligned'], 
                    bins=misalignment_bins,
                    labels=misalignment_labels
                )
                misalignment_dist = misapplied_payments.groupby('misalignment_category').size().reset_index()
                misalignment_dist.columns = ['category', 'count']
            else:
                misalignment_dist = pd.DataFrame()
                
            # Fix points with impacts
            fix_points = [
                {
                    'id': 1,
                    'description': 'Invoice payment distribution needs billing cycle boundary checks',
                    'file': 'PaymentForm.php',
                    'estimated_line': 373,
                    'impact': 'Prevents future payments from being applied to past cycles'
                },
                {
                    'id': 2,
                    'description': 'Lesson payment distribution needs proper date comparison',
                    'file': 'PaymentForm.php',
                    'estimated_line': 410,
                    'impact': 'Ensures payments are only applied to lessons within the current cycle'
                },
                {
                    'id': 3,
                    'description': 'Group lesson payment distribution needs cycle boundary implementation',
                    'file': 'PaymentForm.php',
                    'estimated_line': 444,
                    'impact': 'Completes boundary enforcement for all payment types'
                }
            ]
            
            return {
                'metrics': metrics,
                'customer_impact': customer_impact,
                'timeline': timeline,
                'misalignment_dist': misalignment_dist,
                'fix_points': fix_points,
                'raw_data': misapplied_payments
            }
            
        except Exception as e:
            self.logger.error(f"Error creating summary dashboard: {e}")
            # Return empty dashboard structure
            return {
                'metrics': {'total_misapplied': 0, 'affected_customers': 0, 'total_amount': 0, 'avg_days_misaligned': 0},
                'customer_impact': pd.DataFrame(),
                'timeline': pd.DataFrame(),
                'misalignment_dist': pd.DataFrame(),
                'fix_points': [],
                'raw_data': pd.DataFrame()
            }

    def get_all_dashboard_generators(self) -> List[Dict[str, Any]]:
        """Returns a list of all available dashboard generator functions and their titles."""
        # This will be expanded as more dashboards are added
        return [
            {"title": "Payment Volume Over Time (Monthly)", "function": lambda: self.create_payment_volume_over_time_plot('M')},
            {"title": "Payment Volume Over Time (Daily)", "function": lambda: self.create_payment_volume_over_time_plot('D')},
            {"title": "Payment Status Distribution", "function": self.create_payment_status_distribution_plot},
            {"title": "Average Payment Value by Method", "function": self.create_average_payment_value_plot},
            {"title": "Payment Method Popularity", "function": self.create_payment_method_popularity_plot},
            {"title": "Total Revenue by Month", "function": self.create_revenue_by_month_plot},
            {"title": "Customer 360 Timeline", "function": lambda: self.create_customer_timeline_plot(1)}, # Example customer ID
            {"title": "Customer Business Workflow (Sankey)", "function": lambda: self.create_workflow_sankey_plot(1)}, # Example customer ID
            {"title": "Misapplied Payments", "function": self.detect_misapplied_payments},
            {"title": "Payment Correction Simulation", "function": lambda: self.simulate_payment_corrections(1)}, # Example customer ID
            {"title": "Business Impact Summary", "function": self.get_business_impact_summary},
            {"title": "Payment Misapplications Summary Dashboard", "function": self.create_payment_misapplications_summary_dashboard},
            # Add more entries here as new dashboard methods are implemented
        ]

# Example usage (for testing)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    service = FinancialDashboardsService()
    
    # Test connection
    conn_test = service.repo.test_connection()
    service.logger.info(f"Database connection test: {conn_test}")

    if conn_test.get("connected"):
        service._fetch_data_if_needed() # Pre-fetch data
        print(f"Payment data head:\n{service.raw_payment_data.head() if not service.raw_payment_data.empty else 'No payment data'}")
        print(f"Cycle data head:\n{service.raw_cycle_data.head() if not service.raw_cycle_data.empty else 'No cycle data'}")

        dashboard_gens = service.get_all_dashboard_generators()
        for i, gen_info in enumerate(dashboard_gens):
            print(f"\nGenerating dashboard {i+1}: {gen_info['title']}")
            try:
                fig = gen_info['function']()
                # fig.show() # Uncomment to display figures if running locally and Plotly Orca is installed or in Jupyter
                print(f"Successfully generated {gen_info['title']}")
            except Exception as e:
                print(f"Error generating {gen_info['title']}: {e}")
    else:
        print("Cannot generate dashboards without a database connection.")
