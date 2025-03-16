import requests
import json
import os
from typing import Dict, List, Optional

class CodeReviewer:
    def __init__(self):
        self.api_base = "http://localhost:11434/api"
        
    def review_code(self, source_code: str, file_path: str) -> Dict:
        """
        코드를 분석하고 리뷰 결과를 반환합니다.
        
        Args:
            source_code (str): 리뷰할 소스 코드
            file_path (str): 소스 코드 파일 경로
            
        Returns:
            Dict: 리뷰 결과를 포함하는 딕셔너리
        """
        prompt = f"""다음 코드를 검토하고 상세한 분석을 한글로 제공해주세요.
다음 주요 측면들에 집중해주세요:

1. 코드 품질:
   - 클린 코드 원칙
   - 코드 구조
   - 명명 규칙
   - 함수/메서드 길이
   - 코드 중복

2. 모범 사례:
   - TypeScript/JavaScript 모범 사례
   - 오류 처리
   - 성능 고려사항
   - 보안 고려사항

3. 잠재적 문제:
   - 버그 위험
   - 엣지 케이스
   - 오류 시나리오
   - 성능 병목

4. 구체적 제안:
   - 구체적인 코드 개선점
   - 대안적 접근 방법
   - 최적화 기회

다음 JSON 형식으로 검토 결과를 제공해주세요:
{{
    "summary": "코드 개요",
    "issues": [
        {{
            "severity": "high|medium|low",
            "category": "quality|security|performance|maintainability",
            "description": "문제 설명",
            "suggestion": "개선 방법",
            "line_numbers": [해당되는 줄 번호]
        }}
    ],
    "best_practices": [
        "코드에서 발견된 좋은 사례들"
    ],
    "suggestions": [
        "개선 제안 사항들"
    ]
}}

소스 코드 ({file_path}):
{source_code}
"""

        response = requests.post(
            f"{self.api_base}/chat",
            json={
                "model": "codellama:13b",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "top_p": 0.8,
                    "max_tokens": 2000
                }
            }
        )
        
        if response.status_code == 200:
            try:
                review_content = response.json()["message"]["content"]
                
                # 응답에서 JSON 부분만 추출하기 위한 처리
                try:
                    # 응답에서 첫 번째 '{' 부터 마지막 '}' 까지만 추출
                    json_start = review_content.find('{')
                    json_end = review_content.rfind('}') + 1
                    if json_start != -1 and json_end != -1:
                        json_content = review_content[json_start:json_end]
                        return json.loads(json_content)
                    
                except json.JSONDecodeError as e:
                    print(f"JSON 파싱 실패. 응답 내용: {review_content}")
                    # 기본 형식으로 응답 생성
                    return {
                        "summary": "코드 분석이 완료되었습니다.",
                        "issues": [
                            {
                                "severity": "medium",
                                "category": "quality",
                                "description": "리뷰 결과를 파싱하는 중 오류가 발생했습니다.",
                                "suggestion": "수동 검토가 필요합니다."
                            }
                        ],
                        "best_practices": [],
                        "suggestions": ["자동 리뷰 결과를 파싱할 수 없어 수동 검토가 필요합니다."]
                    }
            except Exception as e:
                print(f"예상치 못한 오류 발생: {str(e)}")
                print(f"전체 응답 내용: {response.text}")
                raise Exception("리뷰 응답 처리 중 오류가 발생했습니다.")
        else:
            raise Exception(f"API 호출 실패: {response.status_code}")
            
    def generate_markdown_report(self, review_result: Dict, file_path: str) -> str:
        """
        리뷰 결과를 마크다운 형식의 보고서로 변환합니다.
        """
        report = [
            f"# 코드 리뷰 보고서: {file_path}\n",
            f"## 요약\n{review_result['summary']}\n",
            
            "## 발견된 문제점\n"
        ]
        
        severity_labels = {
            "high": "심각",
            "medium": "중요",
            "low": "낮음"
        }
        
        category_labels = {
            "quality": "코드 품질",
            "security": "보안",
            "performance": "성능",
            "maintainability": "유지보수성"
        }
        
        for issue in review_result["issues"]:
            severity_emoji = {
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢"
            }.get(issue["severity"], "⚪")
            
            category = category_labels.get(issue["category"], issue["category"])
            severity = severity_labels.get(issue["severity"], issue["severity"])
            
            report.append(
                f"### {severity_emoji} {category} ({severity})\n"
                f"- **설명**: {issue['description']}\n"
                f"- **제안**: {issue['suggestion']}\n"
                + (f"- **해당 줄**: {', '.join(map(str, issue['line_numbers']))}\n" 
                   if issue.get('line_numbers') else "")
                + "\n"
            )
            
        if review_result.get("best_practices"):
            report.append("## 발견된 모범 사례\n")
            for practice in review_result["best_practices"]:
                report.append(f"- ✅ {practice}\n")
            report.append("\n")
            
        if review_result.get("suggestions"):
            report.append("## 개선 제안\n")
            for suggestion in review_result["suggestions"]:
                report.append(f"- 💡 {suggestion}\n")
                
        return "".join(report)

def main():
    if len(sys.argv) < 2:
        print("Usage: python code_reviewer.py <source_code_file_path>")
        return
        
    source_path = sys.argv[1]
    reviewer = CodeReviewer()
    
    # 소스 파일 읽기
    with open(source_path, 'r') as file:
        source_code = file.read()
    
    # 리뷰 수행
    try:
        review_result = reviewer.review_code(source_code, source_path)
        
        # 마크다운 리포트 생성
        report = reviewer.generate_markdown_report(review_result, source_path)
        
        # 리포트 파일 저장
        report_path = f"{source_path}.review.md"
        with open(report_path, 'w') as report_file:
            report_file.write(report)
            
        print(f"Review report generated: {report_path}")
        
    except Exception as e:
        print(f"Error during code review: {str(e)}")

if __name__ == "__main__":
    import sys
    main() 
