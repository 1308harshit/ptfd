#!/usr/bin/env python3
"""
Affected Account Explorer (Dashboard 2)

Lists all accounts potentially affected by the payment misapplication patterns,
allowing drill-down to identify and address issues.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any

from app.services.financial_dashboards_service import FinancialDashboardsService


class AccountExplorerDashboard:
    """
    Dashboard 2: Affected Account Explorer
    
    Lists accounts potentially affected by payment misapplication patterns
    and provides tools to explore the impact on these accounts.
    """
    
    def __init__(self, financial_service: Optional[FinancialDashboardsService] = None):
        """Initialize the dashboard with required services."""
        self.financial_service = financial_service or FinancialDashboardsService()
        
    def run(self):
        """Main entry point for the dashboard."""
        st.title("Affected Account Explorer")
        st.markdown("""
        This dashboard identifies accounts potentially affected by payment misapplication issues
        and allows you to explore the impact on these accounts.
        
        Use the date range selector to narrow down the analysis period.
        """)
        
        # Date range selection
        col1, col2 = st.columns(2)
        with col1:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            start_date_input = st.date_input("Start Date", value=start_date)
        
        with col2:
            end_date_input = st.date_input("End Date", value=end_date)
        
        if start_date_input and end_date_input:
            if start_date_input > end_date_input:
                st.error("Start date must be before end date.")
                return
            
            start_str = start_date_input.strftime('%Y-%m-%d')
            end_str = end_date_input.strftime('%Y-%m-%d')
            
            self._render_affected_customers(start_str, end_str)
            self._render_affected_enrollments(start_str, end_str)
    
    def _render_affected_customers(self, start_date: str, end_date: str):
        """Render the list of affected customers."""
        st.header("Customers with Payment Issues")
        st.markdown("""
        This section identifies customers who have payments applied to lessons in a way that
        suggests potential misapplication across billing cycles.
        """)
        
        with st.spinner("Loading affected customers..."):
            affected_customers = self.financial_service.get_affected_customers(start_date, end_date)
        
        if not affected_customers.empty:
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Affected Customers", len(affected_customers))
            with col2:
                st.metric("Total Suspicious Payments", affected_customers['num_suspicious_payments'].sum())
            with col3:
                st.metric("Avg. Suspicious Payments per Customer", 
                          round(affected_customers['num_suspicious_payments'].mean(), 1))
            
            # Display the data
            st.subheader("Affected Customers List")
            display_df = affected_customers[['user_id', 'firstname', 'lastname', 'num_suspicious_payments']]
            display_df.columns = ['Customer ID', 'First Name', 'Last Name', 'Suspicious Payments Count']
            display_df = display_df.sort_values('Suspicious Payments Count', ascending=False)
            
            # Add a column for viewing customer details
            display_df['View Details'] = display_df['Customer ID'].apply(
                lambda x: f"[View Details](/?customer_id={x})"
            )
            
            st.dataframe(display_df, use_container_width=True)
            
            # Add a histogram of suspicious payments count
            st.subheader("Distribution of Suspicious Payments")
            fig = px.histogram(
                affected_customers, 
                x='num_suspicious_payments',
                nbins=20,
                title="Number of Suspicious Payments per Customer"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Allow searching for a specific customer
            st.subheader("Search for a Specific Customer")
            search_col1, search_col2 = st.columns([3, 1])
            with search_col1:
                search_term = st.text_input("Enter customer name or ID")
            
            with search_col2:
                search_button = st.button("Search")
            
            if search_term and search_button:
                search_results = affected_customers[
                    affected_customers['user_id'].astype(str).str.contains(search_term) |
                    affected_customers['firstname'].str.contains(search_term, case=False) |
                    affected_customers['lastname'].str.contains(search_term, case=False)
                ]
                
                if not search_results.empty:
                    st.subheader("Search Results")
                    display_search = search_results[['user_id', 'firstname', 'lastname', 'num_suspicious_payments']]
                    display_search.columns = ['Customer ID', 'First Name', 'Last Name', 'Suspicious Payments Count']
                    
                    # Add a column for viewing customer details
                    display_search['View Details'] = display_search['Customer ID'].apply(
                        lambda x: f"[View Details](/?customer_id={x})"
                    )
                    
                    st.dataframe(display_search, use_container_width=True)
                else:
                    st.info(f"No customers found matching '{search_term}'.")
        else:
            st.info("No affected customers found in the selected date range.")
    
    def _render_affected_enrollments(self, start_date: str, end_date: str):
        """Render the list of affected enrollments."""
        st.header("Enrollments with Status Issues")
        st.markdown("""
        This section identifies enrollments that may have status issues related to payment
        misapplication, such as incorrect auto-renew status or unexpected end dates.
        """)
        
        with st.spinner("Loading affected enrollments..."):
            affected_enrollments = self.financial_service.get_affected_enrollments(start_date, end_date)
        
        if not affected_enrollments.empty:
            # Display metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Affected Enrollments", len(affected_enrollments))
            with col2:
                auto_renew_count = affected_enrollments[affected_enrollments['isAutoRenew'] == 1].shape[0]
                st.metric("Auto-Renew Enabled", f"{auto_renew_count} ({auto_renew_count / len(affected_enrollments):.0%})")
            
            # Display the data
            st.subheader("Affected Enrollments List")
            display_df = affected_enrollments[['enrolment_id', 'first_name', 'last_name', 'endDateTime', 'isAutoRenew']]
            display_df.columns = ['Enrollment ID', 'Student First Name', 'Student Last Name', 'End Date', 'Auto-Renew']
            display_df['Auto-Renew'] = display_df['Auto-Renew'].apply(lambda x: "Yes" if x == 1 else "No")
            display_df = display_df.sort_values('End Date')
            
            # Add a column for viewing enrollment details
            display_df['View Details'] = display_df['Enrollment ID'].apply(
                lambda x: f"[View Details](/?enrollment_id={x})"
            )
            
            st.dataframe(display_df, use_container_width=True)
            
            # Add a timeline visualization of enrollment end dates
            st.subheader("Enrollment End Date Timeline")
            fig = px.scatter(
                affected_enrollments,
                x='endDateTime',
                y='enrolment_id',
                color='isAutoRenew',
                color_discrete_map={0: 'red', 1: 'green'},
                labels={'endDateTime': 'End Date', 'enrolment_id': 'Enrollment ID', 'isAutoRenew': 'Auto-Renew'},
                title="Enrollment End Dates",
                hover_data=['first_name', 'last_name']
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No affected enrollments found in the selected date range.")
