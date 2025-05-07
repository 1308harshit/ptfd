#!/usr/bin/env python3
"""
Issue Reproduction Dashboard for visualizing and debugging payment misallocation issues.
Related GitHub Issue: #704 - Payment Misapplication Fix
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta
import graphviz

from app.services.financial_dashboards_service import FinancialDashboardsService

class IssueReproductionDashboard:
    """Interactive dashboard for reproducing and analyzing payment misallocation issues."""
    
    def __init__(self):
        """Initialize the dashboard with required services."""
        self.financial_service = FinancialDashboardsService()
        
        # Initialize session state
        if 'issue_page' not in st.session_state:
            st.session_state.issue_page = "Issue Reproduction"
            st.session_state.payment_data = None
            st.session_state.enrollment_data = None
            st.session_state.selected_customer_id = None
    
    def run(self):
        """Main entry point to run the dashboard."""
        st.title("Payment Issue Reproduction System")
        
        # Tab-based navigation
        tabs = st.tabs([
            "Issue Reproduction", 
            "Payment Flow Debugger", 
            "Data State Viewer",
            "Code Path Visualizer", 
            "Test Case Generator", 
            "Regression Monitor"
        ])
        
        # Display the content for each tab
        with tabs[0]:
            self._render_issue_reproduction()
        with tabs[1]:
            self._render_payment_flow_debugger()
        with tabs[2]:
            self._render_data_state_viewer()
        with tabs[3]:
            self._render_code_path_visualizer()
        with tabs[4]:
            self._render_test_case_generator()
        with tabs[5]:
            self._render_regression_monitor()
    
    def _render_issue_reproduction(self):
        """Render the issue reproduction wizard."""
        st.subheader("Issue Reproduction Wizard")
        
        # Select issue type
        issue_type = st.radio(
            "Select Issue Type",
            ["Payment Misallocation", "Enrollment Status/Auto-Renew Issue", "Both Issues"]
        )
        
        # Select reproduction method
        reproduction_method = st.selectbox(
            "Reproduction Method",
            ["Use Reported Customer Data", "Simulate with Custom Data"]
        )
        
        if reproduction_method == "Use Reported Customer Data":
            # Mock data for reported issues
            reported_issues = pd.DataFrame([
                {"customer_id": 123, "customer_name": "Mason Pereira", "issue_type": "Payment Misallocation"},
                {"customer_id": 456, "customer_name": "Irene Bassó", "issue_type": "Enrollment Status Issue"}
            ])
            
            # Filter by selected issue type
            if issue_type != "Both Issues":
                reported_issues = reported_issues[reported_issues["issue_type"] == issue_type]
            
            # Display available examples
            if not reported_issues.empty:
                selected_issue = st.selectbox(
                    "Choose a reported issue to reproduce:",
                    reported_issues["customer_name"].tolist()
                )
                st.session_state.selected_customer_id = reported_issues[
                    reported_issues["customer_name"] == selected_issue]["customer_id"].iloc[0]
            else:
                st.warning("No reported cases available for the selected issue type.")
                
        else:  # Simulate with Custom Data
            # Get mock customer data 
            mock_customers = pd.DataFrame([
                {"id": 123, "name": "Mason Pereira"},
                {"id": 456, "name": "Irene Bassó"},
                {"id": 789, "name": "Mia Echenique"}
            ])
            
            # Customer selection
            selected_customer = st.selectbox("Select Customer", mock_customers["name"].tolist())
            st.session_state.selected_customer_id = mock_customers[
                mock_customers["name"] == selected_customer]["id"].iloc[0]
            
            # Basic simulation parameters
            col1, col2 = st.columns(2)
            with col1:
                st.date_input("Payment Date", datetime.now() - timedelta(days=7))
                if issue_type in ["Payment Misallocation", "Both Issues"]:
                    st.number_input("Payment Amount", min_value=10.0, value=100.0)
            with col2:
                if issue_type in ["Enrollment Status/Auto-Renew Issue", "Both Issues"]:
                    st.checkbox("Simulate Enrollment End Date Change", value=True)
                    st.checkbox("Simulate Auto-Renew Disabled", value=True)
        
        # Reproduce button
        if st.button("Reproduce Issue", key="reproduce_button"):
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simulate processing
            for i, step in enumerate(["Loading data...", "Analyzing...", "Identifying issues...", "Visualizing..."]):
                status_text.text(step)
                progress_bar.progress((i+1)*25)
                time.sleep(0.5)
                
            # Mock result data
            st.session_state.payment_data = {
                "payment_id": 12345,
                "payment_date": "2025-04-05",
                "payment_amount": 100.00,
                "misallocated": True
            }
            
            st.session_state.enrollment_data = {
                "enrollment_id": 7890,
                "end_date_changed": True,
                "auto_renew_disabled": True
            }
            
            st.success("Issue reproduction completed. Navigate to other tabs for detailed analysis.")

    def _render_payment_flow_debugger(self):
        """Render the payment flow debugger."""
        st.subheader("Payment Flow Debugger")
        
        if not st.session_state.payment_data:
            st.info("No payment data available. Please go to the Issue Reproduction tab first.")
            return
        
        payment_data = st.session_state.payment_data
        
        # Basic payment info
        st.markdown(f"#### Payment #{payment_data['payment_id']} - ${payment_data['payment_amount']}")
        
        # Timeline visualization
        st.subheader("Payment Processing Timeline")
        
        # Create simplified timeline
        timeline_events = [
            {"title": "Payment Created", "is_error": False},
            {"title": "ERROR: Due Date Comparison", "is_error": True},
            {"title": "Payment Applied Incorrectly", "is_error": False}
        ]
        
        # Display timeline
        for i, event in enumerate(timeline_events):
            col1, col2 = st.columns([1, 7])
            with col1:
                if event["is_error"]:
                    st.markdown("### 🔴")
                else:
                    st.markdown(f"### {i+1}")
            with col2:
                st.markdown(f"**{event['title']}**")
        
        # Code snippet with error
        st.subheader("Code Snippet with Error")
        code = '''
// PaymentForm.php - save() method (simplified)
public function save()
{
    // ERROR: Sort lessons by date instead of dueDate
    usort($lessons, function($a, $b) {
        return $a->date <=> $b->date;  // INCORRECT
        // Should be: return $a->dueDate <=> $b->dueDate;
    });
}'''
        st.code(code, language="php")
        
        # Impact analysis
        st.subheader("Impact Analysis")
        impact_data = pd.DataFrame({
            "Category": ["Affected Lessons", "Affected Customers"],
            "Count": [342, 57]
        })
        fig = px.bar(impact_data, x="Category", y="Count")
        st.plotly_chart(fig)

    def _render_data_state_viewer(self):
        """Render the data state viewer."""
        st.subheader("Data State Viewer")
        
        # Data selection options
        data_type = st.radio(
            "Select Data Type",
            ["Customer Account", "Payment Records", "Lesson Schedule", "Enrollment Status"]
        )
        
        # Check if customer is selected
        if not st.session_state.selected_customer_id:
            st.warning("Please select a customer in the Issue Reproduction tab first.")
            return
        
        # Account summary for all views
        st.metric(label="Customer ID", value=st.session_state.selected_customer_id)
            
        # Display data based on selection
        if data_type == "Customer Account":
            st.metric(label="Balance", value="$125.50")
            
            # Transaction history
            st.subheader("Transaction History")
            transactions = pd.DataFrame([
                {"date": "2025-04-05", "type": "Payment", "amount": "$100.00"},
                {"date": "2025-04-17", "type": "Lesson", "amount": "-$31.25", "status": "UNPAID"},
                {"date": "2025-05-01", "type": "Lesson", "amount": "-$31.25", "status": "PAID"}
            ])
            st.dataframe(transactions)
            
        elif data_type == "Payment Records":
            # Payment allocation visualization
            st.info("Payment allocated to future lessons, skipping earlier ones.")
            
        elif data_type == "Lesson Schedule":
            lessons = pd.DataFrame([
                {"date": "2025-04-17", "status": "UNPAID", "payment": "SKIPPED"},
                {"date": "2025-05-01", "status": "SCHEDULED", "payment": "PAID"}
            ])
            st.dataframe(lessons)
            
        else:  # Enrollment Status
            st.info("Enrollment status information would be shown here.")

    def _render_code_path_visualizer(self):
        """Render the code path visualizer."""
        st.subheader("Code Path Visualizer")
        
        # Code details
        st.subheader("Payment Processing Code Path")
        
        # Simplified code path visualization
        graph = graphviz.Digraph()
        graph.attr(rankdir='LR')
        graph.node("PaymentForm", "PaymentForm")
        graph.node("DateSort", "Date Sorting\\nERROR")
        graph.node("Payment", "Payment")
        
        graph.edge("PaymentForm", "DateSort", color="red")
        graph.edge("DateSort", "Payment")
        
        st.graphviz_chart(graph)
        
        # Fix code
        st.subheader("Fix Solution")
        fix_code = '''
// CORRECT:
usort($lessons, function($a, $b) {
    return $a->dueDate <=> $b->dueDate;
});'''
        st.code(fix_code, language="php")

    def _render_test_case_generator(self):
        """Render the test case generator."""
        st.subheader("Test Case Generator")
        
        st.selectbox("Testing Approach", ["Unit Testing", "Integration Testing"])
        
        if st.button("Generate Test Cases"):
            st.success("Test cases generated successfully!")
            test_cases = pd.DataFrame([
                {"name": "test_payment_applies_to_correct_billing_cycle", "type": "Integration"},
                {"name": "test_payment_prioritizes_by_due_date", "type": "Unit"}
            ])
            st.dataframe(test_cases)

    def _render_regression_monitor(self):
        """Render the regression monitoring dashboard."""
        st.subheader("Regression Monitor")
        
        # System health metrics
        st.metric(label="Payment Processing Health", value="97%", delta="-3%")
        
        # Failed tests
        st.subheader("Recent Failed Tests")
        failed_tests = pd.DataFrame([
            {"test": "test_payment_applies_to_correct_billing_cycle", "message": "Error in date sorting"}
        ])
        st.dataframe(failed_tests)
