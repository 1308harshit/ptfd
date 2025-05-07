#!/usr/bin/env python3
"""
Payment Misapplication Pattern Visualizer (Dashboard 1)

Provides visualizations to demonstrate how a payment is currently being applied
vs. how it should be applied according to business rules and customer expectations.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from typing import Dict, Optional, List, Any

from app.services.financial_dashboards_service import FinancialDashboardsService


class PaymentVisualizationDashboard:
    """
    Dashboard 1: Payment Misapplication Pattern Visualizer
    
    Visualizes current vs. expected payment flow to help identify and understand 
    misapplication patterns.
    """
    
    def __init__(self, financial_service: Optional[FinancialDashboardsService] = None):
        """Initialize the dashboard with required services."""
        self.financial_service = financial_service or FinancialDashboardsService()
        
    def run(self):
        """Main entry point for the dashboard."""
        st.title("Payment Misapplication Pattern Visualizer")
        st.markdown("""
        This dashboard demonstrates how payments are currently being applied versus how they 
        should be applied according to business rules and customer expectations.
        
        Select a customer and payment to visualize the difference in application patterns.
        """)
        
        # Customer selection
        customers = self.financial_service.get_customers_with_misapplied_payments()
        if not customers.empty:
            selected_customer_id = st.selectbox(
                "Select Customer",
                options=customers['user_id'].tolist(),
                format_func=lambda x: f"{x} - {customers[customers['user_id'] == x]['firstname'].iloc[0]} {customers[customers['user_id'] == x]['lastname'].iloc[0]}"
            )
            
            # Customer overview
            st.subheader("Customer Overview")
            customer_info = self.financial_service.get_customer_details(selected_customer_id)
            if customer_info:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Name:** {customer_info.get('customer_name', 'N/A')}")
                    st.markdown(f"**Email:** {customer_info.get('email', 'N/A')}")
                with col2:
                    st.markdown(f"**Account Balance:** ${customer_info.get('balance', 0):.2f}")
                    st.markdown(f"**Payment Frequency:** {customer_info.get('payment_frequency', 'N/A')}")
            
            # Payment selection
            payments = self.financial_service.get_customer_payments(selected_customer_id)
            if not payments.empty:
                selected_payment_id = st.selectbox(
                    "Select Payment",
                    options=payments['payment_id'].tolist(),
                    format_func=lambda x: f"Payment #{x} - ${payments[payments['payment_id'] == x]['amount'].iloc[0]:.2f} on {payments[payments['payment_id'] == x]['payment_date'].iloc[0].strftime('%Y-%m-%d')}"
                )
                
                self._render_payment_context(selected_payment_id)
                self._render_current_application(selected_payment_id)
                self._render_expected_application(selected_payment_id)
                self._render_discrepancy_analysis(selected_payment_id)
            else:
                st.info("No payments found for this customer.")
        else:
            st.info("No customers with misapplied payments found in the database.")
    
    def _render_payment_context(self, payment_id: int):
        """Render the Payment Context section."""
        st.header("Payment Context")
        
        payment_details = self.financial_service.get_payment_details(payment_id)
        if payment_details:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Payment Date", payment_details.get('payment_date', 'N/A').strftime('%Y-%m-%d') if isinstance(payment_details.get('payment_date'), datetime) else 'N/A')
            with col2:
                st.metric("Payment Amount", f"${payment_details.get('amount', 0):.2f}")
            with col3:
                st.metric("Payment Method", payment_details.get('payment_method', 'N/A'))
            
            # Payment frequency context
            enrolment_details = self.financial_service.get_related_enrolment_details(payment_id)
            if enrolment_details:
                st.markdown(f"""
                **Payment Context:** This payment is part of a **{enrolment_details.get('payment_frequency', 'N/A')}** 
                payment schedule for enrollment #{enrolment_details.get('enrolment_id', 'N/A')}.
                """)
    
    def _render_current_application(self, payment_id: int):
        """Render the Current Application (Buggy) view."""
        st.header("Current Application (Buggy)")
        st.markdown("""
        This section shows how the payment is currently being applied in the system.
        Notice how payments might be applied to lessons outside the expected billing cycle.
        """)
        
        current_applications = self.financial_service.get_current_payment_applications(payment_id)
        if not current_applications.empty:
            # Timeline visualization
            fig = self._create_application_timeline(
                current_applications, 
                payment_id,
                title="Current Payment Application Timeline"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Table view 
            st.subheader("Current Application Details")
            display_df = current_applications[['lesson_date', 'lesson_due_date', 'lesson_amount', 'applied_amount']]
            display_df.columns = ['Lesson Date', 'Lesson Due Date', 'Lesson Amount', 'Applied Amount']
            st.dataframe(display_df, use_container_width=True)
            
            # Highlight potential issues
            future_lessons = current_applications[current_applications['is_future_lesson'] == True]
            if not future_lessons.empty:
                st.warning(f"""
                **Potential Issue Detected:** This payment is being applied to {len(future_lessons)} future lessons 
                (highlighted in red on the timeline) while earlier lessons may be left unpaid.
                """)
        else:
            st.info("No current payment applications found for this payment.")
    
    def _render_expected_application(self, payment_id: int):
        """Render the Expected Application (Simulated) view."""
        st.header("Expected Application (Simulated)")
        st.markdown("""
        This section shows how the payment should be applied according to business rules:
        - Payment should be applied to lessons within the appropriate billing cycle
        - Lessons should be paid in order of due date, then lesson date
        """)
        
        expected_applications = self.financial_service.get_expected_payment_applications(payment_id)
        if not expected_applications.empty:
            # Timeline visualization
            fig = self._create_application_timeline(
                expected_applications,
                payment_id,
                title="Expected Payment Application Timeline",
                is_expected=True
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Table view
            st.subheader("Expected Application Details")
            display_df = expected_applications[['lesson_date', 'lesson_due_date', 'lesson_amount', 'applied_amount']]
            display_df.columns = ['Lesson Date', 'Lesson Due Date', 'Lesson Amount', 'Applied Amount']
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("No expected payment applications could be simulated for this payment.")
    
    def _render_discrepancy_analysis(self, payment_id: int):
        """Render the Discrepancy Analysis section."""
        st.header("Discrepancy Analysis")
        st.markdown("""
        This section highlights the differences between the current and expected payment applications,
        focusing on incorrectly applied payments and due date shifts.
        """)
        
        discrepancies = self.financial_service.get_payment_application_discrepancies(payment_id)
        if discrepancies and discrepancies.get('discrepancy_data') is not None:
            disc_data = discrepancies.get('discrepancy_data')
            
            # Lessons that were paid but shouldn't be
            if 'incorrectly_paid' in disc_data and not disc_data['incorrectly_paid'].empty:
                st.subheader("Lessons Incorrectly Paid by This Payment")
                display_df = disc_data['incorrectly_paid'][['lesson_date', 'lesson_due_date', 'applied_amount']]
                display_df.columns = ['Lesson Date', 'Lesson Due Date', 'Applied Amount']
                st.dataframe(display_df, use_container_width=True)
            
            # Lessons that should be paid but weren't
            if 'should_be_paid' in disc_data and not disc_data['should_be_paid'].empty:
                st.subheader("Lessons That Should Be Paid by This Payment")
                display_df = disc_data['should_be_paid'][['lesson_date', 'lesson_due_date', 'lesson_amount']]
                display_df.columns = ['Lesson Date', 'Lesson Due Date', 'Lesson Amount']
                st.dataframe(display_df, use_container_width=True)
            
            # Due date shifts
            if 'due_date_shifts' in disc_data and not disc_data['due_date_shifts'].empty:
                st.subheader("Due Date Shifts")
                display_df = disc_data['due_date_shifts'][['lesson_date', 'original_due_date', 'new_due_date']]
                display_df.columns = ['Lesson Date', 'Original Due Date', 'New Due Date']
                st.dataframe(display_df, use_container_width=True)
                
                # Visualize due date shifts
                fig = self._create_due_date_shift_visualization(disc_data['due_date_shifts'])
                st.plotly_chart(fig, use_container_width=True)
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Incorrectly Paid Lessons", 
                    len(disc_data.get('incorrectly_paid', pd.DataFrame()))
                )
            with col2:
                st.metric(
                    "Lessons That Should Be Paid", 
                    len(disc_data.get('should_be_paid', pd.DataFrame()))
                )
            with col3:
                st.metric(
                    "Due Date Shifts", 
                    len(disc_data.get('due_date_shifts', pd.DataFrame()))
                )
        else:
            st.info("No discrepancies found between current and expected payment applications.")
    
    def _create_application_timeline(self, df: pd.DataFrame, payment_id: int, title: str, is_expected: bool = False) -> go.Figure:
        """Create a timeline visualization of payment applications."""
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title=title)
            fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Get payment date for reference
        payment_details = self.financial_service.get_payment_details(payment_id)
        payment_date = payment_details.get('payment_date') if payment_details else None
        
        # Create base figure
        fig = go.Figure()
        
        # Add lessons as points
        for _, row in df.iterrows():
            color = 'green' if not row.get('is_future_lesson', False) else 'red'
            if is_expected:
                color = 'blue'  # All expected applications are blue
                
            # Add point for lesson
            fig.add_trace(go.Scatter(
                x=[row['lesson_date']],
                y=[row['lesson_amount']],
                mode='markers',
                marker=dict(size=12, color=color),
                name=f"Lesson on {row['lesson_date'].strftime('%Y-%m-%d')}",
                text=f"Lesson Amount: ${row['lesson_amount']:.2f}<br>Applied: ${row['applied_amount']:.2f}<br>Due Date: {row['lesson_due_date'].strftime('%Y-%m-%d')}",
                hoverinfo='text'
            ))
            
            # Add label
            fig.add_annotation(
                x=row['lesson_date'],
                y=row['lesson_amount'],
                text=f"${row['lesson_amount']:.2f}",
                showarrow=False,
                yshift=15
            )
        
        # Add payment date marker
        if payment_date:
            fig.add_shape(
                type="line",
                x0=payment_date,
                y0=0,
                x1=payment_date,
                y1=max(df['lesson_amount']) * 1.2,
                line=dict(color="black", width=2, dash="dash"),
            )
            
            fig.add_annotation(
                x=payment_date,
                y=max(df['lesson_amount']) * 1.1,
                text=f"Payment Date: {payment_date.strftime('%Y-%m-%d')}",
                showarrow=False,
                yshift=10
            )
        
        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Lesson Date",
            yaxis_title="Amount ($)",
            showlegend=False,
            hovermode="closest"
        )
        
        return fig
    
    def _create_due_date_shift_visualization(self, df: pd.DataFrame) -> go.Figure:
        """Create a visualization of due date shifts."""
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Due Date Shifts")
            fig.add_annotation(text="No due date shifts detected", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        fig = go.Figure()
        
        for idx, row in df.iterrows():
            # Add point for original due date
            fig.add_trace(go.Scatter(
                x=[row['original_due_date']],
                y=[idx],
                mode='markers',
                marker=dict(size=12, color='blue'),
                name=f"Original Due Date: {row['original_due_date'].strftime('%Y-%m-%d')}"
            ))
            
            # Add point for new due date
            fig.add_trace(go.Scatter(
                x=[row['new_due_date']],
                y=[idx],
                mode='markers',
                marker=dict(size=12, color='red'),
                name=f"New Due Date: {row['new_due_date'].strftime('%Y-%m-%d')}"
            ))
            
            # Add line connecting the points
            fig.add_shape(
                type="line",
                x0=row['original_due_date'],
                y0=idx,
                x1=row['new_due_date'],
                y1=idx,
                line=dict(color="gray", width=1)
            )
            
            # Add label
            fig.add_annotation(
                x=row['lesson_date'],
                y=idx,
                text=f"Lesson on {row['lesson_date'].strftime('%Y-%m-%d')}",
                showarrow=False,
                xshift=-120,
                yshift=0
            )
        
        # Update layout
        fig.update_layout(
            title="Due Date Shifts Visualization",
            xaxis_title="Due Date",
            yaxis_title="",
            showlegend=False,
            yaxis=dict(
                showticklabels=False,
                zeroline=False
            )
        )
        
        return fig
