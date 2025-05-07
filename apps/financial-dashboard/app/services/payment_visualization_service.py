#!/usr/bin/env python3
"""
Payment Visualization Service

This service handles the data retrieval and processing for payment visualizations,
specifically focused on billing cycle boundary issues.

Related GitHub Issue: #704
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import text

from app.repositories.legacy_repository import LegacyDatabaseRepository, DatabaseConfig
from app.services.mock_data_service import MockDataService

class PaymentVisualizationService:
    """
    Service for analyzing and visualizing payment distributions with focus on
    billing cycle boundaries.
    """
    
    def __init__(self, use_mock_data: bool = False):
        """Initialize the service with repository access."""
        self.use_mock_data = use_mock_data
        if not use_mock_data:
            config = DatabaseConfig()
            self.repository = LegacyDatabaseRepository(config)
        else:
            self.mock_service = MockDataService()
    
    def execute_query(self, query: str, params: List = None) -> List[Dict]:
        """Execute a raw SQL query and return the results as a list of dictionaries."""
        if self.use_mock_data:
            # Return mock data based on the query
            return []
        
        with self.repository.connection() as conn:
            if params:
                result = conn.execute(text(query), params)
            else:
                result = conn.execute(text(query))
            
            # Convert result to list of dictionaries
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result]
    
    def get_cross_cycle_payments(self, start_date=None, end_date=None) -> pd.DataFrame:
        """
        Get payments that have been applied across billing cycle boundaries.
        
        Args:
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
            
        Returns:
            DataFrame containing payments applied across billing cycles
        """
        query = """
        SELECT 
            p.id AS payment_id,
            p.user_id,
            u.account_id,
            CONCAT(u.first_name, ' ', u.last_name) AS customer_name,
            p.date AS payment_date,
            p.amount,
            ip.invoice_id,
            i.date AS invoice_date,
            EXTRACT(YEAR_MONTH FROM p.date) AS payment_yearmonth,
            EXTRACT(YEAR_MONTH FROM i.date) AS invoice_yearmonth,
            i.balance,
            i.total AS invoice_total
        FROM 
            payment p
        JOIN 
            invoice_payment ip ON p.id = ip.payment_id
        JOIN 
            invoice i ON ip.invoice_id = i.id
        JOIN
            user u ON p.user_id = u.id
        WHERE 
            EXTRACT(YEAR_MONTH FROM p.date) != EXTRACT(YEAR_MONTH FROM i.date)
            {date_filter}
        ORDER BY 
            p.date DESC
        """
        
        date_filter = ""
        params = []
        
        if start_date:
            date_filter += " AND p.date >= %s"
            params.append(start_date)
        
        if end_date:
            date_filter += " AND p.date <= %s"
            params.append(end_date)
        
        query = query.format(date_filter=date_filter)
        
        # For development: generate sample data if query execution fails
        try:
            results = self.execute_query(query, params)
            df = pd.DataFrame(results)
        except Exception as e:
            print(f"Error executing query: {e}")
            # Create mock data for demo purposes
            df = self.generate_mock_cross_cycle_data()
            
        return df
    
    def generate_mock_cross_cycle_data(self) -> pd.DataFrame:
        """
        Generate mock data for cross-cycle payments when database is not available.
        """
        if hasattr(self, 'mock_service'):
            return self.mock_service.generate_cross_cycle_payments(num_records=25)
            
        # Fallback mock data if mock service is not available
        data = []
        account_ids = [f"ACC{i:04d}" for i in range(1, 11)]
        customer_names = ["Jane Smith", "John Doe", "Alice Johnson", "Bob Williams", "Carol Davis"]
        
        for i in range(25):
            payment_date = datetime.now() - timedelta(days=np.random.randint(1, 90))
            invoice_date = payment_date - timedelta(days=np.random.randint(30, 60)) if np.random.random() > 0.5 else payment_date + timedelta(days=np.random.randint(30, 60))
            
            data.append({
                'payment_id': i + 1,
                'user_id': np.random.randint(1, 100),
                'account_id': np.random.choice(account_ids),
                'customer_name': np.random.choice(customer_names),
                'payment_date': payment_date,
                'amount': np.random.randint(50, 500),
                'invoice_id': np.random.randint(1000, 9999),
                'invoice_date': invoice_date,
                'payment_yearmonth': int(payment_date.strftime('%Y%m')),
                'invoice_yearmonth': int(invoice_date.strftime('%Y%m')),
                'balance': np.random.randint(0, 200),
                'invoice_total': np.random.randint(100, 1000)
            })
        
        return pd.DataFrame(data)
    
    def get_payment_distribution_by_cycle(self, start_date=None, end_date=None) -> pd.DataFrame:
        """
        Get payment distribution data grouped by billing cycle.
        
        Args:
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
            
        Returns:
            DataFrame containing payment distribution data by billing cycle
        """
        query = """
        SELECT 
            EXTRACT(YEAR_MONTH FROM p.date) AS payment_yearmonth,
            COUNT(DISTINCT p.id) AS payment_count,
            SUM(p.amount) AS total_amount,
            COUNT(DISTINCT p.user_id) AS customer_count,
            MIN(p.date) AS first_payment_date,
            MAX(p.date) AS last_payment_date
        FROM 
            payment p
        WHERE 
            p.isDeleted = 0
            {date_filter}
        GROUP BY 
            payment_yearmonth
        ORDER BY 
            payment_yearmonth DESC
        """
        
        date_filter = ""
        params = []
        
        if start_date:
            date_filter += " AND p.date >= %s"
            params.append(start_date)
        
        if end_date:
            date_filter += " AND p.date <= %s"
            params.append(end_date)
        
        query = query.format(date_filter=date_filter)
        
        # For development: generate sample data if query execution fails
        try:
            results = self.execute_query(query, params)
            df = pd.DataFrame(results)
        except Exception as e:
            print(f"Error executing query: {e}")
            # Create mock data for demo purposes
            df = self.generate_mock_distribution_data()
            
        return df
    
    def get_at_risk_accounts(self) -> pd.DataFrame:
        """
        Identify accounts at risk of payment misapplication issues based on
        payment patterns.
        
        Returns:
            DataFrame containing at-risk accounts and risk factors
        """
        # For development: generate sample data
        try:
            query = """
            -- Find accounts likely to make payments for future cycles
            SELECT 
                u.id AS user_id,
                u.account_id,
                CONCAT(u.first_name, ' ', u.last_name) AS customer_name,
                COUNT(DISTINCT e.id) AS enrollment_count,
                COUNT(p.id) AS payment_count,
                AVG(DAYOFMONTH(p.date)) AS avg_day_of_month,
                MAX(p.date) AS last_payment_date,
                CASE 
                    WHEN COUNT(DISTINCT e.id) > 1 THEN 1 ELSE 0 
                END AS has_multiple_enrollments,
                CASE 
                    WHEN AVG(DAYOFMONTH(p.date)) < 15 THEN 1 ELSE 0 
                END AS pays_early_in_month
            FROM 
                user u
            JOIN 
                enrolment e ON u.id = e.user_id
            JOIN 
                payment p ON u.id = p.user_id
            WHERE 
                e.is_active = 1 AND
                p.date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH) AND
                p.isDeleted = 0
            GROUP BY 
                u.id
            HAVING 
                payment_count >= 3
            ORDER BY 
                (has_multiple_enrollments + pays_early_in_month) DESC,
                enrollment_count DESC,
                avg_day_of_month ASC
            LIMIT 50
            """
            
            results = self.execute_query(query)
            df = pd.DataFrame(results)
        except Exception as e:
            print(f"Error executing query: {e}")
            # Create mock data for demo purposes
            df = self.generate_mock_risk_data()
        
        if not df.empty:
            # Calculate risk score (0-100)
            df['risk_score'] = (
                (df['has_multiple_enrollments'] * 40) + 
                (df['pays_early_in_month'] * 30) +
                (np.minimum(df['enrollment_count'] - 1, 3) / 3 * 20) +
                ((30 - np.minimum(df['avg_day_of_month'], 30)) / 30 * 10)
            )
            
        return df
    
    def get_account_detail(self, account_id: str) -> Dict[str, Any]:
        """
        Get detailed payment history for a specific account.
        
        Args:
            account_id: Account ID to analyze
            
        Returns:
            Dictionary with account details and payment history
        """
        # For development: generate sample data
        try:
            # Get account information
            account_query = """
            SELECT 
                u.id AS user_id,
                u.account_id,
                u.first_name,
                u.last_name,
                u.email,
                COUNT(DISTINCT e.id) AS enrollment_count
            FROM 
                user u
            LEFT JOIN 
                enrolment e ON u.id = e.user_id
            WHERE 
                u.account_id = %s
            GROUP BY 
                u.id
            """
            
            account_results = self.execute_query(account_query, [account_id])
            if not account_results:
                return {"error": f"Account {account_id} not found"}
            
            account_info = account_results[0]
            
            # Get payment history
            payment_query = """
            SELECT 
                p.id AS payment_id,
                p.date AS payment_date,
                p.amount,
                p.reference,
                EXTRACT(YEAR_MONTH FROM p.date) AS payment_yearmonth
            FROM 
                payment p
            WHERE 
                p.user_id = %s AND
                p.isDeleted = 0
            ORDER BY 
                p.date DESC
            """
            
            payment_results = self.execute_query(payment_query, [account_info['user_id']])
            payment_df = pd.DataFrame(payment_results) if payment_results else pd.DataFrame()
            
            # Get cross-cycle payments for this account
            cross_cycle_query = """
            SELECT 
                p.id AS payment_id,
                p.date AS payment_date,
                p.amount,
                ip.invoice_id,
                i.date AS invoice_date,
                EXTRACT(YEAR_MONTH FROM p.date) AS payment_yearmonth,
                EXTRACT(YEAR_MONTH FROM i.date) AS invoice_yearmonth
            FROM 
                payment p
            JOIN 
                invoice_payment ip ON p.id = ip.payment_id
            JOIN 
                invoice i ON ip.invoice_id = i.id
            WHERE 
                p.user_id = %s AND
                EXTRACT(YEAR_MONTH FROM p.date) != EXTRACT(YEAR_MONTH FROM i.date)
            ORDER BY 
                p.date DESC
            """
            
            cross_cycle_results = self.execute_query(cross_cycle_query, [account_info['user_id']])
            cross_cycle_df = pd.DataFrame(cross_cycle_results) if cross_cycle_results else pd.DataFrame()
            
            # Compile full response
            return {
                "account_info": account_info,
                "payment_history": payment_df.to_dict(orient="records") if not payment_df.empty else [],
                "cross_cycle_payments": cross_cycle_df.to_dict(orient="records") if not cross_cycle_df.empty else [],
                "has_misapplied_payments": not cross_cycle_df.empty,
                "total_payments": len(payment_df) if not payment_df.empty else 0,
                "total_misapplied": len(cross_cycle_df) if not cross_cycle_df.empty else 0,
                "total_amount_misapplied": cross_cycle_df['amount'].sum() if not cross_cycle_df.empty else 0
            }
        except Exception as e:
            print(f"Error executing query: {e}")
            # Create mock data for demo purposes
            return self.generate_mock_account_detail(account_id)
    
    def create_payment_flow_diagram(self, df: pd.DataFrame) -> go.Figure:
        """
        Create a Sankey diagram visualizing payment flows between billing cycles.
        
        Args:
            df: DataFrame with cross-cycle payment data
            
        Returns:
            Plotly figure object with Sankey diagram
        """
        if df.empty:
            # Return empty figure with message
            fig = go.Figure()
            fig.add_annotation(
                text="No cross-cycle payments found in the selected date range",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return fig
            
        # Group by payment cycle and invoice cycle
        flow_df = df.groupby(['payment_yearmonth', 'invoice_yearmonth']).agg({
            'amount': 'sum',
            'payment_id': 'count'
        }).reset_index()
        
        # Prepare Sankey diagram data
        source = []
        target = []
        value = []
        
        # Get unique cycles for node labels
        all_cycles = sorted(list(set(flow_df['payment_yearmonth'].astype(str).unique()) | 
                                 set(flow_df['invoice_yearmonth'].astype(str).unique())))
        cycle_to_idx = {cycle: idx for idx, cycle in enumerate(all_cycles)}
        
        # Create links data
        for _, row in flow_df.iterrows():
            source.append(cycle_to_idx[str(row['payment_yearmonth'])])
            target.append(cycle_to_idx[str(row['invoice_yearmonth'])])
            value.append(float(row['amount']))
        
        # Format cycle labels for better readability
        readable_labels = []
        for cycle in all_cycles:
            try:
                year = int(cycle[:4])
                month = int(cycle[4:])
                readable_labels.append(f"{year}-{month:02d}")
            except (ValueError, IndexError):
                readable_labels.append(str(cycle))
        
        # Create Sankey diagram
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=readable_labels,
                color="blue"
            ),
            link=dict(
                source=source,
                target=target,
                value=value,
                color="rgba(100, 100, 200, 0.4)"
            )
        )])
        
        fig.update_layout(
            title_text="Payment Flow Across Billing Cycles",
            font_size=12,
            height=600
        )
        
        return fig
    
    def create_payment_timeline(self, df: pd.DataFrame) -> go.Figure:
        """
        Create a timeline visualization of payments across billing cycles.
        
        Args:
            df: DataFrame with cross-cycle payment data
            
        Returns:
            Plotly figure object with timeline visualization
        """
        if df.empty:
            # Return empty figure with message
            fig = go.Figure()
            fig.add_annotation(
                text="No payment data available for the selected date range",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        # Create a copy and ensure date columns are datetime
        plot_df = df.copy()
        plot_df['payment_date'] = pd.to_datetime(plot_df['payment_date'])
        plot_df['invoice_date'] = pd.to_datetime(plot_df['invoice_date'])
        
        # Calculate days between payment and invoice (negative means payment is before invoice)
        plot_df['days_between'] = (plot_df['payment_date'] - plot_df['invoice_date']).dt.days
        
        # Create figure
        fig = px.scatter(
            plot_df,
            x='payment_date',
            y='days_between',
            size='amount',
            color='amount',
            hover_name='customer_name',
            hover_data={
                'payment_id': True,
                'invoice_id': True,
                'amount': ':.2f',
                'payment_date': '|%Y-%m-%d',
                'invoice_date': '|%Y-%m-%d',
                'days_between': True
            },
            color_continuous_scale='Viridis',
            size_max=50
        )
        
        # Add a horizontal line at y=0 (same day payment)
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        
        # Add shaded regions for different payment types
        fig.add_hrect(y0=30, y1=plot_df['days_between'].max() + 10, 
                      fillcolor="red", opacity=0.1, line_width=0,
                      annotation_text="Payment After Invoice Due", annotation_position="top right")
        
        fig.add_hrect(y0=0, y1=30, 
                      fillcolor="green", opacity=0.1, line_width=0,
                      annotation_text="Normal Payment Window", annotation_position="top right")
        
        fig.add_hrect(y0=plot_df['days_between'].min() - 10, y1=0, 
                      fillcolor="blue", opacity=0.1, line_width=0,
                      annotation_text="Advance Payment", annotation_position="bottom right")
        
        # Update layout
        fig.update_layout(
            title='Payment Timing Relative to Invoice Date',
            xaxis_title='Payment Date',
            yaxis_title='Days Between Payment and Invoice (negative = advance payment)',
            coloraxis_colorbar_title='Payment Amount',
            height=600
        )
        
        return fig
    
    def create_billing_cycle_heatmap(self, cross_cycle_df):
        """
        Create a heatmap visualization of payment distribution across billing cycles.
        This visualization directly relates to Fix Point #1 in GitHub issue #704.
        
        Args:
            cross_cycle_df: DataFrame with cross-cycle payment data
            
        Returns:
            Plotly figure object with heatmap visualization
        """
        if cross_cycle_df.empty:
            # Create an empty figure with a message if no data
            fig = go.Figure()
            fig.add_annotation(
                text="No cross-cycle payment data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # Aggregate the data by payment and invoice yearmonth
        pivot_data = cross_cycle_df.groupby(['payment_yearmonth', 'invoice_yearmonth']).agg({
            'amount': 'sum',
            'payment_id': 'count'
        }).reset_index()
        
        # Convert yearmonth to date strings for better display
        pivot_data['payment_period'] = pivot_data['payment_yearmonth'].apply(
            lambda ym: f"{ym//100}-{ym%100:02d}"
        )
        pivot_data['invoice_period'] = pivot_data['invoice_yearmonth'].apply(
            lambda ym: f"{ym//100}-{ym%100:02d}"
        )
        
        # Create a pivot table for the heatmap
        heatmap_pivot = pivot_data.pivot_table(
            values='amount',
            index='payment_period',
            columns='invoice_period',
            aggfunc='sum'
        ).fillna(0)
        
        # Ensure we have at least a few periods for display
        if len(heatmap_pivot) < 2:
            # Add some mock periods if not enough data
            periods = self._generate_period_range(6)
            for period in periods:
                if period not in heatmap_pivot.index:
                    heatmap_pivot.loc[period] = 0
                if period not in heatmap_pivot.columns:
                    heatmap_pivot[period] = 0
        
        # Sort the indices to ensure chronological order
        heatmap_pivot = heatmap_pivot.sort_index().sort_index(axis=1)
        
        # Create the heatmap
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_pivot.values,
            x=heatmap_pivot.columns,
            y=heatmap_pivot.index,
            colorscale='Viridis',
            colorbar=dict(title='Payment Amount ($)'),
            hovertemplate=(
                'Payment Period: %{y}<br>' +
                'Invoice Period: %{x}<br>' +
                'Amount: $%{z:.2f}<extra></extra>'
            )
        ))
        
        # Add a diagonal line to show the boundary
        x_values = list(range(len(heatmap_pivot.columns)))
        y_values = list(range(len(heatmap_pivot.index)))
        
        if len(x_values) > 0 and len(y_values) > 0:
            max_val = min(max(x_values), max(y_values))
            
            fig.add_shape(
                type="line",
                x0=-0.5, y0=-0.5,
                x1=max_val+0.5, y1=max_val+0.5,
                line=dict(color="red", width=2, dash="dash"),
            )
        
        # Add annotation explaining the diagonal line
        fig.add_annotation(
            x=len(heatmap_pivot.columns) / 4,
            y=len(heatmap_pivot.index) / 4,
            text="Boundary Issue Area<br>(Future Payments Applied<br>to Past Invoices)",
            showarrow=True,
            arrowhead=2,
            arrowcolor="red",
            ax=40,
            ay=-40
        )
        
        # Update layout
        fig.update_layout(
            title="Payment Distribution Across Billing Cycle Boundaries",
            xaxis_title="Invoice Billing Period",
            yaxis_title="Payment Billing Period",
            xaxis=dict(
                title_font=dict(size=14),
                tickfont=dict(size=12),
                tickangle=45
            ),
            yaxis=dict(
                title_font=dict(size=14),
                tickfont=dict(size=12)
            ),
            margin=dict(t=60, r=30, b=80, l=80),
            height=600
        )
        
        return fig
        
    def create_customer_journey_map(self):
        """
        Create a customer journey map showing impact of payment misapplication.
        This helps business stakeholders see the customer experience implications.
        """
        # Define journey stages
        stages = ['Enrollment', 'Monthly Payment', 'Invoice Receipt', 
                'Balance Check', 'Customer Support']
        
        # Define experience under different scenarios
        correct_application = [5, 5, 5, 5, 5]  # Perfect experience
        minor_misapplication = [5, 4, 3, 2, 3]  # Some frustration
        major_misapplication = [5, 4, 2, 1, 1]  # Major frustration
        
        # Create figure
        fig = go.Figure()
        
        # Add traces for each scenario
        fig.add_trace(go.Scatter(
            x=stages, y=correct_application,
            mode='lines+markers',
            name='Correct Payment Application',
            line=dict(color='green', width=3),
            marker=dict(size=12)
        ))
        
        fig.add_trace(go.Scatter(
            x=stages, y=minor_misapplication,
            mode='lines+markers',
            name='Minor Misapplication',
            line=dict(color='orange', width=3),
            marker=dict(size=12)
        ))
        
        fig.add_trace(go.Scatter(
            x=stages, y=major_misapplication,
            mode='lines+markers',
            name='Major Misapplication',
            line=dict(color='red', width=3),
            marker=dict(size=12)
        ))
        
        # Update layout
        fig.update_layout(
            title="Customer Experience Impact of Payment Misapplication",
            xaxis_title="Customer Journey Stage",
            yaxis_title="Experience Score (5=Excellent, 1=Poor)",
            yaxis=dict(range=[0, 5.5]),
            annotations=[
                dict(
                    x="Balance Check", y=1.2,
                    xref="x", yref="y",
                    text="Critical pain point:<br>Customers see<br>incorrect balances",
                    showarrow=True,
                    arrowhead=2,
                    ax=0, ay=-40
                )
            ]
        )
        
        return fig
    
    def create_domain_relationship_map(self):
        """
        Create a simplified domain relationship visualization showing
        how payment boundaries interact with other business domains.
        """
        # Create a Sankey diagram to show domain relationships
        domains = ["Payment", "Invoice", "Lesson", "Enrollment", "Billing Cycle", "Customer"]
        
        # Define the flows between domains
        sources = [0, 0, 1, 2, 3, 4, 0]
        targets = [1, 4, 2, 3, 5, 3, 5]
        values = [10, 8, 6, 5, 7, 4, 3]
        labels = ["Applies To", "Must Respect", "Charges For", 
                 "Part Of", "Belongs To", "Defined By", "Made By"]
        
        # Create a color map for the nodes
        node_colors = ['#6175c1', '#50b5a5', '#f7c325', 
                      '#ef553b', '#ab63fa', '#ffa15a']
        
        # Create Sankey diagram
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=domains,
                color=node_colors
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                label=labels,
                hovertemplate='%{label}: %{value}<extra></extra>'
            )
        )])
        
        # Update layout
        fig.update_layout(
            title_text="Payment System Domain Context Map",
            font_size=12,
            height=500
        )
        
        return fig

    def _generate_period_range(self, num_periods):
        """Generate a range of period strings for visualizations."""
        current_date = datetime.now()
        periods = []
        
        for i in range(num_periods):
            month = current_date.month - i
            year = current_date.year
            
            # Adjust for negative months
            while month <= 0:
                month += 12
                year -= 1
                
            periods.append(f"{year}-{month:02d}")
            
        return sorted(periods)
    
    # Mock data generation methods for development
    
    def generate_mock_cross_cycle_data(self) -> pd.DataFrame:
        """Generate mock cross-cycle payment data for development."""
        # Create mock data with realistic payment patterns
        data = []
        now = datetime.now()
        
        # Simulate 50 payments across different cycles
        for i in range(50):
            payment_date = now - timedelta(days=i * 5)
            invoice_date = payment_date - timedelta(days=30 if i % 2 == 0 else -30)
            
            payment_yearmonth = int(f"{payment_date.year}{payment_date.month:02d}")
            invoice_yearmonth = int(f"{invoice_date.year}{invoice_date.month:02d}")
            
            data.append({
                'payment_id': 10000 + i,
                'user_id': 100 + (i % 10),
                'account_id': f"ACC{100 + (i % 10):04d}",
                'customer_name': f"Customer {100 + (i % 10)}",
                'payment_date': payment_date,
                'amount': round(100 + (i % 5) * 25, 2),
                'invoice_id': 20000 + i,
                'invoice_date': invoice_date,
                'payment_yearmonth': payment_yearmonth,
                'invoice_yearmonth': invoice_yearmonth,
                'balance': 0.00,
                'invoice_total': round(100 + (i % 5) * 25, 2)
            })
        
        return pd.DataFrame(data)
    
    def generate_mock_distribution_data(self) -> pd.DataFrame:
        """Generate mock payment distribution data for development."""
        # Create mock data with realistic payment patterns
        data = []
        now = datetime.now()
        
        # Generate data for the last 12 months
        for i in range(12):
            month_date = datetime(now.year, now.month, 1) - timedelta(days=i * 30)
            yearmonth = int(f"{month_date.year}{month_date.month:02d}")
            
            data.append({
                'payment_yearmonth': yearmonth,
                'payment_count': 50 + (i % 3) * 10,
                'total_amount': 5000 + (i % 5) * 1000,
                'customer_count': 30 + (i % 3) * 5,
                'first_payment_date': month_date.replace(day=1),
                'last_payment_date': month_date.replace(day=28)
            })
        
        return pd.DataFrame(data)
    
    def generate_mock_risk_data(self) -> pd.DataFrame:
        """Generate mock at-risk account data for development."""
        # Create mock data with realistic risk patterns
        data = []
        
        # Generate 20 accounts with varying risk factors
        for i in range(20):
            data.append({
                'user_id': 100 + i,
                'account_id': f"ACC{100 + i:04d}",
                'customer_name': f"Customer {100 + i}",
                'enrollment_count': 1 + (i % 3),
                'payment_count': 10 + (i % 5),
                'avg_day_of_month': 5 if i % 3 == 0 else 15 if i % 3 == 1 else 25,
                'last_payment_date': datetime.now() - timedelta(days=i * 5),
                'has_multiple_enrollments': 1 if i % 3 == 0 else 0,
                'pays_early_in_month': 1 if i % 2 == 0 else 0
            })
        
        return pd.DataFrame(data)
    
    def generate_mock_account_detail(self, account_id: str) -> Dict[str, Any]:
        """Generate mock account details for development."""
        account_num = int(account_id.replace("ACC", "")) if account_id.startswith("ACC") else 100
        
        # Create account info
        account_info = {
            'user_id': account_num,
            'account_id': account_id,
            'first_name': "Demo",
            'last_name': f"User {account_num}",
            'email': f"user{account_num}@example.com",
            'enrollment_count': 1 + (account_num % 3)
        }
        
        # Create payment history
        payment_history = []
        now = datetime.now()
        
        for i in range(12):
            payment_date = now - timedelta(days=i * 30)
            payment_history.append({
                'payment_id': 10000 + (account_num * 100) + i,
                'payment_date': payment_date,
                'amount': round(100 + (i % 5) * 25, 2),
                'reference': f"REF{10000 + (account_num * 100) + i}",
                'payment_yearmonth': int(f"{payment_date.year}{payment_date.month:02d}")
            })
        
        # Create cross-cycle payments (3 of them)
        cross_cycle = []
        for i in range(3):
            payment_date = now - timedelta(days=i * 60)
            invoice_date = payment_date - timedelta(days=30)
            
            cross_cycle.append({
                'payment_id': 10000 + (account_num * 100) + i,
                'payment_date': payment_date,
                'amount': round(100 + (i % 5) * 25, 2),
                'invoice_id': 20000 + (account_num * 100) + i,
                'invoice_date': invoice_date,
                'payment_yearmonth': int(f"{payment_date.year}{payment_date.month:02d}"),
                'invoice_yearmonth': int(f"{invoice_date.year}{invoice_date.month:02d}")
            })
        
        return {
            'account_info': account_info,
            'payment_history': payment_history,
            'cross_cycle_payments': cross_cycle,
            'has_misapplied_payments': True,
            'total_payments': len(payment_history),
            'total_misapplied': len(cross_cycle),
            'total_amount_misapplied': sum(item['amount'] for item in cross_cycle)
        }
