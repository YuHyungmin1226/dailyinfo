import requests
from bs4 import BeautifulSoup
import re
from dataclasses import dataclass

@dataclass
class BookData:
    """도서 데이터 클래스"""
    rank: int
    title: str
    author: str
    publisher: str

def test_aladin_parsing():
    """개선된 알라딘 파싱 로직 테스트"""
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
        print("🧪 개선된 알라딘 파싱 로직 테스트 중...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        book_data = []
        
        # 1. ss_book_list 클래스를 가진 요소들에서 책 정보 추출
        print("\n📚 ss_book_list에서 데이터 추출:")
        book_lists = soup.find_all('div', class_='ss_book_list')
        print(f"ss_book_list 요소 개수: {len(book_lists)}")
        
        if book_lists:
            for i, book_list in enumerate(book_lists[:10]):  # 처음 10개만 테스트
                book_list_text = book_list.get_text(strip=True)
                print(f"\n박스 {i+1}: {book_list_text[:100]}...")
                
                # 순위와 제목 패턴 찾기
                pattern1 = r'(\d+)\.\s*([가-힣\s]+?)(?:\s+지음|\s+저|\s+편집|\s+글|\s+그림|\s+외|\s*$)'
                matches1 = re.findall(pattern1, book_list_text)
                
                if matches1:
                    for match in matches1:
                        rank = int(match[0])
                        title = match[1].strip()
                        
                        if len(title) > 3:
                            # 저자와 출판사 정보 추출 시도
                            author = "저자 정보 없음"
                            publisher = "출판사 정보 없음"
                            
                            # 저자 패턴 찾기
                            author_pattern = r'([가-힣\s]+?)\s*지음|([가-힣\s]+?)\s*저|([가-힣\s]+?)\s*편집'
                            author_matches = re.findall(author_pattern, book_list_text)
                            if author_matches:
                                for author_match in author_matches:
                                    if any(author_match):
                                        author = next(a for a in author_match if a).strip()
                                        break
                            
                            # 출판사 패턴 찾기
                            publisher_pattern = r'([가-힣\s]+?)\s*\|\s*([가-힣\s]+?)\s*\|'
                            publisher_matches = re.findall(publisher_pattern, book_list_text)
                            if publisher_matches:
                                publisher = publisher_matches[0][1].strip()
                            
                            print(f"  ✅ 추출: {rank}위 - {title[:30]}... (저자: {author}, 출판사: {publisher})")
                            
                            # 중복 제거
                            existing_titles = [book.title for book in book_data]
                            if title not in existing_titles:
                                book_data.append(BookData(rank, title, author, publisher))
                            break
        
        # 2. 책 상품 링크에서 제목 추출
        if not book_data:
            print("\n🔗 책 상품 링크에서 데이터 추출:")
            book_links = soup.find_all('a', href=lambda x: x and 'wproduct.aspx' in x)
            print(f"책 상품 링크 개수: {len(book_links)}")
            
            for i, link in enumerate(book_links[:10]):
                link_text = link.get_text(strip=True)
                if len(link_text) > 5 and not link_text.startswith('http'):
                    rank = i + 1
                    title = link_text
                    author = "저자 정보 없음"
                    publisher = "출판사 정보 없음"
                    
                    print(f"  ✅ 추출: {rank}위 - {title[:30]}...")
                    
                    # 중복 제거
                    existing_titles = [book.title for book in book_data]
                    if title not in existing_titles:
                        book_data.append(BookData(rank, title, author, publisher))
        
        # 3. 전체 텍스트에서 패턴 매칭
        if not book_data:
            print("\n📝 전체 텍스트에서 패턴 매칭:")
            all_text = soup.get_text()
            
            patterns = [
                r'(\d+)\.\s*([가-힣\s]+?)(?:\s+지음|\s+저|\s+편집|\s+글|\s+그림|\s+외)',
                r'(\d+)\s*([가-힣\s]+?)(?:\s+지음|\s+저|\s+편집|\s+글|\s+그림|\s+외)',
                r'순위\s*(\d+)[^가-힣]*([가-힣\s]+?)(?:\s+지음|\s+저|\s+편집|\s+글|\s+그림|\s+외)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, all_text)
                if matches:
                    print(f"패턴 매치: {len(matches)}개")
                    for match in matches[:5]:
                        rank = int(match[0])
                        title = match[1].strip()
                        
                        if len(title) > 3:
                            print(f"  ✅ 추출: {rank}위 - {title[:30]}...")
                            
                            # 중복 제거
                            existing_titles = [book.title for book in book_data]
                            if title not in existing_titles:
                                book_data.append(BookData(rank, title, "저자 정보 없음", "출판사 정보 없음"))
                    break
        
        # 결과 출력
        print(f"\n📊 최종 추출 결과: {len(book_data)}개")
        for book in book_data[:10]:
            print(f"  {book.rank}위: {book.title[:40]}... (저자: {book.author}, 출판사: {book.publisher})")
        
        return book_data
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return []

if __name__ == "__main__":
    test_aladin_parsing() 