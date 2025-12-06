import json
import os
import pandas as pd
import random
import time
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure API
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not found in .env. Falling back to mock data.")

def get_gemini_response(prompt):
    """
    Sends a prompt to Gemini and acts as a wrapper for safety/errors.
    """
    if not API_KEY:
        return None
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"API Error: {e}")
        return None

def generate_debate_content(industry_name, status, metrics):
    """
    Generates debate content using either Gemini (if available) or Mock templates.
    """
    
    # --- PROMPT DESIGN ---
    prompt = f"""
    You are simulating a boardroom debate for a bank regarding the industry: '{industry_name}'.
    
    Context Data:
    - Overall Status: {status}
    - Key Metrics & History: 
    {metrics}
    
    Persona 1: CRO (Chief Risk Officer). Skeptical, matter-of-fact, focused on hard risks. MUST QUOTE SPECIFIC NUMBERS (e.g. "Debt ratio of X", "Bankruptcy rate is Y%", "Margins dropped to Z%"). Warns about liquidity and debt.
    Persona 2: CSO (Chief Strategy Officer). Visionary but data-driven. MUST QUOTE SPECIFIC NUMBERS (e.g. "Capex intensity of X%", "ArXiv papers count: Y"). Focuses on transformation potential (Investment + Science) vs stagnation.
    
    Generate a JSON response with exactly this structure (no markdown formatting):
    {{
        "CRO_Opinion": "3-4 sentences. Concrete, matter-of-fact risk assessment. Focus on financial stability (Liquidity, Debt, Margins).",
        "CSO_Opinion": "3-4 sentences. Concrete, strategic assessment. Focus on future potential (Investment, Innovation/ArXiv) and growth.",
        "Final_Verdict": "BUY" or "HOLD" or "REJECT"
    }}
    
    Rules:
    - If status is CRITICAL, Verdict must be REJECT.
    - If status is OPPORTUNITY, Verdict must be BUY.
    - Else HOLD or BUY based on your assessment.
    - LANGUAGE: POLISH.
    - Tone: Professional, concise, "matter-of-fact" (rzeczowy). No marketing fluff.
    - Reference specific metrics from the context.
    """
    
    # Try Real AI
    ai_response = get_gemini_response(prompt)
    
    if ai_response:
        try:
            # Clean up potential markdown formatting ```json ... ```
            clean_json = ai_response.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_json)
        except json.JSONDecodeError:
            print(f"JSON Parse Error for {industry_name}. Fallback to mock.")
            pass

    # --- FALLBACK MOCK ---
    cro_templates = [
        f"Ryzyko w branży {industry_name} jest niepokojące.",
        f"Koszty stałe w {industry_name} rosną. Zalecam ostrożność.",
        f"Zadłużenie {industry_name} to problem.",
    ]
    cso_templates = [
        f"Trendy dla {industry_name} są obiecujące.",
        f"Technologia zmienia {industry_name}. Widzę potencjał.",
        f"{industry_name} to innowacja.",
    ]
    
    verdict = "HOLD"
    if status == 'CRITICAL': verdict = 'REJECT'
    if status == 'OPPORTUNITY': verdict = 'BUY'
    
    return {
        "CRO_Opinion": random.choice(cro_templates),
        "CSO_Opinion": random.choice(cso_templates),
        "Final_Verdict": verdict
    }

def generate_debates():
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_path, 'data')
    assets_path = os.path.join(base_path, 'app', 'assets')
    
    # Load Real Data
    csv_path = os.path.join(data_path, 'processed_real_index.csv')
    if not os.path.exists(csv_path):
        print("Real index not found, falling back to mock file generation or error.")
        return

    df_full = pd.read_csv(csv_path)
    
    # Filter for MACRO Only (Sections)
    # Use full df for history retrieval
    df_macro_full = df_full[df_full['PKD_Code'].astype(str).str.startswith('SEK_')]
    
    # Target 2024 for main entries
    df_2024 = df_macro_full[df_macro_full['Year'] == 2024]
    
    debates = {}
    
    print(f"Starting generation for {len(df_2024)} Macro Industries using Gemini...")
    
    for index, row in df_2024.iterrows():
        pkd_code = str(row['PKD_Code'])
        industry_name = row['Industry_Name']
        status = row['Status']
        
        # --- GATHER HISTORY (2019-2024) ---
        history_df = df_macro_full[df_macro_full['PKD_Code'] == pkd_code].sort_values('Year')
        # Keep recent history
        history_recent = history_df[history_df['Year'] >= 2019]
        
        history_str = "Recent History (Year: Revenue | YoY | Profitability | Bankruptcy Rate):\n"
        for _, h_row in history_recent.iterrows():
            history_str += (f"- {h_row['Year']}: {h_row['Revenue']:,.0f}M PLN | "
                            f"{h_row['Dynamics_YoY']*100:+.1f}% YoY | "
                            f"Prof: {h_row['Profitability']*100:.1f}% | "
                            f"Bankrupt: {h_row['Bankruptcy_Rate']*100:.2f}%\n")
        
        # Prepare rich context
        metrics = f"""
        Current Year (2024) Snapshot:
        - Revenue: {row.get('Revenue', 0):,.2f} MLN PLN
        - Revenue YoY Change: {row.get('Dynamics_YoY', 0)*100:.2f}%
        - Net Profit Margin: {row.get('Net_Profit_Margin', 0):.2f}%
        - Profitability (share of profitable cos): {row.get('Profitability', 0)*100:.2f}%
        
        - Cash Ratio: {row.get('Cash_Ratio', 0):.2f}
        - Debt to Revenue: {row.get('Debt_to_Revenue', 0):.2f}x
        - Bankruptcy Rate: {row.get('Bankruptcy_Rate', 0):.2f}%
        
        - Investment (Capex): {row.get('Investment', 0):,.1f} MLN PLN
        - Capex Intensity: {row.get('Capex_Intensity', 0):.2f}%
        - Innovation (ArXiv Papers): {row.get('Arxiv_Papers', 0)}
        
        - S&T Score: Stability={row.get('Stability_Score', 0):.1f}, Transformation={row.get('Transformation_Score', 0):.1f}
        
        {history_str}
        """
        
        print(f"Processing: {industry_name} ({pkd_code})...")
        debates[pkd_code] = generate_debate_content(industry_name, status, metrics)
        
        # Simple rate limiting for free tier
        if API_KEY:
            time.sleep(5.0)
        
    # Save to JSON
    output_path = os.path.join(assets_path, 'ai_debates.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(debates, f, ensure_ascii=False, indent=2)
        
    print(f"Generated debates saved to {output_path}")

if __name__ == "__main__":
    generate_debates()
