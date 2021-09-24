# yt_crawler

유튜브 동영상 id 및 메타 데이터 크롤러

## search.py

  유튜브 동영상 id 크롤링

  - StaticCrawler: 정적 크롤링(검색어당 20개까지만 크롤링 가능)
  - DynamicCrawler: 동적 크롤링(검색어당 max_result 값만큼 크롤링 가능)
 
  cf. chrome version: 89.0.4389.23

## meta.py

  유튜브 메타 데이터 크롤링

  - MetaCrawler: 메타 데이터 크롤링, Youtube API key 요구

## check.py

  동영상 존재 여부 확인

  - Checker: 콘텐츠 존재여부 확인, Youtube API key 요구

## example

      from search import StaticCrawler
      
      id_crawler = StaticCrawler()
      keyword = '파이썬'
      id_result = id_crawler.crawling(keyword)
