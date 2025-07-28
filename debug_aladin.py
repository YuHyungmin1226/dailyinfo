import requests
from bs4 import BeautifulSoup
import re

def debug_aladin_structure():
    """알라딘 웹사이트 구조 분석"""
    url = "https://www.aladin.co.kr/shop/common/wbest.aspx?BestType=NowBest&BranchType=2&CID=0&page=1&cnt=100&SortOrder=1"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        print("🔍 알라딘 웹사이트 구조 분석 중...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"📄 응답 상태 코드: {response.status_code}")
        print(f"📄 페이지 제목: {soup.title.string if soup.title else '제목 없음'}")
        
        # 1. 테이블 구조 확인
        print("\n📊 테이블 구조 분석:")
        tables = soup.find_all('table')
        print(f"테이블 개수: {len(tables)}")
        
        for i, table in enumerate(tables[:5]):  # 처음 5개 테이블만 확인
            print(f"\n테이블 {i+1}:")
            print(f"  클래스: {table.get('class', '클래스 없음')}")
            print(f"  ID: {table.get('id', 'ID 없음')}")
            
            # 테이블 내 tr 개수
            rows = table.find_all('tr')
            print(f"  행 개수: {len(rows)}")
            
            if rows:
                # 첫 번째 행의 셀 구조 확인
                first_row = rows[0]
                cells = first_row.find_all(['td', 'th'])
                print(f"  첫 번째 행 셀 개수: {len(cells)}")
                
                for j, cell in enumerate(cells[:3]):  # 처음 3개 셀만 확인
                    cell_text = cell.get_text(strip=True)
                    print(f"    셀 {j+1}: '{cell_text[:50]}...' (클래스: {cell.get('class', '클래스 없음')})")
        
        # 2. 특정 클래스명으로 요소 찾기
        print("\n🔍 특정 클래스명으로 요소 검색:")
        class_patterns = ['ss_book', 'book', 'bestseller', 'rank', 'title']
        
        for pattern in class_patterns:
            elements = soup.find_all(class_=lambda x: x and pattern in str(x).lower())
            print(f"'{pattern}' 포함 클래스: {len(elements)}개")
            
            if elements:
                for elem in elements[:2]:  # 처음 2개만 확인
                    print(f"  - {elem.name}: {elem.get('class')} - '{elem.get_text(strip=True)[:50]}...'")
        
        # 3. 전체 텍스트에서 패턴 찾기
        print("\n🔍 전체 텍스트에서 패턴 검색:")
        all_text = soup.get_text()
        
        # 순위 패턴 찾기
        rank_patterns = [
            r'(\d+)\s*([가-힣\s]+?)(?:\s+지음|\s+저|\s+편집|\s+글|\s+그림|\s+외)',
            r'순위\s*(\d+)[^가-힣]*([가-힣\s]+?)(?:\s+지음|\s+저|\s+편집|\s+글|\s+그림|\s+외)',
            r'(\d+)\s*([가-힣\s]+?)(?:\s*[가-힣]+?\s*지음|\s*[가-힣]+?\s*저|\s*[가-힣]+?\s*편집)',
        ]
        
        for i, pattern in enumerate(rank_patterns):
            matches = re.findall(pattern, all_text)
            print(f"패턴 {i+1}: {len(matches)}개 매치")
            if matches:
                for match in matches[:3]:  # 처음 3개만 출력
                    print(f"  - 순위: {match[0]}, 제목: {match[1][:30]}...")
        
        # 4. HTML 구조 일부 저장
        print("\n💾 HTML 구조 일부 저장 중...")
        with open('aladin_structure.html', 'w', encoding='utf-8') as f:
            f.write(str(soup)[:10000])  # 처음 10000자만 저장
        print("HTML 구조가 'aladin_structure.html' 파일에 저장되었습니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    debug_aladin_structure() 