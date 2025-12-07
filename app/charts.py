import plotly.graph_objects as go
import numpy as np
import pandas as pd

def create_risk_radar_chart(df):
    """Creates the Debt vs Risk Radar Chart."""
    fig_risk = go.Figure()
    
    if df.empty: return fig_risk

    # Data Prep: Ensure Debt to Revenue is calculated
    # Assuming df has 'Total_Debt' and 'Revenue'
    # Use 'Debt_to_Revenue' column if available, else calc
    if 'Debt_to_Revenue' not in df.columns:
        df['Debt_to_Revenue'] = df.apply(lambda x: x['Total_Debt'] / x['Revenue'] if x['Revenue'] > 0 else 0, axis=1)

    # Scatter Trace
    fig_risk.add_trace(go.Scatter(
        x=df['Debt_to_Revenue'],
        y=df['Bankruptcy_Rate'],
        mode='markers',
        text=df['Industry_Name'],
        customdata=np.stack((
            df['Revenue'], 
            df['Total_Debt'], 
            df['Dynamics_YoY'],
            df['PKD_Code']
        ), axis=-1),
        marker=dict(
            size=np.sqrt(df['Revenue']) / np.sqrt(df['Revenue'].max()) * 50 + 10,
            color=df['Dynamics_YoY'], 
            colorscale='RdYlGn', # Red = Low Growth/Shrinkage (Bad), Green = High Growth
            showscale=True,
            colorbar=dict(title="Dynamika R/R"),
            line=dict(width=1, color='white') # White border for contrast
        ),
        hovertemplate="<b>%{text}</b><br>" +
                      "PKD: %{customdata[3]}<br>" +
                      "Zadłużenie: %{x:.2f}x<br>" +
                      "Upadłości: %{y:.2f}%<br>" +
                      "Dynamika: %{customdata[2]:+.1%}<br>" +
                      "Przychody: %{customdata[0]:,.0f} mln<br>" +
                      "Dług: %{customdata[1]:,.0f} mln<extra></extra>"
    ))
    
    # Critical Zone (High Debt > 0.5x AND High Bankruptcy > 2%)
    # Just a visual rectangle
    fig_risk.add_shape(type="rect",
        x0=0.5, y0=1.0, x1=5.0, y1=100, # Assuming max debt around 5x visually
        line=dict(color="Red", width=1, dash="dash"),
        fillcolor="rgba(255, 0, 0, 0.1)"
    )
    
    # Axis Lines
    fig_risk.update_xaxes(zeroline=True, zerolinewidth=1, zerolinecolor='gray')
    fig_risk.update_yaxes(zeroline=True, zerolinewidth=1, zerolinecolor='gray')
    
    fig_risk.update_layout(
        xaxis_title="Zadłużenie (Dług / Przychody)",
        yaxis_title="Wskaźnik Upadłości (%)",
        height=600,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        title="<b>Mapa Ryzyka:</b> Dług (Oś X) vs Upadłość (Oś Y) | Kolor = Dynamika"
    )
    return fig_risk

def create_main_bubble_chart(df, max_revenue_global=None):
    """Creates the S&T Matrix Bubble Chart."""
    fig = go.Figure()
    
    if df.empty: return fig

    # Color mapping for Status
    color_map = {
        'CRITICAL': '#ff4b4b',
        'OPPORTUNITY': '#2ecc71',
        'Neutral': '#3498db'
    }

    # Use global max revenue if provided, else local max
    max_rev = max_revenue_global if max_revenue_global else df['Revenue'].max()
    if max_rev == 0: max_rev = 1
    
    for status in df['Status'].unique():
        subset = df[df['Status'] == status]
        if subset.empty: continue
        
        fig.add_trace(go.Scatter(
            x=subset['Stability_Score'],
            y=subset['Transformation_Score'],
            mode='markers', # Remove text for performance, show on hover
            text=subset['Industry_Name'], 
            marker=dict(
                size=np.sqrt(subset['Revenue'] / max_rev) * 100 + 5, # Sqrt scaling
                color=color_map.get(status, '#888'),
                opacity=0.8,
                line=dict(width=1, color='white')
            ),
            name=status,
            customdata=subset[['Industry_Name', 'Revenue', 'PKD_Code', 'Profitability']],
            hovertemplate="<b>%{customdata[0]}</b><br>" +
                          "PKD: %{customdata[2]}<br>" +
                          "Stability: %{x:.1f}<br>" +
                          "Transformation: %{y:.1f}<br>" +
                          "Revenue: %{customdata[1]:,.0f} mln PLN<extra></extra>"
        ))
        
    # Draw Quadrant Lines
    fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="Transformation Threshold")
    fig.add_vline(x=50, line_dash="dash", line_color="gray", annotation_text="Stability Threshold")

    fig.update_layout(
        xaxis_title="Stability Score (Fundament Finansowy)",
        yaxis_title="Transformation Score (Inwestycje + ArXiv AI)",
        xaxis=dict(autorange=True),
        yaxis=dict(autorange=True),
        height=700,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white")
    )
    
    return fig
