import json
import os
import pandas as pd
import random
import time
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import requests

# Configure API
API_KEY = os.getenv("GEMINI_API_KEY")
USE_OLLAMA = True # Force Ollama for now as per user request
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma2"

if API_KEY and not USE_OLLAMA:
    genai.configure(api_key=API_KEY)
else:
    print("Using Local LLM (Ollama).")

def get_ollama_response(prompt):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json" # Force JSON mode if model supports it, gemma might need help
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        text = response.json()['response']
        # Strip <think> blocks common in R1 models
        if "<think>" in text:
            text = text.split("</think>")[-1].strip()
        return text
    except Exception as e:
        print(f"Ollama Error: {e}")
        return None

def get_gemini_response(prompt):
    """
    Sends a prompt to Gemini and acts as a wrapper for safety/errors.
    """
    if not API_KEY:
        return None
    
    model = genai.GenerativeModel('models/gemini-2.0-flash-lite')
    response = model.generate_content(prompt)
    return response.text

def generate_debate_content(industry_name, status, metrics):
    """
    Generates debate content using either Gemini (if available) or Mock templates.
    """
    
    # --- INTERNAL HELPER FOR SPECIALIST ---
    def get_specialist_opinion(industry, metrics_text, forecast_text):
        prompt_spec = f"""
        Role: Industry Specialist for '{industry}'.
        Task: Provide a concise, insider commentary on the current state of this industry in Poland (2024).
        
        Data Context:
        {metrics_text}
        {forecast_text}
        
        Output Format:
        JSON object with a single key "opinion".
        Exmaple: {{ "opinion": "Twoja opinia..." }}
        
        Content Instructions:
        Focus on specific operational challenges or opportunities relevant to {industry} (e.g. supply chain, labor costs, technology adoption).
        Write in POLISH.
        """
        raw_resp = ""
        if USE_OLLAMA:
            raw_resp = get_ollama_response(prompt_spec)
        else:
            raw_resp = get_gemini_response(prompt_spec)
            
        if raw_resp:
            try:
                # Cleanup and parse
                clean = raw_resp.replace('```json', '').replace('```', '').strip()
                data = json.loads(clean)
                return data.get("opinion", raw_resp)
            except:
                return raw_resp
        return "Brak opinii."

    # 1. Get Specialist Opinion first
    specialist_opinion = get_specialist_opinion(industry_name, metrics, "")
    
    # 2. Generate Board Debate with Context
    prompt = f"""
    You are simulating a boardroom debate for a bank regarding the industry: '{industry_name}'.
    
    Context Data:
    - Overall Status: {status}
    - Key Metrics & History: 
    {metrics}
    
    *** SPECIALIST OPINION ***
    An industry expert stated: "{specialist_opinion}"
    **************************
    
    Persona 1: CRO (Chief Risk Officer). Skeptical. MUST QUOTE SPECIFIC NUMBERS.
    *INSTRUCTION*: Start your opinion by referring to the Specialist's claim (agree or disagree), then add your risk analysis.
    
    Persona 2: CSO (Chief Strategy Officer). Visionary. MUST QUOTE SPECIFIC NUMBERS.
    *INSTRUCTION*: Start your opinion by referring to the Specialist's claim (agree or refute), then add your opportunity analysis.
    
    Generate a valid JSON object. Do not use Markdown.
    
    Output Format:
    {{
        "Specialist_Opinion": "{specialist_opinion}",
        "CRO_Opinion": "Odnosząc się do specjalisty... [reszta opinii]",
        "CSO_Opinion": "W nawiązaniu do eksperta... [reszta opinii]",
        "Final_Verdict": "BUY/HOLD/REJECT",
        "Credit_Recommendation": "INCREASE_EXPOSURE/MAINTAIN/MONITOR/DECREASE_EXPOSURE",
        "Recommendation_Rationale": "Uzasadnienie..."
    }}
    
    INSTRUCTIONS:
    1. WRITE IN POLISH.
    2. Respond to the Specialist.
    3. CRO mentions Debt/Bankruptcy.
    4. CSO mentions Innovation/Capex.
    """
    
    # Try Real AI
    if USE_OLLAMA:
        ai_response = get_ollama_response(prompt)
    else:
        ai_response = get_gemini_response(prompt)
    
    if ai_response:
        try:
            clean_json = ai_response.replace('```json', '').replace('```', '').strip()
            data = json.loads(clean_json)
            # Ensure Specialist Opinion is passed through if AI forgot it
            if "Specialist_Opinion" not in data or not data["Specialist_Opinion"]:
                data["Specialist_Opinion"] = specialist_opinion
            return data
        except json.JSONDecodeError:
            print(f"JSON Parse Error. Fallback.")
            pass

    # --- FALLBACK MOCK ---
    return {
        "Specialist_Opinion": f"Branża {industry_name} boryka się z problemami podażowymi.",
        "CRO_Opinion": f"Zgadzam się z ekspertem. Ryzyko w branży {industry_name} jest niepokojące.",
        "CSO_Opinion": f"Mimo uwag eksperta, trendy dla {industry_name} są obiecujące.",
        "Final_Verdict": "HOLD",
        "Credit_Recommendation": "MONITOR",
        "Recommendation_Rationale": "Brak danych."
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
    output_path = os.path.join(assets_path, 'ai_debates.json')
    
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
        
        # --- GET FORECAST (2026) ---
        forecast_row = df_full[(df_full['PKD_Code'] == pkd_code) & (df_full['Year'] == 2026) & (df_full['Is_Forecast'] == True)]
        
        forecast_context = "Forecast (2025-2026): Not available."
        
        if not forecast_row.empty:
            rev_2026 = forecast_row.iloc[0]['Revenue']
            rev_2024 = row.get('Revenue', 1)
            growth_24_26 = ((rev_2026 - rev_2024) / rev_2024) * 100
            
            forecast_context = f"""
            FORECAST 2026 (Linear Model):
            - Revenue 2026: {rev_2026:,.1f} MLN PLN
            - Growth 2024->2026: {growth_24_26:+.2f}%
            """
        
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
        
        {forecast_context}
        """
        
        print(f"Processing: {industry_name} ({pkd_code})...")
        
        # Retry Logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                debates[pkd_code] = generate_debate_content(industry_name, status, metrics)
                break # Success
            except Exception as e:
                print(f"Error generating for {industry_name}: {e}")
                if "429" in str(e) or "Resource has been exhausted" in str(e):
                    wait_time = 30 * (attempt + 1)
                    print(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print("Non-rate-limit error. Skipping.")
                    break
        
        # Simple rate limiting for free tier
        if not USE_OLLAMA and API_KEY:
            time.sleep(15.0) # Increased base sleep to be safe
        
        # Save Incrementally
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(debates, f, ensure_ascii=False, indent=2)
            print(f"Saved progress for {pkd_code}")
        
    print(f"Generated debates saved to {output_path}")

if __name__ == "__main__":
    generate_debates()
