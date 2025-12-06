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
    - Key Metrics: {metrics}
    
    Persona 1: CRO (Chief Risk Officer). Skeptical, conservative, worried about debt and recession.
    Persona 2: CSO (Chief Strategy Officer). Optimistic, visionary, focused on growth and tech trends.
    
    Generate a JSON response with exactly this structure (no markdown formatting):
    {{
        "CRO_Opinion": "2 sentences from CRO perspective.",
        "CSO_Opinion": "2 sentences from CSO perspective.",
        "Final_Verdict": "BUY" or "HOLD" or "REJECT"
    }}
    
    Rules:
    - If status is CRITICAL, Verdict must be REJECT.
    - If status is OPPORTUNITY, Verdict must be BUY.
    - Else HOLD or BUY based on your assessment.
    - Speak professionally but with character.
    - Polish language.
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
    
    # Load processed data
    df = pd.read_csv(os.path.join(data_path, 'processed_index.csv'))
    
    debates = {}
    
    print(f"Starting generation for {len(df)} industries (Provider: {'Gemini' if API_KEY else 'MOCK'})...")
    
    for index, row in df.iterrows():
        pkd_code = str(row['PKD_Code'])
        industry_name = row['Industry_Name']
        status = row['Status']
        
        # Format metrics for context
        metrics = f"Profitability: {row.get('Profitability', 'N/A')}, Liquidity: {row.get('Liquidity', 'N/A')}"
        
        print(f"Processing: {industry_name}...")
        debates[pkd_code] = generate_debate_content(industry_name, status, metrics)
        
        # Rate limit protection (simple)
        if API_KEY:
            time.sleep(1.0)
        
    # Save to JSON
    output_path = os.path.join(assets_path, 'ai_debates.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(debates, f, ensure_ascii=False, indent=2)
        
    print(f"Generated debates saved to {output_path}")

if __name__ == "__main__":
    generate_debates()
