# HOW TO RUN
4가지 명령어 존재 **add,use,edit,del**
### 새로운 검색 프로필 추가 : ```add```
  기간 길이를 지정하는 경우 : **period**
  ```bash
  python google_news_search.py add temp --language en --country US --query AI --period 7d --max_results 50
  ```
  날짜 범위를 지정하는 경우 : **start_date, end_date**
  ```bash
  python google_news_search.py add temp --language en --country US --query AI --start_date 2024-01-01 --end_date 2024-01-07 --max_results 50
  ```
### 기존 검색 프로필로 검색 : ```use```
  ```bash
  python google_news_search.py use temp
  ```
  결과는 ```./google_news_search_result/{language}\_{country}\_{query}.json``` 파일로 저장됨
### 기존 검색 프로필 수정 : ```edit```   
  '-att {key} {value}'로 바꿀 요소와 값 입력
  ```bash
  python google_news_search.py edit temp --att query US --att max_results 100
  ```
### 기존 검색 프로필 삭제 : ```del```
  ```bash
  python google_news_search.py del temp
  ```
---
* exclude_websites, proxy 인자를 통해 추가적인 설정 가능
* 검색 프로필은 ```./search_profiles.json```에 기록
* 실행 로그는 ```./google_news.log```에 기록
* Gnews 관련 : https://github.com/ranahaani/GNews