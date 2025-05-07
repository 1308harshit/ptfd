#!/usr/bin/env python3
"""
Financial Dashboard

A Streamlit-based visualization dashboard for the SMW financial system,
focusing on identifying and analyzing payment misapplication issues
across billing cycle boundaries.

Related GitHub Issue: #704
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time
import os
from typing import Dict, Optional

from app.services.payment_visualization_service import PaymentVisualizationService
from app.services.financial_dashboards_service import FinancialDashboardsService

class PaymentDashboard:
    """
    Streamlit dashboard for visualizing payment misapplication issues.
    Uses mock data for local development to remove authentication requirements.
    """
    
    def __init__(self):
        """Initialize the dashboard with required services."""
        self.viz_service = PaymentVisualizationService()
        self.financial_service = FinancialDashboardsService()
        
        # Initialize session state if not exists
        if 'selected_view' not in st.session_state:
            st.session_state.selected_view = "payment_misapplications_summary"
            st.session_state.date_range = None
            st.session_state.selected_account = None
    
    def render_navigation(self):
        """Render the navigation sidebar."""
        with st.sidebar:
            st.title("Navigation")
            
            # View selection
            view_options = [
                "Payment Misapplications Summary",  
                "Overview",
                "Payment Flow Analysis",
                "Account Risk Assessment",
                "Account Details",
                "Billing Cycle Heatmap",
                "Customer Journey Map",
                "Domain Relationship Map",
                # New Advanced Financial Dashboards  
                "Customer 360 Timeline", 
                "Customer Business Workflow", 
                "Misapplied Payments Overview", 
                "Payment Correction Simulation", 
                "Business Impact Summary"
            ]
            
            selected_view = st.radio("Select View", view_options)
            st.session_state.selected_view = selected_view.lower().replace(" ", "_")
            
            # Date range selection (for applicable views)
            if st.session_state.selected_view in ["overview", "payment_flow_analysis", "billing_cycle_heatmap"]:
                st.subheader("Date Range")
                
                end_date = datetime.now()
                start_date = end_date - timedelta(days=90)
                
                date_range = st.date_input(
                    "Select date range",
                    value=(start_date, end_date),
                    key="date_input"
                )
                
                if len(date_range) == 2:
                    st.session_state.date_range = date_range
            
            # Customer ID input for relevant views
            if st.session_state.selected_view in ["customer_360_timeline", "customer_business_workflow", "payment_correction_simulation"]:
                st.session_state.customer_id = st.number_input(
                    "Enter Customer ID", 
                    value=st.session_state.get('customer_id', 1), 
                    min_value=1
                )
            
            # Account selection (for account details view)
            if st.session_state.selected_view == "account_details":
                st.subheader("Account Selection")
                
                account_id = st.text_input("Enter Account ID", value="ACC0100")
                if account_id:
                    st.session_state.selected_account = account_id
                    
                    search_btn = st.button("Search Account")
                    if search_btn:
                        st.experimental_rerun()
            
            # Development note
            st.markdown("---")
            st.info("Development Mode: Using mock data")
    
    def render_overview(self):
        """Render the overview dashboard page."""
        st.title("Financial System Overview")
        st.markdown("""
        This dashboard provides visibility into payment distribution across billing cycles,
        helping identify potential misapplication issues where payments intended for future
        cycles are incorrectly applied to past billing cycles.
        """)
        
        if st.session_state.date_range and len(st.session_state.date_range) == 2:
            start_date, end_date = st.session_state.date_range
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            # Get data for the selected date range
            with st.spinner("Loading data..."):
                cross_cycle_df = self.viz_service.get_cross_cycle_payments(start_str, end_str)
                distribution_df = self.viz_service.get_payment_distribution_by_cycle(start_str, end_str)
                at_risk_df = self.viz_service.get_at_risk_accounts()
            
            # Display summary metrics
            st.header("Payment Misapplication Summary")
            
            metrics_cols = st.columns(4)
            with metrics_cols[0]:
                st.metric(
                    "Misapplied Payments", 
                    len(cross_cycle_df) if not cross_cycle_df.empty else 0
                )
            
            with metrics_cols[1]:
                st.metric(
                    "Amount Misapplied", 
                    f"${cross_cycle_df['amount'].sum():.2f}" if not cross_cycle_df.empty else "$0.00"
                )
            
            with metrics_cols[2]:
                st.metric(
                    "Affected Accounts", 
                    cross_cycle_df['account_id'].nunique() if not cross_cycle_df.empty else 0
                )
            
            with metrics_cols[3]:
                st.metric(
                    "At-Risk Accounts", 
                    len(at_risk_df) if not at_risk_df.empty else 0
                )
            
            # Display payment flow diagram
            st.header("Payment Flow Visualization")
            flow_fig = self.viz_service.create_payment_flow_diagram(cross_cycle_df)
            st.plotly_chart(flow_fig, use_container_width=True)
            
            # Display payment timeline
            st.header("Payment Timing Analysis")
            timeline_fig = self.viz_service.create_payment_timeline(cross_cycle_df)
            st.plotly_chart(timeline_fig, use_container_width=True)
            
            # Display affected accounts table
            st.header("Top Affected Accounts")
            
            if not cross_cycle_df.empty:
                account_df = cross_cycle_df.groupby('account_id').agg({
                    'payment_id': 'count',
                    'amount': 'sum',
                    'customer_name': 'first'
                }).reset_index()
                
                account_df.columns = ['Account ID', 'Customer', 'Misapplied Count', 'Total Amount']
                account_df = account_df.sort_values('Total Amount', ascending=False)
                
                st.dataframe(account_df.head(10), use_container_width=True)
                
                if len(account_df) > 10:
                    st.write(f"... and {len(account_df) - 10} more accounts")
            else:
                st.info("No misapplied payments found in the selected date range.")
        else:
            st.info("Please select a date range in the sidebar to view payment data.")
    
    def render_payment_flow_analysis(self):
        """Render the payment flow analysis page."""
        st.title("Payment Flow Analysis")
        
        if st.session_state.date_range and len(st.session_state.date_range) == 2:
            start_date, end_date = st.session_state.date_range
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            # Get data for the selected date range
            with st.spinner("Loading data..."):
                cross_cycle_df = self.viz_service.get_cross_cycle_payments(start_str, end_str)
            
            # Display payment flow diagram with detailed explanation
            st.header("Cross-Cycle Payment Flow")
            st.markdown("""
            This Sankey diagram visualizes how payments are flowing between billing cycles.
            Each node represents a billing cycle, and the flows show how payments from one cycle
            are being applied to invoices in different cycles.
            
            **Problem Indicators:**
            - Flows from recent cycles to older cycles indicate payments intended for future
              lessons being applied to past invoices
            - Large flows between distant cycles suggest systematic misapplication
            """)
            
            flow_fig = self.viz_service.create_payment_flow_diagram(cross_cycle_df)
            st.plotly_chart(flow_fig, use_container_width=True)
            
            # Display detailed data table
            st.header("Detailed Cross-Cycle Payments")
            
            if not cross_cycle_df.empty:
                # Add a calculated column for months between payment and invoice
                display_df = cross_cycle_df.copy()
                display_df['payment_date'] = pd.to_datetime(display_df['payment_date'])
                display_df['invoice_date'] = pd.to_datetime(display_df['invoice_date'])
                
                display_df['months_between'] = ((display_df['payment_yearmonth'] // 100) * 12 + (display_df['payment_yearmonth'] % 100)) - \
                                              ((display_df['invoice_yearmonth'] // 100) * 12 + (display_df['invoice_yearmonth'] % 100))
                
                # Filter and display columns
                display_cols = [
                    'payment_id', 'account_id', 'customer_name', 
                    'payment_date', 'invoice_date', 'amount',
                    'months_between'
                ]
                
                st.dataframe(display_df[display_cols], use_container_width=True)
                
                # Export option
                export_csv = st.download_button(
                    label="Export to CSV",
                    data=display_df[display_cols].to_csv(index=False),
                    file_name=f"cross_cycle_payments_{start_str}_to_{end_str}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No cross-cycle payments found in the selected date range.")
        else:
            st.info("Please select a date range in the sidebar to view payment flow analysis.")
    
    def render_account_risk_assessment(self):
        """Render the account risk assessment page."""
        st.title("Account Risk Assessment")
        st.markdown("""
        This page identifies accounts that are at higher risk of payment misapplication
        based on their payment patterns and enrollment history.
        
        **Risk Factors:**
        - Multiple active enrollments
        - Early-month payment patterns
        - History of cross-cycle payments
        """)
        
        # Get at-risk accounts
        with st.spinner("Analyzing account risk factors..."):
            at_risk_df = self.viz_service.get_at_risk_accounts()
        
        if not at_risk_df.empty:
            # Display risk score distribution
            st.header("Risk Score Distribution")
            
            fig = px.histogram(
                at_risk_df,
                x="risk_score",
                nbins=20,
                title="Distribution of Risk Scores"
            )
            
            fig.update_layout(
                xaxis_title="Risk Score (higher = more risk)",
                yaxis_title="Number of Accounts"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display at-risk accounts table
            st.header("At-Risk Accounts")
            
            display_cols = [
                'account_id', 'customer_name', 'enrollment_count',
                'payment_count', 'avg_day_of_month', 'risk_score'
            ]
            
            # Sort by risk score descending
            sorted_df = at_risk_df.sort_values('risk_score', ascending=False)
            
            st.dataframe(sorted_df[display_cols], use_container_width=True)
            
            # Export option
            export_csv = st.download_button(
                label="Export to CSV",
                data=sorted_df[display_cols].to_csv(index=False),
                file_name=f"at_risk_accounts_{datetime.now().strftime('%Y-%m-%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No at-risk accounts identified in the analysis.")
    
    def render_account_details(self):
        """Render the account details page."""
        st.title("Account Payment Details")
        
        if st.session_state.selected_account:
            account_id = st.session_state.selected_account
            
            # Get account details
            with st.spinner(f"Loading account data for {account_id}..."):
                account_data = self.viz_service.get_account_detail(account_id)
            
            if account_data.get("error"):
                st.error(account_data["error"])
                return
            
            # Display account info
            st.header("Account Information")
            
            info_cols = st.columns(2)
            with info_cols[0]:
                st.markdown(f"**Account ID:** {account_data['account_info']['account_id']}")
                st.markdown(f"**Customer:** {account_data['account_info']['first_name']} {account_data['account_info']['last_name']}")
                st.markdown(f"**Email:** {account_data['account_info']['email']}")
            
            with info_cols[1]:
                st.markdown(f"**Enrollments:** {account_data['account_info']['enrollment_count']}")
                st.markdown(f"**Total Payments:** {account_data['total_payments']}")
                st.markdown(f"**Misapplied Payments:** {account_data['total_misapplied']}")
            
            # Payment history
            st.header("Payment History")
            
            payment_history = account_data["payment_history"]
            if payment_history:
                payment_df = pd.DataFrame(payment_history)
                payment_df['payment_date'] = pd.to_datetime(payment_df['payment_date'])
                
                # Format for display
                payment_df = payment_df.sort_values('payment_date', ascending=False)
                
                st.dataframe(payment_df, use_container_width=True)
            else:
                st.info("No payment history found for this account.")
            
            # Cross-cycle payments
            st.header("Cross-Cycle Payments")
            
            cross_cycle = account_data["cross_cycle_payments"]
            if cross_cycle:
                cross_df = pd.DataFrame(cross_cycle)
                cross_df['payment_date'] = pd.to_datetime(cross_df['payment_date'])
                cross_df['invoice_date'] = pd.to_datetime(cross_df['invoice_date'])
                
                # Calculate months between
                cross_df['months_between'] = ((cross_df['payment_yearmonth'] // 100) * 12 + (cross_df['payment_yearmonth'] % 100)) - \
                                            ((cross_df['invoice_yearmonth'] // 100) * 12 + (cross_df['invoice_yearmonth'] % 100))
                
                # Format for display
                cross_df = cross_df.sort_values('payment_date', ascending=False)
                
                st.dataframe(cross_df, use_container_width=True)
                
                # Export option
                export_csv = st.download_button(
                    label="Export to CSV",
                    data=cross_df.to_csv(index=False),
                    file_name=f"account_{account_id}_cross_cycle_payments.csv",
                    mime="text/csv"
                )
                
                st.warning(f"This account has {len(cross_df)} payments that were misapplied across billing cycles.")
            else:
                st.success("No cross-cycle payment issues found for this account.")
        else:
            st.info("Please enter an Account ID in the sidebar to view account details.")
    
    def render_billing_cycle_heatmap(self):
        """Render the billing cycle heatmap page."""
        st.title("Billing Cycle Boundary Analysis")
        st.markdown("""
        This heatmap visualization shows payment distribution across billing cycle boundaries.
        It provides a clear view of Fix Point #1 - invoice payment distribution across cycles.
        
        **How to interpret:**
        - The diagonal shows payments made and applied in the same cycle (correct)
        - Above diagonal: Prepayments applied to future cycles
        - Below diagonal: Payments applied to past cycles (potential misapplication)
        """)
        
        if st.session_state.date_range and len(st.session_state.date_range) == 2:
            start_date, end_date = st.session_state.date_range
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            # Get data for the selected date range
            with st.spinner("Loading data..."):
                cross_cycle_df = self.viz_service.get_cross_cycle_payments(start_str, end_str)
            
            # Display billing cycle heatmap
            st.header("Payment Distribution Across Billing Cycles")
            heatmap_fig = self.viz_service.create_billing_cycle_heatmap(cross_cycle_df)
            st.plotly_chart(heatmap_fig, use_container_width=True)
            
            # Display explanation
            st.subheader("Understanding the Fix")
            st.markdown("""
            The payment misapplication issue (GitHub issue #704) occurs when payments intended for future 
            lessons are incorrectly applied to past billing cycles. This causes problems because:
            
            1. Customers expect their payments to be applied to future lessons
            2. The system's current behavior creates confusion about which invoices are paid
            3. It can lead to incorrect financial reporting
            
            The fix will enforce proper billing cycle boundaries by checking payment and invoice dates before applying payments.
            """)
        else:
            st.info("Please select a date range in the sidebar to view the billing cycle heatmap.")
    
    def render_customer_journey_map(self):
        """Render the customer journey map visualization."""
        st.title("Customer Experience Impact")
        st.markdown("""
        This visualization translates technical payment boundary issues into customer experience impacts.
        It shows how payment misapplication affects different stages of the customer journey, highlighting
        the business value of fixing the boundary issues identified in GitHub issue #704.
        
        **Key Insights:**
        - Balance Check is the critical pain point where customers experience the most frustration
        - Major misapplication issues can lead to poor customer support experiences
        - Correct payment application maintains a consistently positive customer experience
        """)
        
        # Create and display the customer journey map
        with st.spinner("Generating customer journey visualization..."):
            journey_fig = self.viz_service.create_customer_journey_map()
            st.plotly_chart(journey_fig, use_container_width=True)
        
        # Business impact explanation
        st.header("Business Impact")
        cols = st.columns(3)
        
        with cols[0]:
            st.metric("Customer Satisfaction Impact", "↓ 58%", "-3.8 points")
            st.markdown("""
            Misapplied payments directly impact customer satisfaction during invoice review and balance checks.
            """)
        
        with cols[1]:
            st.metric("Support Call Volume", "↑ 42%", "+87 calls/month")
            st.markdown("""
            Payment boundary issues drive increased support call volume as customers question their balances.
            """)
            
        with cols[2]:
            st.metric("Retention Risk", "↑ 23%", "+12% churn potential")
            st.markdown("""
            Accounts with multiple misapplied payments show significantly higher churn risk.
            """)
    
    def render_domain_relationship_map(self):
        """Render the domain relationship visualization."""
        st.title("Financial System Domain Context Map")
        st.markdown("""
        This domain context map visualizes how the financial system interacts with other business domains
        in the SMW application. It highlights the boundaries and relationships that must be respected
        to ensure proper payment application across billing cycles.
        
        **Key Domain Boundaries:**
        - Payments must respect billing cycle boundaries
        - Invoices must be properly linked to lessons
        - Enrollments define the customer relationship context
        """)
        
        # Create and display the domain relationship map
        with st.spinner("Generating domain relationship visualization..."):
            domain_fig = self.viz_service.create_domain_relationship_map()
            st.plotly_chart(domain_fig, use_container_width=True)
        
        # Domain boundary explanation
        st.header("Domain Boundaries Implementation")
        st.markdown("""
        ### Fix Points in Domain Context
        
        The three fix points from GitHub issue #704 map to key domain boundaries:
        
        1. **Fix Point #1: Invoice payment distribution**
           - Domain Boundary: Payment ➔ Billing Cycle
           - Implementation: Validate payment date against invoice billing cycle
        
        2. **Fix Point #2: Lesson payment distribution**
           - Domain Boundary: Invoice ➔ Lesson
           - Implementation: Proper date comparison for lesson payment allocation
        
        3. **Fix Point #3: Group lesson payment distribution**
           - Domain Boundary: Lesson ➔ Enrollment
           - Implementation: Respect enrollment cycle periods for group lessons
        
        This domain-driven approach ensures that each business capability has clear boundaries,
        improving maintainability and making the business rules explicit in the code.
        """)
    
    def render_customer_360_timeline(self):
        """Render the customer 360 timeline page."""
        customer_id = st.session_state.get('customer_id', 1)
        st.header(f"Customer {customer_id} Timeline")
        try:
            fig = self.financial_service.create_customer_timeline_plot(customer_id)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error generating timeline: {e}")
            st.info("Make sure the database connection is working and the specified customer exists.")

    def render_customer_business_workflow(self):
        """Render the customer business workflow page."""
        customer_id = st.session_state.get('customer_id', 1)
        st.header(f"Customer {customer_id} Business Workflow (Sankey)")
        try:
            fig = self.financial_service.create_workflow_sankey_plot(customer_id)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error generating Sankey: {e}")
            st.info("Make sure the database connection is working and the specified customer exists.")

    def render_misapplied_payments_overview(self):
        """Render the misapplied payments overview page."""
        st.header("Misapplied Payments Overview")
        try:
            df_misapplied = self.financial_service.detect_misapplied_payments()
            if not df_misapplied.empty:
                st.dataframe(df_misapplied)
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Misapplied Payments", len(df_misapplied))
                with col2:
                    st.metric("Affected Customers", df_misapplied['customer_id'].nunique())
                with col3:
                    total_amount = df_misapplied['amount'].sum() if 'amount' in df_misapplied.columns else "N/A"
                    st.metric("Total Amount", f"${total_amount:,.2f}" if isinstance(total_amount, (int, float)) else total_amount)
            else:
                st.info("No misapplied payments detected or data not available.")
        except Exception as e:
            st.error(f"Error detecting misapplied payments: {e}")
            st.info("This could be due to database connection issues or missing cycle data.")

    def render_payment_correction_simulation(self):
        """Render the payment correction simulation page."""
        customer_id = st.session_state.get('customer_id', 1)
        st.header(f"Payment Correction Simulation for Customer {customer_id}")
        try:
            simulation_data = self.financial_service.simulate_payment_corrections(customer_id)
            
            # Split the screen for before/after comparison
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Payments Before Correction")
                st.dataframe(simulation_data.get('before', pd.DataFrame()))
            
            with col2:
                st.subheader("Payments After Correction")
                st.dataframe(simulation_data.get('after', pd.DataFrame()))
            
            # Impact analysis if we have both before and after data
            before = simulation_data.get('before', pd.DataFrame())
            after = simulation_data.get('after', pd.DataFrame())
            if not before.empty and not after.empty:
                st.subheader("Simulation Impact Analysis")
                st.markdown("This shows how fixing the payment misapplication issue affects customer balance and payment distribution.")
        except Exception as e:
            st.error(f"Error running simulation: {e}")
            st.info("Make sure the database connection is working and the specified customer exists.")

    def render_business_impact_summary(self):
        """Render the business impact summary page."""
        st.header("Business Impact Summary of Misapplied Payments")
        try:
            df_impact = self.financial_service.get_business_impact_summary()
            
            # Display impact metrics in a more visual way
            for idx, row in df_impact.iterrows():
                metric = row['metric']
                value = row['value']
                if metric == "Total Value" and isinstance(value, (int, float)):
                    value = f"${value:,.2f}"
                st.metric(label=metric, value=value)
            
            st.subheader("Detailed Impact")
            st.dataframe(df_impact)
            
            st.markdown("""
            ### Root Cause
            Payment distribution logic doesn't respect billing cycle boundaries, applying future payments to past cycles.
            
            ### Fix Points
            1. Invoice payment distribution needs billing cycle boundary checks
            2. Lesson payment distribution needs proper date comparison
            3. Group lesson payment distribution needs cycle boundary implementation
            """)
        except Exception as e:
            st.error(f"Error generating impact summary: {e}")
            st.info("This could be due to database connection issues or missing data.")

    def render_payment_misapplications_summary(self):
        """Render the main payment misapplications summary dashboard."""
        st.header("Payment Misapplications Summary Dashboard")
        
        try:
            # Get the summary data
            summary_data = self.financial_service.create_payment_misapplications_summary_dashboard()
            
            # Display high-level metrics
            metrics = summary_data.get('metrics', {})
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Misapplied Payments", metrics.get('total_misapplied', 0))
            with col2:
                st.metric("Affected Customers", metrics.get('affected_customers', 0))
            with col3:
                st.metric("Total Amount", f"${metrics.get('total_amount', 0):,.2f}")
            with col4:
                st.metric("Avg Days Misaligned", f"{metrics.get('avg_days_misaligned', 0):.1f}")
            
            # Tabs for different sections
            tab1, tab2, tab3, tab4 = st.tabs(["Customer Impact", "Timeline", "Fix Points", "Raw Data"])
            
            with tab1:
                st.subheader("Most Affected Customers")
                customer_impact = summary_data.get('customer_impact', pd.DataFrame())
                if not customer_impact.empty:
                    # Create a bar chart for customer impact
                    fig = px.bar(
                        customer_impact, 
                        x='customer_id', 
                        y='payment_count',
                        hover_data=['total_amount'],
                        labels={'payment_count': 'Number of Misapplied Payments', 'customer_id': 'Customer ID'},
                        title='Top Customers with Misapplied Payments'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(customer_impact)
                else:
                    st.info("No customer impact data available.")
                    
                # Show misalignment distribution
                st.subheader("Payment Misalignment Distribution")
                misalignment_dist = summary_data.get('misalignment_dist', pd.DataFrame())
                if not misalignment_dist.empty:
                    fig = px.bar(
                        misalignment_dist,
                        x='category',
                        y='count',
                        labels={'count': 'Number of Payments', 'category': 'Misalignment Category'},
                        title='Distribution of Payment Misalignments'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No misalignment distribution data available.")
            
            with tab2:
                st.subheader("Timeline of Misapplied Payments")
                timeline = summary_data.get('timeline', pd.DataFrame())
                if not timeline.empty:
                    fig = px.line(
                        timeline,
                        x='month',
                        y='count',
                        labels={'count': 'Number of Misapplied Payments', 'month': 'Month'},
                        title='Misapplied Payments Over Time'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No timeline data available.")
            
            with tab3:
                st.subheader("Fix Points")
                fix_points = summary_data.get('fix_points', [])
                if fix_points:
                    for fix in fix_points:
                        with st.expander(f"Fix Point #{fix.get('id')}: {fix.get('description')}"):
                            st.markdown(f"""
                            **File:** `{fix.get('file')}`  
                            **Line:** ~{fix.get('estimated_line')}  
                            **Impact:** {fix.get('impact')}
                            """)
                else:
                    st.info("No fix points identified.")
                
                st.subheader("Root Cause Analysis")
                st.markdown("""
                ### Payment Misapplication Root Cause

                The current payment distribution logic doesn't respect billing cycle boundaries:
                
                1. **Invoice payment distribution** (PaymentForm.php, line ~373)
                   - Problem: Payments from future cycles can be applied to past invoices
                   - Fix: Implement billing cycle boundary checks
                
                2. **Lesson payment distribution** (PaymentForm.php, line ~410)
                   - Problem: Incorrect date comparison allows cross-cycle payments
                   - Fix: Proper date comparison with billing cycle context
                
                3. **Group lesson payment distribution** (PaymentForm.php, line ~444)
                   - Problem: Missing cycle boundary check for group lessons
                   - Fix: Implement consistent cycle boundary handling
                
                The combined effect creates accounting inconsistencies where future payments are
                incorrectly applied to past billing periods, affecting customer balances and
                financial reporting accuracy.
                """)
            
            with tab4:
                st.subheader("Raw Misapplied Payments Data")
                raw_data = summary_data.get('raw_data', pd.DataFrame())
                if not raw_data.empty:
                    st.dataframe(raw_data)
                else:
                    st.info("No raw data available.")
        
        except Exception as e:
            st.error(f"Error rendering payment misapplications summary: {e}")
            st.info("This could be due to database connection issues or missing data.")

    def run(self):
        """
        Main entry point to run the Streamlit dashboard.
        This sets up the page and calls the appropriate render methods.
        """
        st.set_page_config(
            page_title="SMW Financial Dashboard",
            page_icon="💰",
            layout="wide"
        )
        
        # Add CSS styling
        st.markdown("""
        <style>
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        h1, h2, h3 {
            margin-top: 0.5rem;
            margin-bottom: 1rem;
        }
        .stMetric {
            background-color: rgba(28, 131, 225, 0.1);
            padding: 10px;
            border-radius: 5px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Render the top banner with app name and mode indicator
        st.markdown("""
        <h1 style='text-align: center;'>SMW Financial Dashboard</h1>
        <p style='text-align: center; color: #ff9f00; font-weight: bold;'>Development Mode - Using Mock Data</p>
        """, unsafe_allow_html=True)
        
        # Render the navigation sidebar
        self.render_navigation()
        
        # Render the appropriate content based on the selected view
        if st.session_state.selected_view == "overview":
            self.render_overview()
        elif st.session_state.selected_view == "payment_flow_analysis":
            self.render_payment_flow_analysis()
        elif st.session_state.selected_view == "account_risk_assessment":
            self.render_account_risk_assessment()
        elif st.session_state.selected_view == "account_details":
            self.render_account_details()
        elif st.session_state.selected_view == "billing_cycle_heatmap":
            self.render_billing_cycle_heatmap()
        elif st.session_state.selected_view == "customer_journey_map":
            self.render_customer_journey_map()
        elif st.session_state.selected_view == "domain_relationship_map":
            self.render_domain_relationship_map()
        elif st.session_state.selected_view == "customer_360_timeline":
            self.render_customer_360_timeline()
        elif st.session_state.selected_view == "customer_business_workflow":
            self.render_customer_business_workflow()
        elif st.session_state.selected_view == "misapplied_payments_overview":
            self.render_misapplied_payments_overview()
        elif st.session_state.selected_view == "payment_correction_simulation":
            self.render_payment_correction_simulation()
        elif st.session_state.selected_view == "business_impact_summary":
            self.render_business_impact_summary()
        elif st.session_state.selected_view == "payment_misapplications_summary":
            self.render_payment_misapplications_summary()
        else:
            st.header("Overview")
            self.render_overview()

def main():
    """Entry point for the dashboard."""
    dashboard = PaymentDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()
