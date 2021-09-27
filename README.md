# YouTube Crawler

유튜브 동영상 id 및 메타 데이터 크롤러


## 요구사항
1.     pip install -r requirements.txt
2. 구글 API key => ./config/api_key.json 에 추가 (key 하나 당 동영상 10000개)

## Example (in root directory)
python ./src/crawling.py -k example_keyword.csv

## id 검색
유튜브 동영상 id 크롤링

- Static Mode: 정적 크롤링(검색어당 20만 크롤링)
- Dynamic Mode: 동적 크롤링(검색어당 num 값만큼 크롤링)
    - chromedriver version: 93
    -     python ./src/crawling.py -k example_keyword.csv -d True

검색 옵션 
- 0: 동영상+모두+관련성
- 1: 동영상+모두+업로드날짜
- 2: 동영상+모두+조회수
- 3: 동영상+모두+평점
- 4: 동영상+이번달+관련성
- 5: 동영상+이번달+업로드날짜
- 6: 동영상+이번달+조회수 
- 7: 동영상+이번달+평점
- 8: 동영상+올해+관련성
- 9: 동영상+올해+업로드날짜
- 10: 동영상+올해+조회수
- 11: 동영상+올해+평점


## 메타데이터
- Youtube API key 요구

## 검색어
- csv (line)
- txt (line)
