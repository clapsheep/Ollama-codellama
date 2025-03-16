import requests
import sys
import os
import time  # time 모듈 추가

class TestCodeGenerator:
    def __init__(self):
        self.api_base = "http://localhost:11434/api"
        
    def generate_test(self, source_code: str, source_path: str) -> str:
        # 시작 시간 기록
        start_time = time.time()
        
        # 소스 파일 경로에서 src/ 이후 부분을 추출
        import_path = source_path.split('src/')[-1]
        if import_path.endswith('.ts'):
            import_path = import_path[:-3]  # .ts 확장자 제거
        
        prompt = f"""Please generate Vitest test code for the following source code.

Important: Generate only TypeScript test code, not any other language.
Specifically, create test code for the functions defined in the source code.
Use vitest for testing.

- Exclude unnecessary explanations or comments
- DO NOT include any code block markers (```) or language indicators
- Generate only pure executable test code
- DO NOT include any markdown formatting
- DO NOT include any explanatory text

Please consider the following aspects when writing tests:
1. For date-related tests:
   - Consider edge cases for month-end/year-end
   - Utilize JavaScript Date object's automatic overflow handling
   - Use proper date calculation methods (e.g., setDate()) instead of simple arithmetic
   - Consider leap years

2. General test considerations:
   - Include edge cases as well as normal cases
   - Include tests for exception scenarios
   - Each test should verify only one behavior

3. Parameter handling:
   - Always provide valid values for all required parameters
   - For error case testing:
     - Fill all parameters with valid default values first
     - Then modify only the specific parameter being tested for error
     - Use expect().toThrow() or similar assertions for error cases

Write the test code starting directly with the imports, like this:

import {{ describe, it, expect }} from 'vitest';
import {{ functionName }} from '@/{import_path}';

describe('Test Suite Name', () => {{
    // Test cases
}});

Source code:
{source_code}"""

        response = requests.post(
            f"{self.api_base}/chat",
            json={
                "model": "codellama:7b",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "options": {
                    "temperature": 0.2,  # 온도값 낮춤 (더 결정적인 출력)
                    "top_p": 0.8,        # top_p 값도 조정
                    "max_tokens": 2000    # 최대 토큰 수 제한
                }
            }
        )
        
        # 종료 시간 기록 및 소요 시간 계산
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"API 요청 처리 시간: {elapsed_time:.2f}초")
        
        if response.status_code == 200:
            return response.json()["message"]["content"]
        else:
            raise Exception(f"API 호출 실패: {response.status_code}")

def main():
    if len(sys.argv) < 2:
        print("사용법: python code_generator.py <소스코드_파일_경로>")
        return
        
    source_path = sys.argv[1]
    generator = TestCodeGenerator()
    
    # 소스 파일 읽기
    with open(source_path, 'r') as file:
        source_code = file.read()
    
    # 테스트 파일 경로 생성
    test_path = source_path.replace('/utils/', '/__tests__/utils/').replace('.ts', '.test.ts')
    
    # __tests__ 디렉토리 생성
    os.makedirs(os.path.dirname(test_path), exist_ok=True)
    
    # 테스트 코드 생성
    test_code = generator.generate_test(source_code, source_path)
    
    # 테스트 파일 저장
    with open(test_path, 'w') as test_file:
        test_file.write(test_code)
        
    print(f"테스트 파일이 생성되었습니다: {test_path}")

if __name__ == "__main__":
    main() 
