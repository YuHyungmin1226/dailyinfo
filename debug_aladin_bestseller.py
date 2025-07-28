import requests
from bs4 import BeautifulSoup
import re

def debug_aladin_bestseller():
    """알라딘 실제 베스트셀러 데이터 찾기"""
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
        print("🔍 알라딘 실제 베스트셀러 데이터 찾기...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. 테이블에서 베스트셀러 데이터 찾기
        print("\n📊 테이블에서 베스트셀러 데이터 찾기:")
        tables = soup.find_all('table')
        
        for i, table in enumerate(tables):
            table_text = table.get_text(strip=True)
            
            # 베스트셀러 관련 키워드가 있는 테이블 찾기
            if any(keyword in table_text for keyword in ['베스트', '순위', '1위', '2위', '3위']):
                print(f"\n테이블 {i+1} (베스트셀러 관련):")
                print(f"  클래스: {table.get('class', '클래스 없음')}")
                print(f"  ID: {table.get('id', 'ID 없음')}")
                
                # 테이블 행 분석
                rows = table.find_all('tr')
                print(f"  행 개수: {len(rows)}")
                
                # 처음 몇 개 행의 내용 확인
                for j, row in enumerate(rows[:5]):
                    row_text = row.get_text(strip=True)
                    if len(row_text) > 10:  # 의미있는 내용이 있는 행만
                        print(f"    행 {j+1}: {row_text[:100]}...")
        
        # 2. 특정 클래스명으로 베스트셀러 요소 찾기
        print("\n🔍 베스트셀러 관련 클래스명으로 검색:")
        bestseller_classes = ['bestseller', 'rank', 'book_list', 'item_list', 'product']
        
        for class_name in bestseller_classes:
            elements = soup.find_all(class_=lambda x: x and class_name in str(x).lower())
            if elements:
                print(f"\n'{class_name}' 포함 클래스: {len(elements)}개")
                for elem in elements[:2]:
                    elem_text = elem.get_text(strip=True)
                    if len(elem_text) > 20:
                        print(f"  - {elem.name}: {elem.get('class')}")
                        print(f"    텍스트: {elem_text[:100]}...")
        
        # 3. 링크에서 베스트셀러 데이터 찾기
        print("\n🔗 링크에서 베스트셀러 데이터 찾기:")
        links = soup.find_all('a', href=True)
        book_links = [link for link in links if 'wproduct.aspx' in link.get('href', '')]
        
        print(f"책 상품 링크: {len(book_links)}개")
        if book_links:
            for i, link in enumerate(book_links[:5]):
                link_text = link.get_text(strip=True)
                if len(link_text) > 5:
                    print(f"  {i+1}: {link_text[:50]}...")
                    print(f"    href: {link.get('href')}")
        
        # 4. 전체 텍스트에서 순위 패턴 찾기
        print("\n🔍 전체 텍스트에서 순위 패턴 찾기:")
        all_text = soup.get_text()
        
        # 다양한 순위 패턴 시도
        patterns = [
            r'(\d+)위\s*([가-힣\s]+?)(?:\s+지음|\s+저|\s+편집|\s+글|\s+그림|\s+외|\s*$)',
            r'(\d+)\.\s*([가-힣\s]+?)(?:\s+지음|\s+저|\s+편집|\s+글|\s+그림|\s+외|\s*$)',
            r'순위\s*(\d+)[^가-힣]*([가-힣\s]+?)(?:\s+지음|\s+저|\s+편집|\s+글|\s+그림|\s+외|\s*$)',
        ]
        
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, all_text)
            if matches:
                print(f"\n패턴 {i+1} 매치: {len(matches)}개")
                for match in matches[:5]:
                    rank = match[0]
                    title = match[1].strip()
                    if len(title) > 5:
                        print(f"  - {rank}위: {title[:40]}...")
        
        # 5. 특정 ID나 클래스로 베스트셀러 영역 찾기
        print("\n🎯 특정 영역에서 베스트셀러 찾기:")
        specific_selectors = [
            '#bestseller',
            '.bestseller',
            '#book_list',
            '.book_list',
            '#rank_list',
            '.rank_list',
            '#product_list',
            '.product_list'
        ]
        
        for selector in specific_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"\n{selector}: {len(elements)}개")
                for elem in elements[:1]:
                    elem_text = elem.get_text(strip=True)
                    if len(elem_text) > 50:
                        print(f"  텍스트: {elem_text[:100]}...")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    debug_aladin_bestseller() 