#!/usr/bin/env python3
"""
SMW Financial Dashboard Application

Main entry point for the Streamlit-based financial dashboard application
focusing on identifying and analyzing payment misapplication issues
across billing cycle boundaries.

Related GitHub Issue: #704
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Ensure the application can import from app package
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

from app.dashboards.payment_visualization import PaymentVisualizationDashboard
from app.dashboards.account_explorer import AccountExplorerDashboard
from app.dashboards.payment_flow_visualization import PaymentFlowVisualizationDashboard
from app.dashboards.auth import Auth
# from app.dashboards.account_deep_dive import AccountDeepDiveDashboard  # Disabled per request

def main():
    """Initialize and run the financial dashboard application."""
    st.set_page_config(
        page_title="SMW Financial Dashboard",
        page_icon="💰",
        layout="wide"
    )
    
    # Check authentication before showing any dashboard
    if not Auth.check_authentication():
        return
    
    # Add a sidebar for navigation between dashboards
    with st.sidebar:
        st.title("SMW Financial Dashboard")
        st.markdown("---")
        
        dashboard_options = {
            "Payment Visualization": "See how payments are applied vs. how they should be applied",
            "Account Explorer": "Identify accounts affected by payment misapplication issues",
            "Payment Flow Visualization": "Interactive D3.js visualization of payment flow patterns",
            "Issue Reproduction System": "Interactive system to reproduce and debug payment issues"
            # "Account Deep Dive": "Get a complete 360° view of a specific customer account" - Disabled per request
        }
        
        selected_dashboard = st.radio(
            "Select Dashboard",
            options=list(dashboard_options.keys())
        )
        
        st.markdown(f"**Description:** {dashboard_options[selected_dashboard]}")
        st.markdown("---")
        st.markdown("**Related:** GitHub Issue [#704](https://github.com/Arcadia-Music-Academy/smw/issues/704) - Payment Misapplication Fix")
        
        # Add logout button
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()
    
    # Display the selected dashboard
    if selected_dashboard == "Payment Visualization":
        dashboard = PaymentVisualizationDashboard()
        dashboard.run()
    elif selected_dashboard == "Account Explorer":
        dashboard = AccountExplorerDashboard()
        dashboard.run()
    elif selected_dashboard == "Payment Flow Visualization":
        dashboard = PaymentFlowVisualizationDashboard()
        dashboard.run()
    elif selected_dashboard == "Issue Reproduction System":
        from app.dashboards.issue_reproduction_dashboard import IssueReproductionDashboard
        dashboard = IssueReproductionDashboard()
        dashboard.run()
    # elif selected_dashboard == "Account Deep Dive":  # Disabled per request
    #     dashboard = AccountDeepDiveDashboard()
    #     dashboard.run()

if __name__ == "__main__":
    main()
