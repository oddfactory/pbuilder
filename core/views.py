import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import SystemSettings, PromptHistory
import requests

def index(request):
    return render(request, 'index.html')

def build_data_spec_markdown(data_spec_json):
    try:
        specs = json.loads(data_spec_json)
        dim = specs.get('dim', [])
        seg = specs.get('seg', [])
        met = specs.get('met', [])
        
        md = ""
        if dim:
            md += f"* **기준(차원):** {', '.join(dim)}\n"
        if seg:
            md += f"* **타겟팅/분류(세그먼트):** {', '.join(seg)}\n"
        if met:
            md += f"* **성과/효율(메트릭):** {', '.join(met)}\n"
            
        # Add formula hints automatically for efficiency metrics
        formulas = []
        if 'ROAS' in met:
            formulas.append("  - **ROAS 계산 공식:** (전환값 합계 / 광고비용 합계) * 100")
        if 'CTR' in met:
            formulas.append("  - **CTR 계산 공식:** (클릭수 합계 / 노출수 합계) * 100")
        if 'CPC' in met:
            formulas.append("  - **CPC 계산 공식:** (광고비용 합계 / 클릭수 합계)")
        if 'CPA' in met:
            formulas.append("  - **CPA 계산 공식:** (광고비용 합계 / 전환수 합계)")
        if 'CVR' in met:
            formulas.append("  - **CVR 계산 공식:** (전환수 합계 / 클릭수 합계) * 100")
            
        if formulas:
            md += "\n" + "\n".join(formulas)
            
        return md.strip()
    except:
        return data_spec_json

def generate_fallback_prompt(data):
    role = data.get('role', '')
    data_spec_raw = data.get('data_spec', '')
    core_layout = data.get('core_layout', '')
    tech_stack = data.get('tech_stack', '')
    
    data_spec_formatted = build_data_spec_markdown(data_spec_raw)

    prompt = f"""## 1. 역할 부여
{role} 이 대시보드를 사용할 실무자의 니즈를 정확히 파악하여, 실무에서 즉시 활용할 수 있는 직관적이고 분석적인 코드를 작성해야 해.

## 2. 데이터 명세 및 계산 로직
{data_spec_formatted}

## 3. UI/UX 및 시각화 요구사항
{core_layout}

## 4. 기술 스택
* **선택된 스택:** {tech_stack}

## 5. 최종 지시사항
1. 위의 요구사항을 완벽히 만족하는 전체 대시보드 소스 코드를 작성할 것.
2. 모던하고 미려한 디자인(깔끔한 여백, 시인성 높은 컬러 팔레트)을 적용할 것.
3. 제공된 코드는 즉시 복사하여 실행할 수 있도록 완벽한 형태일 것.
4. 각 차트 컴포넌트와 데이터 전처리 로직(가중평균 계산 등)에는 시니어 레벨의 상세한 주석을 달아줄 것.
"""
    return prompt

def generate_gemini_prompt(api_key, data):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    role = data.get('role', '')
    data_spec_raw = data.get('data_spec', '')
    core_layout = data.get('core_layout', '')
    tech_stack = data.get('tech_stack', '')
    
    data_spec_formatted = build_data_spec_markdown(data_spec_raw)

    system_prompt = """당신은 프롬프트 엔지니어링 전문가입니다. 사용자가 입력한 요구사항을 바탕으로, AI 모델(Claude, ChatGPT 등)이 대시보드 개발을 완벽히 수행할 수 있도록 지시하는 '최고급 마크다운 프롬프트'를 생성해주세요.

반드시 아래의 마크다운 계층 구조와 형태를 그대로 유지하면서, 내용을 더욱 구체적이고 전문적으로 보강하여 출력해야 합니다.
코드 블록 내부에서 마크다운 서식(`##`, `*`, `**`)이 깨지지 않도록 이스케이프 처리에 유의하세요.

## 1. 역할 부여
## 2. 데이터 명세 및 계산 로직
## 3. UI/UX 및 시각화 요구사항
## 4. 기술 스택
## 5. 최종 지시사항"""

    user_input = f"역할: {role}\n데이터 스펙:\n{data_spec_formatted}\n\n레이아웃 매칭(다중 지표 조합):\n{core_layout}\n\n기술 스택: {tech_stack}\n\n이 정보를 바탕으로, AI가 완벽한 대시보드 코드를 짤 수 있도록 구체적이고 체계적인 프롬프트를 만들어주세요."

    payload = {
        "contents": [
            {
                "parts": [{"text": system_prompt + "\n\n" + user_input}]
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        result = response.json()
        generated_text = result['candidates'][0]['content']['parts'][0]['text']
        return generated_text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return None

@csrf_exempt
def generate_prompt(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body)
        
        settings = SystemSettings.get_settings()
        api_key = settings.gemini_api_key

        generated_prompt = None

        if api_key:
            generated_prompt = generate_gemini_prompt(api_key, data)
        
        # Fallback
        if not generated_prompt:
            generated_prompt = generate_fallback_prompt(data)

        # Save to history
        PromptHistory.objects.create(
            role=data.get('role', ''),
            data_spec=data.get('data_spec', ''),
            core_layout=data.get('core_layout', ''),
            tech_stack=data.get('tech_stack', ''),
            generated_prompt=generated_prompt
        )

        return JsonResponse({'prompt': generated_prompt})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
