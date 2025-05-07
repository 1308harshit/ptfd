#!/usr/bin/env python3
"""
Payment Flow Visualization Dashboard

Interactive visualization for payment flow patterns in the SMW system,
focusing on identifying misapplication patterns across billing cycles.

Related GitHub Issue: #704
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime, timedelta
import random
from typing import Dict, List, Any, Optional, Tuple

from app.services.financial_dashboards_service import FinancialDashboardsService


class PaymentFlowVisualizationDashboard:
    """
    Dashboard for visualizing payment flows using Plotly.
    
    This dashboard provides interactive visualizations to help identify and analyze
    payment misapplication patterns across billing cycles.
    """
    
    def __init__(self, financial_service: Optional[FinancialDashboardsService] = None):
        """Initialize the dashboard with required services."""
        self.financial_service = financial_service or FinancialDashboardsService()
    
    def run(self):
        """Main entry point for the dashboard."""
        st.title("Payment Flow Visualization")
        st.markdown("""
        This dashboard uses interactive visualizations to help identify and analyze 
        payment misapplication patterns across billing cycles.
        
        Select a customer and date range to visualize payment flows.
        """)
        
        # Customer selection
        customers = self.financial_service.get_customers_with_misapplied_payments()
        if not customers.empty:
            st.subheader("Customer Selection")
            selected_customer_id = st.selectbox(
                "Select Customer",
                options=customers['user_id'].tolist(),
                format_func=lambda x: f"{x} - {customers[customers['user_id'] == x]['firstname'].iloc[0]} {customers[customers['user_id'] == x]['lastname'].iloc[0]}"
            )
            
            # Date range selection
            st.subheader("Date Range")
            col1, col2 = st.columns(2)
            with col1:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=90)
                start_date_input = st.date_input("Start Date", value=start_date, key="d3_start_date")
            
            with col2:
                end_date_input = st.date_input("End Date", value=end_date, key="d3_end_date")
            
            if start_date_input and end_date_input:
                if start_date_input > end_date_input:
                    st.error("Start date must be before end date.")
                    return
                
                start_str = start_date_input.strftime('%Y-%m-%d')
                end_str = end_date_input.strftime('%Y-%m-%d')
                
                # Now add visualization tabs
                tab1, tab2, tab3 = st.tabs(["Payment Flow Sankey", "Payment Timeline", "Payment Network"])
                
                with tab1:
                    self._render_sankey_diagram(selected_customer_id, start_str, end_str)
                
                with tab2:
                    self._render_payment_timeline(selected_customer_id, start_str, end_str)
                
                with tab3:
                    self._render_payment_network(selected_customer_id, start_str, end_str)
        else:
            st.info("No customers with misapplied payments found in the database.")
    
    def _render_sankey_diagram(self, customer_id: str, start_date: str, end_date: str):
        """Render the Payment Flow Sankey Diagram using Plotly."""
        st.subheader("Payment Flow Sankey Diagram")
        st.markdown("""
        This diagram visualizes how payments flow to specific lessons, highlighting misallocations 
        where payments are applied to lessons outside their intended billing cycle.
        """)
        
        # Get payment flow data for selected customer
        try:
            # In a real implementation, this would fetch real data
            # payment_flow_data = self.financial_service.get_payment_flow_data(customer_id, start_date, end_date)
            payment_flow_data = self._get_mock_payment_flow_data(customer_id)
            
            if not payment_flow_data['nodes'] or not payment_flow_data['links']:
                st.warning("No payment flow data available for the selected date range.")
                return
            
            # Create a Plotly Sankey diagram
            fig = self._create_sankey_diagram(payment_flow_data)
            st.plotly_chart(fig, use_container_width=True)
            
            # Add legend
            st.markdown("""
            **Legend:**
            - **Blue nodes:** Payments
            - **Green nodes:** Lessons in the correct billing cycle
            - **Orange nodes:** Lessons in a different billing cycle (misapplied)
            - **Gray links:** Correct payment applications
            - **Red links:** Misapplied payments
            """)
        except Exception as e:
            st.error(f"Error rendering Sankey diagram: {e}")
    
    def _create_sankey_diagram(self, data: Dict[str, Any]) -> go.Figure:
        """Create a Plotly Sankey diagram from the provided data."""
        nodes = data['nodes']
        links = data['links']
        
        # Prepare node labels and colors
        node_labels = [node['name'] for node in nodes]
        node_colors = []
        
        for node in nodes:
            if node['type'] == 'payment':
                node_colors.append('rgba(52, 152, 219, 0.8)')  # Blue for payments
            elif node['type'] == 'lesson':
                # Check if this lesson has any misapplied payments
                is_misapplied = any(
                    link['target'] == nodes.index(node) and not link.get('correct', True)
                    for link in links
                )
                node_colors.append('rgba(230, 126, 34, 0.8)' if is_misapplied else 'rgba(39, 174, 96, 0.8)')
        
        # Prepare link colors
        link_colors = [
            'rgba(231, 76, 60, 0.6)' if not link.get('correct', True) else 'rgba(153, 153, 153, 0.6)'
            for link in links
        ]
        
        # Create the Sankey diagram
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=node_labels,
                color=node_colors
            ),
            link=dict(
                source=[link['source'] for link in links],
                target=[link['target'] for link in links],
                value=[link.get('value', 1) for link in links],
                color=link_colors
            )
        )])
        
        fig.update_layout(
            title_text="Payment Flow Sankey Diagram",
            font_size=12,
            height=600
        )
        
        return fig
    
    def _render_payment_timeline(self, customer_id: str, start_date: str, end_date: str):
        """Render the Payment Timeline visualization using Plotly."""
        st.subheader("Payment Timeline")
        st.markdown("""
        This timeline shows when payments were made relative to billing cycles, helping to identify
        patterns that may lead to misapplication issues.
        """)
        
        try:
            # In a real implementation, this would fetch real data
            # timeline_data = self.financial_service.get_payment_timeline_data(customer_id, start_date, end_date)
            timeline_data = self._get_mock_timeline_data(customer_id)
            
            if not timeline_data.get('events'):
                st.warning("No timeline data available for the selected date range.")
                return
            
            # Create a Plotly timeline visualization
            fig = self._create_timeline_visualization(timeline_data)
            st.plotly_chart(fig, use_container_width=True)
            
            # Add observations
            st.subheader("Patterns and Observations")
            insights = self._generate_timeline_insights(timeline_data)
            
            for insight in insights:
                if insight['type'] == 'warning':
                    st.warning(insight['message'])
                elif insight['type'] == 'info':
                    st.info(insight['message'])
                elif insight['type'] == 'success':
                    st.success(insight['message'])
        except Exception as e:
            st.error(f"Error rendering payment timeline: {e}")
    
    def _create_timeline_visualization(self, data: Dict[str, Any]) -> go.Figure:
        """Create a Plotly timeline visualization from the provided data."""
        events = data.get('events', [])
        cycles = data.get('cycles', [])
        
        fig = go.Figure()
        
        # Add billing cycle ranges as shaded regions
        for i, cycle in enumerate(cycles):
            color = "rgba(240, 240, 240, 0.5)" if i % 2 == 0 else "rgba(220, 220, 220, 0.5)"
            
            fig.add_shape(
                type="rect",
                x0=cycle['start_date'],
                x1=cycle['end_date'],
                y0=0,
                y1=1,
                fillcolor=color,
                line=dict(width=0),
                layer="below"
            )
            
            # Add cycle label
            fig.add_annotation(
                x=(datetime.fromisoformat(cycle['start_date']) + 
                   (datetime.fromisoformat(cycle['end_date']) - 
                    datetime.fromisoformat(cycle['start_date'])) / 2).isoformat(),
                y=0.95,
                text=cycle['name'],
                showarrow=False
            )
        
        # Add events as points on the timeline
        event_types = {
            'payment': {'y': 0.3, 'color': 'rgb(52, 152, 219)', 'symbol': 'circle'},
            'lesson': {'y': 0.6, 'color': 'rgb(39, 174, 96)', 'symbol': 'square'},
            'misapplied': {'y': 0.6, 'color': 'rgb(230, 126, 34)', 'symbol': 'square'}
        }
        
        # Group events by type for separate traces
        for event_type, props in event_types.items():
            type_events = [event for event in events if event['type'] == event_type]
            
            if event_type == 'lesson':
                # Further filter to only correctly applied lessons
                type_events = [event for event in type_events if not event.get('misapplied')]
            
            if event_type == 'misapplied':
                # Get lessons that are misapplied
                type_events = [event for event in events 
                             if event['type'] == 'lesson' and event.get('misapplied')]
            
            if type_events:
                fig.add_trace(go.Scatter(
                    x=[event['date'] for event in type_events],
                    y=[props['y']] * len(type_events),
                    mode='markers',
                    marker=dict(
                        size=12,
                        color=props['color'],
                        symbol=props['symbol']
                    ),
                    text=[event['description'] for event in type_events],
                    hoverinfo='text',
                    name=event_type.capitalize()
                ))
        
        # Add connection lines between payments and lessons
        for event in events:
            if event['type'] == 'payment' and 'connections' in event:
                for connection in event['connections']:
                    target_event = next((e for e in events if e['id'] == connection['target']), None)
                    if target_event:
                        line_color = 'rgba(231, 76, 60, 0.6)' if connection.get('misapplied') else 'rgba(153, 153, 153, 0.6)'
                        line_dash = 'dash' if connection.get('misapplied') else 'solid'
                        
                        fig.add_shape(
                            type="line",
                            x0=event['date'],
                            y0=event_types['payment']['y'],
                            x1=target_event['date'],
                            y1=event_types['lesson' if not connection.get('misapplied') else 'misapplied']['y'],
                            line=dict(
                                color=line_color,
                                width=1.5,
                                dash=line_dash
                            )
                        )
        
        # Update layout
        fig.update_layout(
            title="Payment Timeline Analysis",
            xaxis=dict(
                title="Date",
                type='date'
            ),
            yaxis=dict(
                visible=False,
                range=[0, 1]
            ),
            height=500,
            showlegend=True
        )
        
        return fig
    
    def _render_payment_network(self, customer_id: str, start_date: str, end_date: str):
        """Render the Payment Network visualization using Plotly."""
        st.subheader("Payment Network Visualization")
        st.markdown("""
        This network graph visualizes the relationships between payments and lessons,
        highlighting patterns of misapplication across billing cycles.
        """)
        
        try:
            # In a real implementation, this would fetch real data
            # network_data = self.financial_service.get_payment_network_data(customer_id, start_date, end_date)
            network_data = self._get_mock_network_data(customer_id)
            
            if not network_data.get('nodes') or not network_data.get('links'):
                st.warning("No network data available for the selected date range.")
                return
            
            # Create a Plotly network visualization
            fig = self._create_network_visualization(network_data)
            st.plotly_chart(fig, use_container_width=True)
            
            # Add legend
            st.markdown("""
            **Legend:**
            - **Blue nodes:** Payments
            - **Green nodes:** Lessons in the correct billing cycle
            - **Orange nodes:** Lessons in a different billing cycle (misapplied)
            - **Gray edges:** Correct payment applications
            - **Red edges:** Misapplied payments
            """)
        except Exception as e:
            st.error(f"Error rendering payment network: {e}")
    
    def _create_network_visualization(self, data: Dict[str, Any]) -> go.Figure:
        """Create a Plotly network visualization from the provided data."""
        nodes = data.get('nodes', [])
        links = data.get('links', [])
        
        # Create a simple layout for the nodes
        payment_nodes = [node for node in nodes if node['type'] == 'payment']
        lesson_nodes = [node for node in nodes if node['type'] == 'lesson']
        
        # Position nodes
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        node_size = []
        node_symbols = []
        
        # Position payment nodes on left
        for i, node in enumerate(payment_nodes):
            node_x.append(0.2)
            node_y.append(1.0 * (i + 1) / (len(payment_nodes) + 1))
            node_text.append(f"{node['name']}<br>Amount: ${node.get('amount', 0):.2f}")
            node_color.append('rgb(52, 152, 219)')  # Blue for payments
            node_size.append(25)
            node_symbols.append('circle')
        
        # Position lesson nodes on right
        for i, node in enumerate(lesson_nodes):
            node_x.append(0.8)
            node_y.append(1.0 * (i + 1) / (len(lesson_nodes) + 1))
            node_text.append(f"{node['name']}<br>Date: {node.get('date', 'N/A')}")
            
            # Check if any links to this node are misapplied
            misapplied = any(
                link['target'] == nodes.index(node) and not link.get('correct', True) 
                for link in links
            )
            node_color.append('rgb(230, 126, 34)' if misapplied else 'rgb(39, 174, 96)')
            node_size.append(20)
            node_symbols.append('square')
        
        # Create edges
        edge_x = []
        edge_y = []
        edge_colors = []
        
        for link in links:
            source_idx = link['source']
            target_idx = link['target']
            
            source_x = node_x[source_idx]
            source_y = node_y[source_idx]
            target_x = node_x[target_idx]
            target_y = node_y[target_idx]
            
            edge_x.extend([source_x, target_x, None])
            edge_y.extend([source_y, target_y, None])
            
            edge_color = 'rgba(231, 76, 60, 0.8)' if not link.get('correct', True) else 'rgba(153, 153, 153, 0.6)'
            edge_colors.extend([edge_color, edge_color, edge_color])
        
        # Create the figure
        fig = go.Figure()
        
        # Add edges
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1.5, color=edge_colors),
            hoverinfo='none',
            mode='lines',
            name='Connections'
        ))
        
        # Add nodes
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            marker=dict(
                size=node_size,
                color=node_color,
                line=dict(width=1, color='white'),
                symbol=node_symbols
            ),
            text=node_text,
            hoverinfo='text',
            name='Nodes'
        ))
        
        # Update layout
        fig.update_layout(
            title="Payment Network Visualization",
            showlegend=False,
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[0, 1]
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[0, 1]
            ),
            height=600,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
        
    def _get_mock_payment_flow_data(self, customer_id: str) -> Dict[str, Any]:
        """Generate mock data for the payment flow visualization."""
        # Create mock nodes representing payments and lessons
        nodes = [
            # Payment nodes
            {"id": "p1", "name": f"Payment #{customer_id}-1", "type": "payment", "amount": 120.00, "date": "2025-03-01"},
            {"id": "p2", "name": f"Payment #{customer_id}-2", "type": "payment", "amount": 80.00, "date": "2025-03-15"},
            {"id": "p3", "name": f"Payment #{customer_id}-3", "type": "payment", "amount": 200.00, "date": "2025-04-01"},
            
            # Lesson nodes
            {"id": "l1", "name": "Piano Lesson 1", "type": "lesson", "date": "2025-03-05", "cycle": "March 2025"},
            {"id": "l2", "name": "Piano Lesson 2", "type": "lesson", "date": "2025-03-12", "cycle": "March 2025"},
            {"id": "l3", "name": "Piano Lesson 3", "type": "lesson", "date": "2025-03-19", "cycle": "March 2025"},
            {"id": "l4", "name": "Piano Lesson 4", "type": "lesson", "date": "2025-03-26", "cycle": "March 2025"},
            {"id": "l5", "name": "Piano Lesson 5", "type": "lesson", "date": "2025-04-02", "cycle": "April 2025"},
            {"id": "l6", "name": "Piano Lesson 6", "type": "lesson", "date": "2025-04-09", "cycle": "April 2025"},
        ]
        
        # Map node IDs to indices
        node_id_to_index = {node["id"]: i for i, node in enumerate(nodes)}
        
        # Create mock links between payments and lessons
        links = [
            # Payment 1 correctly applied to March lessons
            {"source": node_id_to_index["p1"], "target": node_id_to_index["l1"], "value": 60.00, "correct": True},
            {"source": node_id_to_index["p1"], "target": node_id_to_index["l2"], "value": 60.00, "correct": True},
            
            # Payment 2 correctly applied to March lessons
            {"source": node_id_to_index["p2"], "target": node_id_to_index["l3"], "value": 60.00, "correct": True},
            
            # Payment 2 incorrectly applied to April lesson (misapplication)
            {"source": node_id_to_index["p2"], "target": node_id_to_index["l5"], "value": 20.00, "correct": False},
            
            # Payment 3 correctly applied to April lessons
            {"source": node_id_to_index["p3"], "target": node_id_to_index["l6"], "value": 60.00, "correct": True},
            
            # Payment 3 incorrectly applied to March lessons (misapplication)
            {"source": node_id_to_index["p3"], "target": node_id_to_index["l4"], "value": 60.00, "correct": False},
        ]
        
        return {"nodes": nodes, "links": links}
    
    def _get_mock_timeline_data(self, customer_id: str) -> Dict[str, Any]:
        """Generate mock data for the timeline visualization."""
        # Create mock billing cycles
        cycles = [
            {"id": "c1", "name": "March 2025", "start_date": "2025-03-01", "end_date": "2025-03-31"},
            {"id": "c2", "name": "April 2025", "start_date": "2025-04-01", "end_date": "2025-04-30"},
        ]
        
        # Create mock events (payments and lessons)
        events = [
            # Payments
            {
                "id": "p1", "type": "payment", "date": "2025-03-01", 
                "description": f"Payment #{customer_id}-1: $120.00",
                "amount": 120.00,
                "connections": [
                    {"target": "l1", "amount": 60.00},
                    {"target": "l2", "amount": 60.00}
                ]
            },
            {
                "id": "p2", "type": "payment", "date": "2025-03-15", 
                "description": f"Payment #{customer_id}-2: $80.00",
                "amount": 80.00,
                "connections": [
                    {"target": "l3", "amount": 60.00},
                    {"target": "l5", "amount": 20.00, "misapplied": True}
                ]
            },
            {
                "id": "p3", "type": "payment", "date": "2025-04-01", 
                "description": f"Payment #{customer_id}-3: $200.00",
                "amount": 200.00,
                "connections": [
                    {"target": "l4", "amount": 60.00, "misapplied": True},
                    {"target": "l6", "amount": 60.00}
                ]
            },
            
            # Lessons
            {"id": "l1", "type": "lesson", "date": "2025-03-05", "description": "Piano Lesson 1 - $60.00", "cycle": "c1"},
            {"id": "l2", "type": "lesson", "date": "2025-03-12", "description": "Piano Lesson 2 - $60.00", "cycle": "c1"},
            {"id": "l3", "type": "lesson", "date": "2025-03-19", "description": "Piano Lesson 3 - $60.00", "cycle": "c1"},
            {"id": "l4", "type": "lesson", "date": "2025-03-26", "description": "Piano Lesson 4 - $60.00", "cycle": "c1", "misapplied": True},
            {"id": "l5", "type": "lesson", "date": "2025-04-02", "description": "Piano Lesson 5 - $60.00", "cycle": "c2", "misapplied": True},
            {"id": "l6", "type": "lesson", "date": "2025-04-09", "description": "Piano Lesson 6 - $60.00", "cycle": "c2"},
        ]
        
        return {"cycles": cycles, "events": events}
    
    def _generate_timeline_insights(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate insights from the timeline data."""
        insights = [
            {
                "type": "warning",
                "message": "Payment made on boundary dates (like the 1st of the month) often leads to misapplication issues."
            },
            {
                "type": "info",
                "message": "Payments made in the middle of billing cycles (like March 15) are less likely to be misapplied."
            },
            {
                "type": "warning",
                "message": "Payment #3 made on April 1 was incorrectly applied to a March lesson (previous billing cycle)."
            }
        ]
        
        return insights
    
    def _get_mock_network_data(self, customer_id: str) -> Dict[str, Any]:
        """Generate mock data for the network visualization."""
        # Use the same data structure as the payment flow data for simplicity
        return self._get_mock_payment_flow_data(customer_id)
