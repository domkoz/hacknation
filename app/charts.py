import plotly.graph_objects as go
import numpy as np
import pandas as pd

def create_risk_radar_chart(df):
    """
    Creates the Debt vs Risk Radar Chart (Scatter).
    
    Axes:
        X: Debt to Revenue (Leverage).
        Y: Bankruptcy Rate (Risk).
        Color: Revenue Dynamics (YoY Growth).
        Size: Revenue.
        
    Args:
        df (pd.DataFrame): Data containing Debt, Revenue, Bankruptcy_Rate, etc.
        
    Returns:
        go.Figure: Plotly figure object.
    """
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
    """
    Creates the main S&T Matrix Bubble Chart.
    
    Axes:
        X: Stability Score (Profit, Growth, Safety).
        Y: Transformation Score (Capex, Innovation).
        Color: Status (Opportunity, Warning, Neutral).
        Size: Revenue.
    
    Args:
        df (pd.DataFrame): Data with pre-calculated Stability/Transformation Scores.
        max_revenue_global (float, optional): Max revenue for scaling bubble sizes consistently. 
        
    Returns:
        go.Figure: Plotly figure object.
    """
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

def create_historical_chart(df, metric_col, title, y_axis_title, is_percent=False):
    """Creates a historical line chart with forecast."""
    fig = go.Figure()
    
    if df.empty: return fig
    
    # Split Real vs Forecast
    # Note: We must ensure 'Is_Forecast' col exists or assume False
    if 'Is_Forecast' not in df.columns:
        df['Is_Forecast'] = False
        
    real_df = df[df['Is_Forecast'] == False]
    forecast_df = df[df['Is_Forecast'] == True]
    
    # Add Last Real Point to Forecast to make line continuous
    if not real_df.empty and not forecast_df.empty:
        last_real = real_df.iloc[-1]
        forecast_df = pd.concat([pd.DataFrame([last_real]), forecast_df], ignore_index=True)
        
    # Formatting
    y_format = ".1%" if is_percent else ".2f"
    
    # Real Trace
    fig.add_trace(go.Scatter(
        x=real_df['Year'],
        y=real_df[metric_col],
        mode='lines+markers',
        name='Historia',
        line=dict(color='#3498db', width=3),
        marker=dict(size=8),
        text=real_df[metric_col],
        hovertemplate=f"Rok: %{{x}}<br>{title}: %{{y:{y_format}}}<extra></extra>"
    ))
    
    # Forecast Trace
    if not forecast_df.empty:
        fig.add_trace(go.Scatter(
            x=forecast_df['Year'],
            y=forecast_df[metric_col],
            mode='lines+markers',
            name='Prognoza (AI)',
            line=dict(color='#f1c40f', width=3, dash='dot'),
            marker=dict(size=8, symbol='diamond-open'),
            text=forecast_df[metric_col],
            hovertemplate=f"Rok: %{{x}} (Prognoza)<br>{title}: %{{y:{y_format}}}<extra></extra>"
        ))
        
    fig.update_layout(
        title=title,
        xaxis_title="Rok",
        yaxis_title=y_axis_title,
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

    return fig

def create_st_time_chart(df):
    """
    Creates a time series chart showing S&T score history and forecast.
    X-Axis: Year
    Y-Axis: Score (0-100)
    Two lines: Stability and Transformation.
    """
    fig = go.Figure()
    
    if df.empty: return fig
    
    # Sort by Year
    df = df.sort_values('Year')
    
    # Split Real vs Forecast for distinct styling (solid vs dot)
    # Actually, simpler to just plot lines with different styling if possible, 
    # but creating separate traces for Real vs Forecast is clearer.
    
    if 'Is_Forecast' not in df.columns:
        df['Is_Forecast'] = False
        
    real_df = df[df['Is_Forecast'] == False]
    forecast_df = df[df['Is_Forecast'] == True]
    
    # Bridge the gap
    if not real_df.empty and not forecast_df.empty:
        last_real = real_df.iloc[-1]
        forecast_df = pd.concat([pd.DataFrame([last_real]), forecast_df], ignore_index=True)

    # --- STABILITY SCORE ---
    # Real
    fig.add_trace(go.Scatter(
        x=real_df['Year'], y=real_df['Stability_Score'],
        mode='lines+markers', name='Stability (Real)',
        line=dict(color='#29b6f6', width=3),
        marker=dict(size=8)
    ))
    # Forecast
    if not forecast_df.empty:
        fig.add_trace(go.Scatter(
            x=forecast_df['Year'], y=forecast_df['Stability_Score'],
            mode='lines+markers', name='Stability (Prognoza)',
            line=dict(color='#29b6f6', width=3, dash='dot'),
            marker=dict(size=8, symbol='diamond-open'),
            showlegend=False # Avoid clutter, or keep if clear
        ))

    # --- TRANSFORMATION SCORE ---
    # Real
    fig.add_trace(go.Scatter(
        x=real_df['Year'], y=real_df['Transformation_Score'],
        mode='lines+markers', name='Transformation (Real)',
        line=dict(color='#ab47bc', width=3),
        marker=dict(size=8)
    ))
    # Forecast
    if not forecast_df.empty:
        fig.add_trace(go.Scatter(
            x=forecast_df['Year'], y=forecast_df['Transformation_Score'],
            mode='lines+markers', name='Transformation (Prognoza)',
            line=dict(color='#ab47bc', width=3, dash='dot'),
            marker=dict(size=8, symbol='diamond-open'),
            showlegend=False
        ))

    fig.update_layout(
        title="Ewolucja Wyników S&T (2019-2026)",
        xaxis_title="Rok",
        yaxis_title="Wynik Punktowy (0-100)",
        yaxis=dict(range=[0, 100], showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
        
    return fig
