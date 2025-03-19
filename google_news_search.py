import argparse
import json
import sys
import os
import re
import logging
import traceback
from datetime import datetime
from typing import Optional, List, Dict
from gnews import GNews


# Logger 설정
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 파일 핸들러 추가 (로그 파일명 "google_news.log")
log_file = "google_news.log"
fh = logging.FileHandler(log_file)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)


def clean_filename(filename: str) -> str:
    """
    파일명에서 사용할 수 없는 문자 제거

    Parameters:
        filename (str): 원본 파일명

    Returns:
        str: 안전한 파일명
    """
    return re.sub(r'[\/:*?"<>|]', '_', filename)


def load_existing_data(file_path: str) -> List:
    """
    기존 JSON 파일을 불러와 리스트로 반환

    Parameters:
        file_path (str): 불러올 JSON 파일 경로

    Returns:
        list: JSON 데이터 리스트 (없으면 빈 리스트 반환)
    """
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                logger.error("JSON 파일 오류: %s", file_path)
                return []
    return []


def load_profiles(file_path: str = "search_profiles.json") -> Dict[str, Dict]:
    """저장된 SearchProfile 목록을 불러옴"""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logger.error("JSON 파일을 불러올 수 없습니다.")
    return {}


def save_profiles(profiles: Dict[str, Dict],
                  file_path: str = "./search_profiles.json") -> None:
    """SearchProfile 목록 dict를 JSON 파일로 저장"""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=4)


def edit_profile(args):
    """
    SearchProfile을 수정하는 함수
    """
    profiles = load_profiles()

    if args.name not in profiles:
        logger.error(f"{args.name} 프로필을 찾을 수 없습니다.")
        return

    profile_data = profiles[args.name]

    # 수정할 요소들을 key-value 딕셔너리로 변환
    if args.att is not None:
        updates = {key: value for key, value in args.att}
        logger.info(f"수정할 속성: {updates}")

        # 기존 프로필 업데이트
        for key, value in updates.items():
            if key in profile_data:
                old = profile_data[key]
                profile_data[key] = value
                logger.info(f"{key} : {old} -> {value} 변경되었습니다.")
            else:
                logger.warning(f"{key}는 존재하지 않는 속성입니다.")

        # 업데이트된 프로필 저장
        profiles[args.name] = profile_data
        save_profiles(profiles)
        logger.info(f"{args.name} 프로필이 수정되었습니다.")


class SearchProfile:
    """
    GNews 검색 설정 파라미터를 관리하는 클래스

    Parameters:
        language: 뉴스 검색 언어 (예: 'en', 'ko')
        country: 뉴스 소스 국가 (예: 'US', 'KR')
        period: 검색 기간 (예: '7d', '1h', '30m', '1y')
        query: 검색어
        start_date: 검색 시작 날짜 (YYYY-MM-DD 형식)
        end_date: 검색 종료 날짜 (YYYY-MM-DD 형식)
        max_results: 가져올 최대 뉴스 개수 (기본값: 100)
        exclude_websites: 제외할 웹사이트 목록 (기본값 None → 빈 리스트)
        proxy: 프록시 설정 (기본값 None → 빈 딕셔너리)
    """

    def __init__(self,
                 language: str,
                 country: str,
                 period: str,
                 query: str,
                 start_date: Optional[str] = None,
                 end_date: Optional[str] = None,
                 max_results: int = 100,
                 exclude_websites: Optional[List[str]] = None,
                 proxy: Optional[Dict[str, str]] = None) -> None:
        self.language = language
        self.country = country
        self.period = period
        if start_date:
            self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            self.start_date = None
        if end_date:
            self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            self.end_date = None
        self.max_results = max_results
        self.exclude_websites = (exclude_websites
                                 if exclude_websites else [])
        self.proxy = proxy if proxy else {}
        self.query = query
        self.results = []

    def save_as_json(
            self,
            folder_path: str = './google_news_search_result'
    ) -> None:
        """
        기존 데이터 리스트에 새로운 검색 결과(self.results)를 추가하여
        JSON 파일({language}_{country}_{query}.json)로 저장

        Parameters:
            folder_path (str): 저장할 폴더 경로 (기본값 './google_news_search_result')
        """
        os.makedirs(folder_path, exist_ok=True)
        file_name = clean_filename(
            f"{self.language}_{self.country}_{self.query}.json"
        )
        file_path = os.path.join(folder_path, file_name)
        existing_results = load_existing_data(file_path)
        # 중복 제거 (링크를 기준으로 중복 방지)
        existing_links = {item["url"] for item in existing_results}
        combined_results = existing_results + [
            item for item in self.results
            if item["url"] not in existing_links
        ]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(combined_results, f, ensure_ascii=False, indent=4)
        logger.info(f"검색 결과가 {file_path}에 저장되었습니다.")

    def to_dict(self) -> dict:
        """프로필 저장을 위해 SearchProfile 객체를 딕셔너리로 변환"""
        return {
            "language": self.language,
            "country": self.country,
            "period": self.period,
            "start_date": (self.start_date.strftime("%Y-%m-%d")
                           if self.start_date else None),
            "end_date": (self.end_date.strftime("%Y-%m-%d")
                         if self.end_date else None),
            "max_results": self.max_results,
            "exclude_websites": self.exclude_websites,
            "query": self.query
        }

    @staticmethod
    def from_dict(data: dict) -> "SearchProfile":
        """프로필을 불러오기 위해 딕셔너리를 SearchProfile 객체로 변환"""
        return SearchProfile(**data)


def google_news_search(profile: SearchProfile) -> None:
    """
    GNews 패키지를 사용하여 구글 뉴스 검색 결과를 가져오고 저장.
    https://github.com/ranahaani/GNews

    Parameters:
        profile (SearchProfile): 검색 설정을 포함한 객체

    Returns:
        JSON 파일
    """
    google_news = GNews(
        language=profile.language,
        country=profile.country,
        period=profile.period,
        start_date=profile.start_date,
        end_date=profile.end_date,
        max_results=profile.max_results,
        exclude_websites=profile.exclude_websites,
        proxy=profile.proxy
    )
    profile.results = google_news.get_news(profile.query)
    logger.info(f"{len(profile.results)}개의 검색 결과를 찾았습니다.")
    profile.save_as_json()


def main() -> None:
    try:
        parser = argparse.ArgumentParser(description="Google Search")
        subparsers = parser.add_subparsers(dest="mode")

        # 'use'
        use_parser = subparsers.add_parser('use', help='기존 프로필 사용')
        use_parser.add_argument(
            "name", type=str,
            help="사용할 SearchProfile의 이름"
        )

        # 'edit'
        edit_parser = subparsers.add_parser('edit', help='기존 프로필 수정')
        edit_parser.add_argument(
            "name", type=str,
            help="수정할 SearchProfile의 이름"
        )
        edit_parser.add_argument(
            "--att", type=str, nargs="+", action='append',
            help="수정할 요소 (예: --att key1 value1 --att key2 value2 ...)"
        )

        # 'add'
        add_parser = subparsers.add_parser('add', help='새로운 프로필 추가')
        add_parser.add_argument(
            "name", type=str,
            help="새롭게 생성할 SearchProfile의 이름"
        )
        group_period = add_parser.add_argument_group("Period Parameters")
        group_period.add_argument(
            "--period", type=str, default=None,
            help="검색 기간 (예: '7d', '1m', '1y')"
        )
        group_period.add_argument(
            "--start_date", type=str, default=None,
            help="검색 시작 날짜 (YYYY-MM-DD)"
        )
        group_period.add_argument(
            "--end_date", type=str, default=None,
            help="검색 종료 날짜 (YYYY-MM-DD)"
        )

        add_parser.add_argument(
            "--language", type=str, required=True,
            help="Language (예: en, ko)"
        )
        add_parser.add_argument(
            "--country", type=str, required=True,
            help="Country (예: US, KR)"
        )
        add_parser.add_argument(
            "--max_results", type=int, default=100,
            help="최대 검색 결과 개수"
        )
        add_parser.add_argument(
            "--exclude", nargs="*",
            help="제외할 웹사이트 리스트 (예: cnn.com bbc.com)"
        )
        add_parser.add_argument(
            "--query", type=str, required=True,
            help="검색어"
        )

        # 'del'
        del_parser = subparsers.add_parser('del', help='기존 프로필 삭제')
        del_parser.add_argument(
            "name", type=str,
            help="삭제할 SearchProfile의 이름"
        )

        try:
            args = parser.parse_args()
        except SystemExit as e:
            logger.error("잘못된 입력으로 프로그램이 종료됨 (입력: %s) | 종료 코드: %s", " ".join(sys.argv), e)
            return

        profiles = load_profiles()

        if args.mode == 'use':
            if args.name in profiles:
                profile = SearchProfile.from_dict(profiles[args.name])
                logger.info(f"'{args.name}' 프로필이 선택되었습니다.")

                google_news_search(profile)
            else:
                logger.error(f"'{args.name}' 프로필을 찾을 수 없습니다.")
                return

        elif args.mode == 'add':
            if not (args.period or (args.start_date and args.end_date)):
                logger.error(
                    "검색 기간을 지정하려면 --period 또는"
                    " --start_date와 --end_date를 함께 제공해야 합니다."
                )

            profile = SearchProfile(
                language=args.language,
                country=args.country,
                period=args.period,
                start_date=args.start_date,
                end_date=args.end_date,
                max_results=args.max_results,
                exclude_websites=args.exclude,
                query=args.query
            )
            profiles[args.name] = profile.to_dict()
            save_profiles(profiles)
            logger.info(f"'{args.name}' 프로필이 저장되었습니다.")

        elif args.mode == 'edit':
            edit_profile(args)

        elif args.mode == 'del':
            del profiles[args.name]
            save_profiles(profiles)
            logger.info(f"'{args.name}' 프로필이 삭제되었습니다.")

        else:
            logger.error(
                "--profile 옵션으로 사용할 프로필을 선택하거나, --new-profile 옵션을 "
                "사용해 새 프로필을 생성하세요."
            )
            return
    except Exception as e:
        logger.exception("실행 중 예외 발생: %s", e)
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
