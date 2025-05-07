#!/usr/bin/env python3
"""
Individual Account Deep Dive (Dashboard 3)

Provides a complete 360-degree view for a single selected customer,
focusing on the interaction of enrollments, lessons, and payments.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any, Tuple

from app.services.financial_dashboards_service import FinancialDashboardsService


class AccountDeepDiveDashboard:
    """
    Dashboard 3: Individual Account Deep Dive
    
    Provides a comprehensive view of a single customer account, including
    enrollments, lessons, payments, and their interactions.
    """
    
    def __init__(self, financial_service: Optional[FinancialDashboardsService] = None):
        """Initialize the dashboard with required services."""
        self.financial_service = financial_service or FinancialDashboardsService()
        
    def run(self):
        """Main entry point for the dashboard."""
        st.title("Individual Account Deep Dive")
        st.markdown("""
        This dashboard provides a comprehensive 360-degree view of a single customer account,
        focusing on the interaction between enrollments, lessons, and payments.
        
        Enter a customer ID to begin the analysis.
        """)
        
        # Customer ID input
        col1, col2 = st.columns([3, 1])
        with col1:
            customer_id = st.text_input("Enter Customer ID")
        
        with col2:
            search_button = st.button("Analyze Account")
        
        if customer_id and search_button:
            # Get customer information
            customer_info = self.financial_service.get_customer_details(customer_id)
            
            if customer_info:
                # Display customer header
                st.header(f"Account Analysis: {customer_info.get('customer_name', f'Customer #{customer_id}')}")
                
                # Customer overview
                self._render_customer_overview(customer_id, customer_info)
                
                # Enrollment summary
                self._render_enrollment_summary(customer_id)
                
                # Lesson timeline
                self._render_lesson_timeline(customer_id)
                
                # Payment allocation ledger
                self._render_payment_allocation_ledger(customer_id)
                
                # "What-If" simulation
                self._render_whatif_simulation(customer_id)
            else:
                st.error(f"No customer found with ID: {customer_id}")
    
    def _render_customer_overview(self, customer_id: str, customer_info: Dict[str, Any]):
        """Render the customer overview section."""
        st.subheader("Customer Overview")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Customer Name", customer_info.get('customer_name', 'N/A'))
            st.markdown(f"**Email:** {customer_info.get('email', 'N/A')}")
        
        with col2:
            st.metric("Account Balance", f"${customer_info.get('balance', 0):.2f}")
            st.markdown(f"**Payment Frequency:** {customer_info.get('payment_frequency', 'N/A')}")
        
        with col3:
            # Get payment statistics
            payment_stats = self.financial_service.get_customer_payment_statistics(customer_id)
            
            st.metric("Total Payments", payment_stats.get('total_payments', 0))
            st.markdown(f"**Total Amount Paid:** ${payment_stats.get('total_amount_paid', 0):.2f}")
        
        # Financial health indicators
        st.subheader("Financial Health Indicators")
        
        risk_indicators = self.financial_service.get_customer_risk_indicators(customer_id)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Payment Issue Risk", 
                f"{risk_indicators.get('payment_issue_risk_score', 0)}/10",
                delta=risk_indicators.get('payment_issue_risk_delta', 0),
                delta_color="inverse"
            )
        
        with col2:
            st.metric(
                "Missed Payments", 
                risk_indicators.get('missed_payments_count', 0),
                delta=risk_indicators.get('missed_payments_delta', 0),
                delta_color="inverse"
            )
        
        with col3:
            st.metric(
                "Misapplied Payments", 
                risk_indicators.get('misapplied_payments_count', 0),
                delta=risk_indicators.get('misapplied_payments_delta', 0),
                delta_color="inverse"
            )
        
        with col4:
            st.metric(
                "Due Date Shifts", 
                risk_indicators.get('due_date_shifts_count', 0),
                delta=risk_indicators.get('due_date_shifts_delta', 0),
                delta_color="inverse"
            )
    
    def _render_enrollment_summary(self, customer_id: str):
        """Render the enrollment summary section."""
        st.subheader("Enrollment Summary")
        
        enrollments = self.financial_service.get_customer_enrollments(customer_id)
        
        if not enrollments.empty:
            # Display enrollment table
            display_df = enrollments[['enrolment_id', 'student_name', 'course_name', 'payment_frequency', 'startDateTime', 'endDateTime', 'isAutoRenew']]
            display_df.columns = ['Enrollment ID', 'Student', 'Course', 'Payment Frequency', 'Start Date', 'End Date', 'Auto-Renew']
            display_df['Auto-Renew'] = display_df['Auto-Renew'].apply(lambda x: "Yes" if x == 1 else "No")
            
            st.dataframe(display_df, use_container_width=True)
            
            # Add enrollment timeline
            fig = px.timeline(
                enrollments,
                x_start='startDateTime',
                x_end='endDateTime',
                y='enrolment_id',
                color='isAutoRenew',
                color_discrete_map={0: 'red', 1: 'green'},
                labels={'enrolment_id': 'Enrollment ID', 'isAutoRenew': 'Auto-Renew'},
                title="Enrollment Timeline",
                hover_data=['student_name', 'course_name', 'payment_frequency']
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No enrollments found for customer #{customer_id}")
    
    def _render_lesson_timeline(self, customer_id: str):
        """Render the interactive lesson timeline section."""
        st.subheader("Lesson Timeline (Interactive)")
        st.markdown("""
        This timeline shows all lessons for the customer's students, color-coded by payment status.
        It also overlays payment dates and draws lines showing which lessons each payment was applied to.
        """)
        
        # Date range selector for timeline
        col1, col2 = st.columns(2)
        with col1:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            start_date_input = st.date_input("Timeline Start Date", value=start_date, key="timeline_start")
        
        with col2:
            end_date_input = st.date_input("Timeline End Date", value=end_date, key="timeline_end")
        
        if start_date_input > end_date_input:
            st.error("Start date must be before end date.")
            return
        
        start_str = start_date_input.strftime('%Y-%m-%d')
        end_str = end_date_input.strftime('%Y-%m-%d')
        
        # Get the data
        with st.spinner("Loading lesson and payment data..."):
            lessons_df, payments_df, payment_allocations = self.financial_service.get_customer_timeline_data(
                customer_id, 
                start_str, 
                end_str
            )
        
        if not lessons_df.empty or not payments_df.empty:
            # Create the visualization
            fig = self._create_timeline_visualization(lessons_df, payments_df, payment_allocations)
            st.plotly_chart(fig, use_container_width=True)
            
            # Add filtering options
            st.subheader("Filter Timeline Data")
            
            col1, col2 = st.columns(2)
            with col1:
                if not lessons_df.empty and 'student_name' in lessons_df.columns:
                    students = ['All'] + sorted(lessons_df['student_name'].unique().tolist())
                    selected_student = st.selectbox("Filter by Student", options=students)
            
            with col2:
                if not lessons_df.empty and 'paid_status' in lessons_df.columns:
                    status_options = ['All', 'Paid', 'Unpaid']
                    selected_status = st.selectbox("Filter by Payment Status", options=status_options)
            
            # Apply filters and update visualization
            filtered_lessons = lessons_df.copy()
            
            if selected_student != 'All':
                filtered_lessons = filtered_lessons[filtered_lessons['student_name'] == selected_student]
            
            if selected_status != 'All':
                is_paid = 1 if selected_status == 'Paid' else 0
                filtered_lessons = filtered_lessons[filtered_lessons['paid_status'] == is_paid]
            
            if selected_student != 'All' or selected_status != 'All':
                updated_fig = self._create_timeline_visualization(filtered_lessons, payments_df, payment_allocations)
                st.plotly_chart(updated_fig, use_container_width=True)
            
            # Display lesson data table
            st.subheader("Lesson Data")
            
            if not filtered_lessons.empty:
                display_df = filtered_lessons[['lesson_id', 'lesson_date', 'due_date', 'student_name', 'lesson_amount', 'paid_status']]
                display_df.columns = ['Lesson ID', 'Lesson Date', 'Due Date', 'Student', 'Amount', 'Paid']
                display_df['Paid'] = display_df['Paid'].apply(lambda x: "Yes" if x == 1 else "No")
                
                st.dataframe(display_df.sort_values('Lesson Date'), use_container_width=True)
            else:
                st.info("No lessons found matching the selected filters.")
        else:
            st.info(f"No lessons or payments found for customer #{customer_id} in the selected date range.")
    
    def _render_payment_allocation_ledger(self, customer_id: str):
        """Render the payment allocation ledger section."""
        st.subheader("Payment Allocation Ledger")
        st.markdown("""
        This ledger shows each payment and how it was allocated to lessons and invoices.
        """)
        
        # Get payment data
        payments = self.financial_service.get_customer_payments(customer_id)
        
        if not payments.empty:
            # Create an expandable section for each payment
            for _, payment in payments.iterrows():
                with st.expander(f"Payment #{payment['payment_id']} - ${payment['amount']:.2f} on {payment['payment_date'].strftime('%Y-%m-%d')}"):
                    # Payment details
                    st.markdown(f"""
                    **Payment Details:**
                    - **Date:** {payment['payment_date'].strftime('%Y-%m-%d')}
                    - **Amount:** ${payment['amount']:.2f}
                    - **Method:** {payment.get('payment_method', 'N/A')}
                    - **Balance Remaining:** ${payment.get('balance', 0):.2f}
                    """)
                    
                    # Lesson payment allocations
                    lesson_allocations = self.financial_service.get_payment_lesson_allocations(payment['payment_id'])
                    
                    if not lesson_allocations.empty:
                        st.markdown("**Lesson Payment Allocations:**")
                        
                        display_df = lesson_allocations[['lesson_id', 'lesson_date', 'applied_amount', 'student_name']]
                        display_df.columns = ['Lesson ID', 'Lesson Date', 'Applied Amount', 'Student']
                        
                        st.dataframe(display_df, use_container_width=True)
                        
                        # Calculate total allocated
                        total_allocated = lesson_allocations['applied_amount'].sum()
                        st.markdown(f"**Total Allocated to Lessons:** ${total_allocated:.2f}")
                    else:
                        st.markdown("**Lesson Payment Allocations:** None")
                    
                    # Invoice payment allocations
                    invoice_allocations = self.financial_service.get_payment_invoice_allocations(payment['payment_id'])
                    
                    if not invoice_allocations.empty:
                        st.markdown("**Invoice Payment Allocations:**")
                        
                        display_df = invoice_allocations[['invoice_id', 'invoice_date', 'applied_amount']]
                        display_df.columns = ['Invoice ID', 'Invoice Date', 'Applied Amount']
                        
                        st.dataframe(display_df, use_container_width=True)
                        
                        # Calculate total allocated
                        total_allocated = invoice_allocations['applied_amount'].sum()
                        st.markdown(f"**Total Allocated to Invoices:** ${total_allocated:.2f}")
                    else:
                        st.markdown("**Invoice Payment Allocations:** None")
        else:
            st.info(f"No payments found for customer #{customer_id}")
    
    def _render_whatif_simulation(self, customer_id: str):
        """Render the "What-If" scenario simulation section."""
        st.subheader("What-If Scenario (Fix Simulation)")
        st.markdown("""
        This section simulates how payment allocations would look if the payment misapplication
        issue were fixed. Select a payment to see how it would be correctly applied.
        """)
        
        # Get payment data
        payments = self.financial_service.get_customer_payments(customer_id)
        
        if not payments.empty:
            # Payment selection
            payment_options = [f"Payment #{row['payment_id']} - ${row['amount']:.2f} on {row['payment_date'].strftime('%Y-%m-%d')}" 
                              for _, row in payments.iterrows()]
            
            selected_payment_option = st.selectbox("Select Payment for Simulation", options=payment_options)
            
            if selected_payment_option:
                # Extract payment ID from selection
                selected_payment_id = int(selected_payment_option.split('#')[1].split(' ')[0])
                
                # Run simulation
                st.markdown("### Simulation Results")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Current Payment Application**")
                    current_applications = self.financial_service.get_current_payment_applications(selected_payment_id)
                    
                    if not current_applications.empty:
                        display_df = current_applications[['lesson_date', 'lesson_due_date', 'applied_amount']]
                        display_df.columns = ['Lesson Date', 'Due Date', 'Applied Amount']
                        st.dataframe(display_df, use_container_width=True)
                    else:
                        st.info("No current payment applications found.")
                
                with col2:
                    st.markdown("**Simulated Correct Application**")
                    expected_applications = self.financial_service.get_expected_payment_applications(selected_payment_id)
                    
                    if not expected_applications.empty:
                        display_df = expected_applications[['lesson_date', 'lesson_due_date', 'applied_amount']]
                        display_df.columns = ['Lesson Date', 'Due Date', 'Applied Amount']
                        st.dataframe(display_df, use_container_width=True)
                    else:
                        st.info("No simulated payment applications generated.")
                
                # Simulated timeline visualization
                st.markdown("### Simulated Timeline Comparison")
                
                if not current_applications.empty or not expected_applications.empty:
                    # Create a combined timeline visualization
                    fig = self._create_simulation_comparison_visualization(
                        current_applications,
                        expected_applications,
                        selected_payment_id
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Insufficient data for timeline visualization.")
                
                # Impact summary
                st.markdown("### Impact Summary")
                
                impact_metrics = self.financial_service.get_payment_correction_impact(selected_payment_id)
                
                if impact_metrics:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "Lessons Newly Paid", 
                            impact_metrics.get('newly_paid_lessons', 0)
                        )
                    
                    with col2:
                        st.metric(
                            "Lessons No Longer Paid", 
                            impact_metrics.get('no_longer_paid_lessons', 0)
                        )
                    
                    with col3:
                        st.metric(
                            "Due Date Corrections", 
                            impact_metrics.get('due_date_corrections', 0)
                        )
                    
                    # Additional impact details
                    if 'impact_description' in impact_metrics:
                        st.markdown("**Impact Description:**")
                        st.markdown(impact_metrics['impact_description'])
                else:
                    st.info("No impact metrics available for this simulation.")
        else:
            st.info(f"No payments found for customer #{customer_id}")
    
    def _create_timeline_visualization(
        self, 
        lessons_df: pd.DataFrame, 
        payments_df: pd.DataFrame, 
        payment_allocations: Dict[int, List[Dict[str, Any]]]
    ) -> go.Figure:
        """Create an interactive timeline visualization of lessons and payments."""
        fig = go.Figure()
        
        # Add lessons as points
        if not lessons_df.empty:
            # Define color map for lesson status
            color_map = {0: 'red', 1: 'green'}
            
            # Add scatter plot for lessons
            fig.add_trace(go.Scatter(
                x=lessons_df['lesson_date'],
                y=lessons_df['lesson_amount'],
                mode='markers',
                marker=dict(
                    size=10,
                    color=[color_map.get(status, 'gray') for status in lessons_df['paid_status']],
                    line=dict(width=1, color='black')
                ),
                name='Lessons',
                text=[f"Lesson #{row['lesson_id']}<br>Date: {row['lesson_date'].strftime('%Y-%m-%d')}<br>Due: {row['due_date'].strftime('%Y-%m-%d')}<br>Amount: ${row['lesson_amount']:.2f}<br>Student: {row['student_name']}<br>Status: {'Paid' if row['paid_status'] == 1 else 'Unpaid'}"
                      for _, row in lessons_df.iterrows()],
                hoverinfo='text'
            ))
        
        # Add payments as vertical lines
        if not payments_df.empty:
            for _, payment in payments_df.iterrows():
                # Add line for payment date
                fig.add_shape(
                    type="line",
                    x0=payment['payment_date'],
                    y0=0,
                    x1=payment['payment_date'],
                    y1=max(lessons_df['lesson_amount'].max() * 1.1, payment['amount'] * 1.1) if not lessons_df.empty else payment['amount'] * 1.1,
                    line=dict(color="blue", width=2, dash="dot"),
                )
                
                # Add annotation for payment
                fig.add_annotation(
                    x=payment['payment_date'],
                    y=max(lessons_df['lesson_amount'].max() * 1.05, payment['amount'] * 1.05) if not lessons_df.empty else payment['amount'] * 1.05,
                    text=f"Payment: ${payment['amount']:.2f}",
                    showarrow=False,
                    yshift=10
                )
                
                # Add connections to allocated lessons
                if payment['payment_id'] in payment_allocations:
                    for allocation in payment_allocations[payment['payment_id']]:
                        # Check if the lesson exists in the lessons_df
                        if 'lesson_id' in allocation and 'lesson_date' in allocation:
                            matching_lessons = lessons_df[lessons_df['lesson_id'] == allocation['lesson_id']]
                            
                            if not matching_lessons.empty:
                                lesson_row = matching_lessons.iloc[0]
                                
                                # Determine if this is a problematic payment application
                                is_problematic = False
                                if 'is_problematic' in allocation:
                                    is_problematic = allocation['is_problematic']
                                else:
                                    # Consider it problematic if payment date is after lesson date by more than 14 days
                                    payment_date = payment['payment_date']
                                    lesson_date = lesson_row['lesson_date']
                                    if (payment_date - lesson_date).days > 14:
                                        is_problematic = True
                                
                                # Add line from payment to lesson
                                fig.add_shape(
                                    type="line",
                                    x0=payment['payment_date'],
                                    y0=payment['amount'] * 0.9,
                                    x1=lesson_row['lesson_date'],
                                    y1=lesson_row['lesson_amount'],
                                    line=dict(
                                        color="red" if is_problematic else "green", 
                                        width=1,
                                        dash="solid" if is_problematic else "dash"
                                    ),
                                )
        
        # Update layout
        fig.update_layout(
            title="Lesson and Payment Timeline",
            xaxis_title="Date",
            yaxis_title="Amount ($)",
            hovermode="closest",
            showlegend=False,
            yaxis=dict(tickprefix='$')
        )
        
        return fig
    
    def _create_simulation_comparison_visualization(
        self,
        current_df: pd.DataFrame,
        expected_df: pd.DataFrame,
        payment_id: int
    ) -> go.Figure:
        """Create a visualization comparing current and expected payment applications."""
        fig = go.Figure()
        
        # Get payment details
        payment_details = self.financial_service.get_payment_details(payment_id)
        payment_date = payment_details.get('payment_date') if payment_details else None
        payment_amount = payment_details.get('amount', 0) if payment_details else 0
        
        # Add current applications as red points
        if not current_df.empty:
            fig.add_trace(go.Scatter(
                x=current_df['lesson_date'],
                y=current_df['applied_amount'],
                mode='markers',
                marker=dict(size=12, color='red'),
                name='Current Application',
                text=[f"Lesson Date: {row['lesson_date'].strftime('%Y-%m-%d')}<br>Due Date: {row['lesson_due_date'].strftime('%Y-%m-%d')}<br>Applied: ${row['applied_amount']:.2f}"
                      for _, row in current_df.iterrows()],
                hoverinfo='text'
            ))
        
        # Add expected applications as blue points
        if not expected_df.empty:
            fig.add_trace(go.Scatter(
                x=expected_df['lesson_date'],
                y=expected_df['applied_amount'],
                mode='markers',
                marker=dict(size=12, color='blue'),
                name='Expected Application',
                text=[f"Lesson Date: {row['lesson_date'].strftime('%Y-%m-%d')}<br>Due Date: {row['lesson_due_date'].strftime('%Y-%m-%d')}<br>Applied: ${row['applied_amount']:.2f}"
                      for _, row in expected_df.iterrows()],
                hoverinfo='text'
            ))
        
        # Add payment date marker
        if payment_date:
            fig.add_shape(
                type="line",
                x0=payment_date,
                y0=0,
                x1=payment_date,
                y1=max(current_df['applied_amount'].max() if not current_df.empty else 0,
                       expected_df['applied_amount'].max() if not expected_df.empty else 0,
                       payment_amount) * 1.1,
                line=dict(color="black", width=2, dash="dash"),
            )
            
            fig.add_annotation(
                x=payment_date,
                y=max(current_df['applied_amount'].max() if not current_df.empty else 0,
                      expected_df['applied_amount'].max() if not expected_df.empty else 0,
                      payment_amount) * 1.05,
                text=f"Payment Date: {payment_date.strftime('%Y-%m-%d')}",
                showarrow=False,
                yshift=10
            )
        
        # Update layout
        fig.update_layout(
            title="Payment Application Comparison: Current vs. Expected",
            xaxis_title="Lesson Date",
            yaxis_title="Amount Applied ($)",
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            yaxis=dict(tickprefix='$')
        )
        
        return fig
