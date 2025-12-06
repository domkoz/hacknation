import json
import os
import pandas as pd
import random

def generate_mock_debate(industry_name, status):
    """
    Generates a mock debate between CRO (Risk) and CSO (Strategy) based on industry status.
    """
    
    # Templates for CRO
    cro_templates = [
        "Ryzyko regulacyjne w {industry} jest niepokojące. Widzimy presję na marże.",
        "Koszty stałe w {industry} rosną szybciej niż przychody. Zalecam ostrożność.",
        "Wskaźniki zadłużenia dla {industry} są na granicy akceptowalności. Czy to bezpieczne?",
        "Nie podoba mi się cykliczność {industry}. W razie recesji będą pierwsi do windykacji."
    ]
    
    # Templates for CSO
    cso_templates = [
        "Ale spójrz na trendy! {industry} to przyszłość, musimy tam być zanim konkurencja wejdzie.",
        "Technologia zmienia {industry} nie do poznania. Widzę tu potencjał na 20% wzrostu.",
        "To jest 'Hidden Gem'. {industry} ma solidne podstawy i świetne perspektywy w erze AI.",
        "Nie bądźmy dinozaurami. {industry} to innowacja, którą klienci kochają."
    ]
    
    # Specific logic based on Status
    if status == 'CRITICAL':
        cro_opinion = f"To jest bomba z opóźnionym zapłonem! {industry_name} ma fatalną płynność. STOP."
        cso_opinion = f"Może i jest ryzyko, ale {industry_name} przechodzi restrukturyzację. Warto obserwować."
        verdict = "REJECT"
    elif status == 'OPPORTUNITY':
        cro_opinion = f"Finansowo {industry_name} wygląda stabilnie, choć martwi mnie zależność od cen energii."
        cso_opinion = f"To jest nasz czarny koń! {industry_name} idealnie wpisuje się w megatrendy. BUY!"
        verdict = "BUY"
    else: # Neutral
        cro_opinion = random.choice(cro_templates).format(industry=industry_name)
        cso_opinion = random.choice(cso_templates).format(industry=industry_name)
        verdict = "HOLD"
        
    return {
        "CRO_Opinion": cro_opinion,
        "CSO_Opinion": cso_opinion,
        "Final_Verdict": verdict
    }

def generate_debates():
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_path, 'data')
    assets_path = os.path.join(base_path, 'app', 'assets')
    
    # Load processed data
    df = pd.read_csv(os.path.join(data_path, 'processed_index.csv'))
    
    debates = {}
    
    for index, row in df.iterrows():
        pkd_code = str(row['PKD_Code'])
        industry_name = row['Industry_Name']
        status = row['Status']
        
        debates[pkd_code] = generate_mock_debate(industry_name, status)
        
    # Save to JSON
    output_path = os.path.join(assets_path, 'ai_debates.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(debates, f, ensure_ascii=False, indent=2)
        
    print(f"Generated debates for {len(debates)} industries. Saved to {output_path}")

if __name__ == "__main__":
    generate_debates()
