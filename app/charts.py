import plotly.graph_objects as go
import numpy as np
import pandas as pd

def create_risk_radar_chart(df):
    """Creates the Bankruptcy Risk Scatter Plot."""
    fig_risk = go.Figure()
    
    if df.empty: return fig_risk

    # Scatter Trace
    fig_risk.add_trace(go.Scatter(
        x=df['Dynamics_YoY'] * 100, # Percent
        y=df['Bankruptcy_Rate'],
        mode='markers',
        text=df['Industry_Name'],
        customdata=np.stack((
            df['Revenue'], 
            df['Total_Debt'], 
            df['Net_Profit'],
            df['PKD_Code']
        ), axis=-1),
        marker=dict(
            size=np.sqrt(df['Revenue']) / np.sqrt(df['Revenue'].max()) * 50 + 10,
            color=df['Bankruptcy_Rate'], 
            colorscale='RdYlGn_r', # Red-Yellow-Green REVERSED (High Risk = Red)
            showscale=True,
            colorbar=dict(title="Wskaźnik Upadłości (%)"),
            line=dict(width=1, color='DarkSlateGrey')
        ),
        hovertemplate="<b>%{text}</b><br>" +
                      "PKD: %{customdata[3]}<br>" +
                      "Upadłości: %{y:.2f}%<br>" +
                      "Dynamika: %{x:+.1f}%<br>" +
                      "Przychody: %{customdata[0]:,.0f} mln<br>" +
                      "Dług: %{customdata[1]:,.0f} mln<extra></extra>"
    ))
    
    # Critical Zone
    fig_risk.add_shape(type="rect",
        x0=-100, y0=1.0, x1=0, y1=100,
        line=dict(color="Red", width=1, dash="dash"),
        fillcolor="rgba(255, 0, 0, 0.1)"
    )
    
    # Annotation if data exists
    if not df.empty:
        max_bankrupt = df['Bankruptcy_Rate'].max()
        fig_risk.add_annotation(
            x=-5, y=max_bankrupt if max_bankrupt > 1.0 else 1.0,
            text="STREFA KRYTYCZNA",
            showarrow=False,
            font=dict(color="red", size=14)
        )
    
    fig_risk.update_layout(
        xaxis_title="Dynamika Przychodów R/R (%)",
        yaxis_title="Wskaźnik Upadłości (%)",
        xaxis=dict(zeroline=True, zerolinecolor='white'),
        yaxis=dict(zeroline=True, zerolinecolor='white'),
        height=600,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white")
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
