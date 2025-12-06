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
    
    Persona 1: CRO (Chief Risk Officer). Skeptical, conservative. MUST QUOTE SPECIFIC NUMBERS (e.g. "Revenue dropped by X%", "Bankruptcy rate is Y%"). Warns about negative trends in history.
    Persona 2: CSO (Chief Strategy Officer). Optimistic, visionary. MUST QUOTE SPECIFIC NUMBERS (e.g. "Profitability of Z%", "Growth in 2021"). Focuses on transformation potential despite risks.
    
    Generate a JSON response with exactly this structure (no markdown formatting):
    {{
        "CRO_Opinion": "3-4 sentences. Start with a strong warning. Use data from the context to justify fear.",
        "CSO_Opinion": "3-4 sentences. Start with a strategic opportunity. Use data to justify growth potential.",
        "Final_Verdict": "BUY" or "HOLD" or "REJECT"
    }}
    
    Rules:
    - If status is CRITICAL, Verdict must be REJECT.
    - If status is OPPORTUNITY, Verdict must be BUY.
    - Else HOLD or BUY based on your assessment.
    - LANGUAGE: POLISH.
    - Be detailed and specific. Do not use generic phrases.
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
        - Revenue: {row['Revenue']:,.2f} MLN PLN
        - Revenue YoY Change: {row['Dynamics_YoY']*100:.2f}%
        - Profitability (share of profitable cos): {row['Profitability']*100:.2f}%
        - Bankruptcy Rate: {row['Bankruptcy_Rate']*100:.2f}% (Count: {row['Bankruptcy_Count']})
        - Total Entities: {row['Entity_Count']}
        - S&T Score: Stability={row['Stability_Score']:.1f}, Transformation={row['Transformation_Score']:.1f}
        
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
