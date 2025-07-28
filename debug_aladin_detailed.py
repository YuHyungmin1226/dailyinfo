import requests
from bs4 import BeautifulSoup
import re

def debug_aladin_detailed():
    """알라딘 ss_book_box 상세 구조 분석"""
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
        print("🔍 알라딘 ss_book_box 상세 구조 분석 중...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # ss_book_box 요소들 찾기
        book_boxes = soup.find_all('div', class_='ss_book_box')
        print(f"📚 ss_book_box 요소 개수: {len(book_boxes)}")
        
        if book_boxes:
            print("\n📖 첫 번째 ss_book_box 구조:")
            first_box = book_boxes[0]
            print(f"전체 텍스트: {first_box.get_text(strip=True)[:200]}...")
            
            # 순위 정보 찾기
            rank_elements = first_box.find_all(text=re.compile(r'^\d+$'))
            print(f"\n순위 요소들: {rank_elements}")
            
            # 제목 정보 찾기
            title_elements = first_box.find_all(['a', 'span', 'div'], class_=lambda x: x and 'title' in str(x).lower())
            print(f"\n제목 관련 요소들: {len(title_elements)}개")
            for elem in title_elements[:3]:
                print(f"  - {elem.name}: {elem.get('class')} - '{elem.get_text(strip=True)[:50]}...'")
            
            # 링크 요소들 찾기
            links = first_box.find_all('a')
            print(f"\n링크 요소들: {len(links)}개")
            for link in links[:3]:
                print(f"  - href: {link.get('href', 'href 없음')}")
                print(f"    텍스트: '{link.get_text(strip=True)[:50]}...'")
                print(f"    클래스: {link.get('class', '클래스 없음')}")
            
            # 모든 텍스트 노드 확인
            print(f"\n📝 모든 텍스트 노드:")
            text_nodes = first_box.find_all(text=True)
            for i, text in enumerate(text_nodes[:10]):
                text_clean = text.strip()
                if text_clean:
                    print(f"  {i+1}: '{text_clean[:50]}...'")
        
        # 실제 베스트셀러 데이터 추출 시도
        print("\n🎯 실제 베스트셀러 데이터 추출 시도:")
        extracted_books = []
        
        for i, box in enumerate(book_boxes[:10]):  # 처음 10개만 시도
            box_text = box.get_text(strip=True)
            
            # 순위와 제목 패턴 찾기
            # 패턴 1: 숫자 + 제목
            pattern1 = r'(\d+)\s*([가-힣\s]+?)(?:\s+지음|\s+저|\s+편집|\s+글|\s+그림|\s+외|\s*$)'
            matches1 = re.findall(pattern1, box_text)
            
            # 패턴 2: 제목만 찾기 (순위는 인덱스로)
            pattern2 = r'([가-힣\s]{5,}?)(?:\s+지음|\s+저|\s+편집|\s+글|\s+그림|\s+외|\s*$)'
            matches2 = re.findall(pattern2, box_text)
            
            print(f"\n박스 {i+1}:")
            print(f"  전체 텍스트: {box_text[:100]}...")
            print(f"  패턴1 매치: {len(matches1)}개")
            if matches1:
                for match in matches1[:2]:
                    print(f"    - 순위: {match[0]}, 제목: {match[1][:30]}...")
            
            print(f"  패턴2 매치: {len(matches2)}개")
            if matches2:
                for match in matches2[:2]:
                    print(f"    - 제목: {match[:30]}...")
            
            # 실제 데이터 추출
            if matches1:
                for match in matches1:
                    rank = int(match[0])
                    title = match[1].strip()
                    if len(title) > 3:
                        extracted_books.append({
                            'rank': rank,
                            'title': title,
                            'author': '저자 정보 없음',
                            'publisher': '출판사 정보 없음'
                        })
                        break  # 첫 번째 매치만 사용
        
        print(f"\n📊 추출된 책 데이터: {len(extracted_books)}개")
        for book in extracted_books[:5]:
            print(f"  - {book['rank']}위: {book['title'][:30]}...")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    debug_aladin_detailed() 