import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
import os

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="S&T Index Boardroom",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD ASSETS ---
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

try:
    # Adjust path if running locally from root
    css_path = os.path.join(os.path.dirname(__file__), 'assets/style.css')
    load_css(css_path)
except FileNotFoundError:
    st.warning("CSS file not found.")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    # Adjust path
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_path, 'data')
    # Use REAL data now
    processed_path = os.path.join(data_path, 'processed_real_index.csv')
    return pd.read_csv(processed_path)

# @st.cache_data (Disabled to force reload of real debates)
def load_debates():
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_path = os.path.join(base_path, 'app', 'assets')
    json_path = os.path.join(assets_path, 'ai_debates.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

try:
    df_all = load_data()
    debates = load_debates()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=PKO+Mock+Logo", use_container_width=True) # Replace with real logo if available
    st.title("S&T Dashboard")
    
    # --- TIME SLIDER (New!) ---
    min_year = int(df_all['Year'].min())
    max_year = int(df_all['Year'].max())
    
    selected_year = st.slider("Wybierz Rok:", min_value=min_year, max_value=max_year, value=max_year)
    
    st.divider()
    
    # Filter by Year first
    df = df_all[df_all['Year'] == selected_year].copy()
    
    # --- LEVEL OF DETAIL ---
    level_map = {
        "Sekcje (Makro)": "L1",
        "Działy (2 cyfry)": "L2",
        "Grupy (3 cyfry)": "L3",
        "Klasy (4 cyfry)": "L4"
    }
    selected_level_label = st.radio("Poziom Szczegółowości:", list(level_map.keys()), index=1)
    selected_level = level_map[selected_level_label]
    
    # Filter Logic
    if selected_level == "L1":
        # Sections (SEK_A, SEK_B...)
        df = df[df['PKD_Code'].astype(str).str.startswith('SEK_')]
    elif selected_level == "L2":
        # Divisions (01., 02. -> Length 3)
        df = df[(df['PKD_Code'].astype(str).str.len() == 3) & (~df['PKD_Code'].astype(str).str.startswith('SEK'))]
    elif selected_level == "L3":
        # Groups (01.1 -> Length 4)
        df = df[df['PKD_Code'].astype(str).str.len() == 4]
    elif selected_level == "L4":
        # Classes (01.11 -> Length 5, excluding SEK_)
        df = df[(df['PKD_Code'].astype(str).str.len() == 5) & (~df['PKD_Code'].astype(str).str.startswith('SEK'))]
    
    # Sector Filter (using first digit of PKD as proxy if Sector col mock is gone, or using the new Sector col if available)
    # The new real index script assigns "Ogólny" or we can infer.
    # Let's try to extract Sector from Industry Name to make it cooler or just show top 100 to avoid lag.
    
    # Ensure Sector column exists, if not fill it
    if 'Sector' not in df.columns:
        df['Sector'] = 'All'
        
    unique_sectors = sorted(df['Sector'].unique())
    selected_sector = st.selectbox("Wybierz Sektor:", ["Wszystkie"] + list(unique_sectors))
    
    if selected_sector != "Wszystkie":
        filtered_df = df[df['Sector'] == selected_sector]
    else:
        filtered_df = df

    # Revenue Filter
    min_rev_val = int(df['Revenue'].min())
    max_rev_val = int(df['Revenue'].max())
    
    # Defaults: Show top 50% by default if possible, or full range
    revenue_threshold = st.slider("Minimalne Przychody (mln PLN):", min_value=min_rev_val, max_value=max_rev_val, value=min_rev_val)
    
    filtered_df = filtered_df[filtered_df['Revenue'] >= revenue_threshold]

    st.info("💡 **Instrukcja:** Kliknij w bąbelek na wykresie, aby zobaczyć debatę Zarządu.")
    st.caption(f"Dane dla roku: {selected_year}. Liczba branż: {len(filtered_df)}")


# --- MAIN LAYOUT ---
st.title(f"S&T Index ({selected_year})")
st.markdown("### `System Diagnostyki Branżowej AI PKO BP` (Real Data)")

col_main, col_details = st.columns([2, 1])

# --- CHART (LEFT) ---
with col_main:
    # Create Bubble Chart using Plotly Graph Objects for more control
    fig = go.Figure()

    # Color mapping for Status
    color_map = {
        'CRITICAL': '#ff4b4b',
        'OPPORTUNITY': '#2ecc71',
        'Neutral': '#3498db'
    }

    # Add traces for different statuses to allow legend
    for status in df['Status'].unique():
        subset = filtered_df[filtered_df['Status'] == status]
        if subset.empty: continue
        
        # Scale size logic (Real revenue is HUGE, need log or sqrt scaling for visual sanity)
        # Or just normalization.
        # Let's use simple scaling factor.
        max_rev = df_all['Revenue'].max()
        if max_rev == 0: max_rev = 1
        
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
        yaxis_title="Transformation Score (Potencjał + Hype)",
        xaxis=dict(range=[0, 100]),
        yaxis=dict(range=[0, 100]),
        height=700,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white")
    )

    # Display Chart
    st.plotly_chart(fig, use_container_width=True, key="bubble_chart", on_select="rerun", selection_mode="points")


# --- DETAILS (RIGHT + BOTTOM) ---
with col_details:
    st.subheader("AI Boardroom")
    
    # Check if a point is selected
    selection = st.session_state.get("bubble_chart", {}).get("selection", {}).get("points", [])
    
    selected_pkd = None
    selected_row = None
    
    if selection:
        point = selection[0]
        x_val = point['x']
        y_val = point['y']
        
        # Find exact match
        # Note: filtered_df matches the chart.
        possible_rows = filtered_df[
            (abs(filtered_df['Stability_Score'] - x_val) < 0.001) & 
            (abs(filtered_df['Transformation_Score'] - y_val) < 0.001)
        ]
        
        if not possible_rows.empty:
            selected_row = possible_rows.iloc[0]
            selected_pkd = str(selected_row['PKD_Code'])
            industry_name = selected_row['Industry_Name']
            
            st.markdown(f"#### {industry_name}")
            st.caption(f"PKD: {selected_pkd}")
            
            # Metrics Row
            m1, m2 = st.columns(2)
            m1.metric("Stability", f"{selected_row['Stability_Score']:.1f}", delta_color="normal")
            m2.metric("Transformation", f"{selected_row['Transformation_Score']:.1f}", delta_color="normal")
            
            # Detailed Breakdown
            with st.expander("📊 Szczegóły Wyliczeń"):
                st.markdown(f"""
                **Składowe Stability Score:**
                - Rentowność: `{selected_row.get('Profitability', 0)*100:.2f}%`
                - Dynamika R/R: `{selected_row.get('Dynamics_YoY', 0)*100:.2f}%`
                
                **Inne:**
                - Przychody: `{selected_row.get('Revenue', 0):,.2f}` mln PLN
                - Upadłości: `{selected_row.get('Bankruptcy_Rate', 0):.2f}%`
                """)
            
            st.divider()
            
            # Debate Content
            debate = debates.get(selected_pkd)
            if debate:
                st.markdown(f"""
                <div class="cro-bubble">
                    <strong>👩‍💼 CRO:</strong> "{debate['CRO_Opinion']}"
                </div>
                <div class="cso-bubble">
                    <strong>🚀 CSO:</strong> "{debate['CSO_Opinion']}"
                </div>
                <div class="verdict-box {'verdict-buy' if debate['Final_Verdict']=='BUY' else 'verdict-reject' if debate['Final_Verdict']=='REJECT' else 'verdict-hold'}">
                    WERDYKT: {debate['Final_Verdict']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Brak debaty (AI odpoczywa).")
                
    else:
        st.write("👈 Kliknij bąbelek!")

# --- RECURSIVE DRILL DOWN SECTION ---
current_selection_pkd = selected_pkd
level_depth = 0
max_depth = 3 # Safety break

while current_selection_pkd and level_depth < max_depth:
    st.divider()
    
    # Get details for current selection
    # Need to find row for current_selection_pkd in df_all (for correct Year)
    # We use df_all because child might not be in the initial 'filtered_df' if user filtered by something else, 
    # but logically drill down should show global context.
    
    current_row_df = df_all[(df_all['PKD_Code'] == current_selection_pkd) & (df_all['Year'] == selected_year)]
    if current_row_df.empty:
        break
        
    current_row = current_row_df.iloc[0]
    st.markdown(f"### 📉 Poziom {level_depth + 1}: `{current_row['Industry_Name']}`")
    
    col_hist, col_sub = st.columns(2)
    
    # 1. HISTORY CHART
    with col_hist:
        st.caption(f"Historia: {current_selection_pkd}")
        hist_df = df_all[df_all['PKD_Code'] == current_selection_pkd].sort_values('Year')
        if not hist_df.empty:
            fig_h = go.Figure()
            fig_h.add_trace(go.Scatter(x=hist_df['Year'], y=hist_df['Revenue'], name='Przychody', line=dict(color='#3498db')))
            fig_h.update_layout(height=300, margin=dict(l=0,r=0,t=20,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
            st.plotly_chart(fig_h, use_container_width=True, key=f"hist_{level_depth}_{current_selection_pkd}")
            
    # 2. CHILDREN CHART
    next_selection = None
    with col_sub:
        st.caption(f"Składowe: {current_selection_pkd}")
        
        children_df = pd.DataFrame()
        
        # --- FIND CHILDREN LOGIC ---
        if current_selection_pkd.startswith('SEK_'):
             # Section Logic
            section_char = current_selection_pkd.split('_')[1]
            ranges = {
                'A': (1, 3), 'B': (5, 9), 'C': (10, 33), 'D': (35, 35), 'E': (36, 39),
                'F': (41, 43), 'G': (45, 47), 'H': (49, 53), 'I': (55, 56), 'J': (58, 63),
                'K': (64, 66), 'L': (68, 68), 'M': (69, 75), 'N': (77, 82), 'O': (84, 84),
                'P': (85, 85), 'Q': (86, 88), 'R': (90, 93), 'S': (94, 96)
            }
            if section_char in ranges:
                start, end = ranges[section_char]
                l2_candidates = df_all[
                    (df_all['Year'] == selected_year) & 
                    (df_all['PKD_Code'].str.len() == 3) & 
                    (~df_all['PKD_Code'].str.startswith('SEK'))
                ].copy()
                def get_prefix(code):
                    try: return int(str(code)[:2])
                    except: return -1
                l2_candidates['Prefix'] = l2_candidates['PKD_Code'].apply(get_prefix)
                children_df = l2_candidates[(l2_candidates['Prefix'] >= start) & (l2_candidates['Prefix'] <= end)]
        else:
            # Standard Logic
            # 01. (3) -> 01.x (4) | 01.1 (4) -> 01.xx (5)
            curr_len = len(current_selection_pkd)
            target_len = 0
            if curr_len == 3: target_len = 4
            elif curr_len == 4: target_len = 5
            
            if target_len:
                child_candidates = df_all[
                    (df_all['Year'] == selected_year) & 
                    (df_all['PKD_Code'].str.startswith(current_selection_pkd)) &
                    (df_all['PKD_Code'].str.len() == target_len)
                ].copy()
                children_df = child_candidates
        
        # --- RENDER SUB CHART ---
        if not children_df.empty:
            fig_sub = go.Figure()
            max_rev_sub = children_df['Revenue'].max()
            if max_rev_sub == 0: max_rev_sub = 1
            
            fig_sub.add_trace(go.Scatter(
                x=children_df['Stability_Score'],
                y=children_df['Transformation_Score'],
                mode='markers',
                text=children_df['Industry_Name'],
                marker=dict(
                    size=np.sqrt(children_df['Revenue'] / max_rev_sub) * 60 + 10,
                    color=children_df['Status'].map(color_map).fillna('#888'),
                    line=dict(width=1, color='white')
                ),
                customdata=children_df[['PKD_Code']], # Pass PKD for selection
                hovertemplate="<b>%{text}</b><extra></extra>"
            ))
            
            fig_sub.update_layout(
                xaxis=dict(range=[0, 100], showgrid=False, zeroline=False),
                yaxis=dict(range=[0, 100], showgrid=False, zeroline=False),
                height=300,
                margin=dict(l=0,r=0,t=0,b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                showlegend=False,
                font=dict(color='white')
            )
            
            # UNIQUE KEY for each level to capture selection
            chart_key = f"drill_chart_{level_depth}_{current_selection_pkd}"
            st.plotly_chart(fig_sub, use_container_width=True, key=chart_key, on_select="rerun", selection_mode="points")
            
            # CHECK SELECTION
            sub_sel = st.session_state.get(chart_key, {}).get("selection", {}).get("points", [])
            if sub_sel:
                # Find which point
                p = sub_sel[0]
                # Match by index or coordinate. 
                # Plotly selection returns pointIndex which corresponds to dataframe index IF reset.
                # Safer: Match x/y or use pointIndex if we ensure order.
                # "pointIndex" is reliable if we used 1 trace and didn't shuffle.
                # We used 1 trace here!
                
                try:
                    next_pkd_code = children_df.iloc[p['point_index']]['PKD_Code']
                    next_selection = next_pkd_code
                except:
                    pass
        else:
            st.write("Brak podkategorii.")
            
    # Advance loop
    if next_selection:
        current_selection_pkd = next_selection
        level_depth += 1
    else:
        break

