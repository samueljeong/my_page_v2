"""
Google Docs 연동 모듈 - 대본 관리

- 에피소드별 Google Docs 생성/조회
- Docs에서 대본 가져오기
- 시트에 Docs URL 저장
"""

import os
import re
from typing import Dict, Any, Optional

from .config import SERIES_INFO, SHEET_NAME


def col_index_to_letter(col_idx: int) -> str:
    """컬럼 인덱스를 Excel 컬럼 레터로 변환 (A=0, Z=25, AA=26)"""
    result = ""
    while col_idx >= 0:
        result = chr(ord('A') + col_idx % 26) + result
        col_idx = col_idx // 26 - 1
    return result


def get_docs_service():
    """Google Docs 서비스 객체 가져오기"""
    try:
        from drama_server import get_docs_service_account
        return get_docs_service_account()
    except ImportError:
        # drama_server에 함수가 없으면 직접 생성
        try:
            from drama_server import get_credentials
            from googleapiclient.discovery import build
            creds = get_credentials()
            return build('docs', 'v1', credentials=creds)
        except Exception as e:
            print(f"[DOCS] 서비스 연결 실패: {e}")
            return None


def get_drive_service():
    """Google Drive 서비스 객체 가져오기 (폴더 관리용)"""
    try:
        from drama_server import get_drive_service_account
        return get_drive_service_account()
    except ImportError:
        try:
            from drama_server import get_credentials
            from googleapiclient.discovery import build
            creds = get_credentials()
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            print(f"[DRIVE] 서비스 연결 실패: {e}")
            return None


def get_or_create_folder(folder_name: str = "혈영이세계_대본") -> Optional[str]:
    """
    대본 저장용 폴더 가져오기 또는 생성

    Returns:
        folder_id: Google Drive 폴더 ID
    """
    drive = get_drive_service()
    if not drive:
        return None

    try:
        # 기존 폴더 검색
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = drive.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])

        if files:
            print(f"[DRIVE] 기존 폴더 사용: {folder_name}")
            return files[0]['id']

        # 폴더 생성
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = drive.files().create(body=file_metadata, fields='id').execute()
        print(f"[DRIVE] 폴더 생성: {folder_name}")
        return folder.get('id')

    except Exception as e:
        print(f"[DRIVE] 폴더 생성 실패: {e}")
        return None


def create_episode_doc(
    episode: int,
    initial_content: str = "",
    title: str = "",
) -> Dict[str, Any]:
    """
    에피소드용 Google Docs 생성

    Args:
        episode: 에피소드 번호 (1~60)
        initial_content: 초기 대본 내용
        title: 에피소드 제목

    Returns:
        {"ok": True, "doc_id": "...", "doc_url": "..."}
    """
    docs = get_docs_service()
    drive = get_drive_service()

    if not docs or not drive:
        return {"ok": False, "error": "Google API 서비스 연결 실패"}

    episode_id = f"EP{episode:03d}"
    doc_title = f"[{SERIES_INFO['title']}] {episode_id}"
    if title:
        doc_title += f" - {title}"

    try:
        # 기존 문서 확인
        existing = get_episode_doc_by_number(episode)
        if existing and existing.get("ok"):
            print(f"[DOCS] 기존 문서 사용: {episode_id}")
            return existing

        # 폴더 가져오기
        folder_id = get_or_create_folder()

        # 문서 생성
        doc = docs.documents().create(body={'title': doc_title}).execute()
        doc_id = doc.get('documentId')

        # 폴더로 이동
        if folder_id:
            drive.files().update(
                fileId=doc_id,
                addParents=folder_id,
                fields='id, parents'
            ).execute()

        # 초기 내용 삽입
        if initial_content:
            requests = [{
                'insertText': {
                    'location': {'index': 1},
                    'text': initial_content
                }
            }]
            docs.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()

        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

        print(f"[DOCS] ✓ 문서 생성: {doc_title}")

        # 시트에 URL 저장
        _save_doc_url_to_sheet(episode, doc_url)

        return {
            "ok": True,
            "episode": episode,
            "episode_id": episode_id,
            "doc_id": doc_id,
            "doc_url": doc_url,
            "title": doc_title,
        }

    except Exception as e:
        print(f"[DOCS] 문서 생성 실패: {e}")
        return {"ok": False, "error": str(e)}


def get_episode_doc_by_number(episode: int) -> Dict[str, Any]:
    """
    에피소드 번호로 기존 Docs 검색

    시트의 대본URL 컬럼에서 찾거나, Drive에서 제목으로 검색
    """
    # 1) 시트에서 URL 조회
    from .sheets import get_episode_by_number
    ep_data = get_episode_by_number(episode)

    if ep_data and ep_data.get("대본URL"):
        doc_url = ep_data["대본URL"]
        # URL에서 doc_id 추출
        match = re.search(r'/document/d/([a-zA-Z0-9_-]+)', doc_url)
        if match:
            doc_id = match.group(1)
            return {
                "ok": True,
                "episode": episode,
                "doc_id": doc_id,
                "doc_url": doc_url,
                "source": "sheet",
            }

    # 2) Drive에서 검색
    drive = get_drive_service()
    if not drive:
        return {"ok": False, "error": "Drive 서비스 연결 실패"}

    episode_id = f"EP{episode:03d}"
    query = f"name contains '{episode_id}' and mimeType='application/vnd.google-apps.document' and trashed=false"

    try:
        results = drive.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])

        if files:
            doc_id = files[0]['id']
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
            return {
                "ok": True,
                "episode": episode,
                "doc_id": doc_id,
                "doc_url": doc_url,
                "source": "drive_search",
            }

        return {"ok": False, "error": f"{episode_id} 문서를 찾을 수 없습니다"}

    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_script_from_doc(episode: int) -> Dict[str, Any]:
    """
    Google Docs에서 대본 가져오기

    Args:
        episode: 에피소드 번호

    Returns:
        {"ok": True, "script": "...", "char_count": 25000}
    """
    # 문서 찾기
    doc_info = get_episode_doc_by_number(episode)
    if not doc_info.get("ok"):
        return doc_info

    doc_id = doc_info["doc_id"]
    docs = get_docs_service()

    if not docs:
        return {"ok": False, "error": "Docs 서비스 연결 실패"}

    try:
        doc = docs.documents().get(documentId=doc_id).execute()
        content = doc.get('body', {}).get('content', [])

        # 텍스트 추출
        script_parts = []
        for element in content:
            if 'paragraph' in element:
                for text_run in element['paragraph'].get('elements', []):
                    if 'textRun' in text_run:
                        script_parts.append(text_run['textRun'].get('content', ''))

        script = ''.join(script_parts).strip()

        print(f"[DOCS] ✓ EP{episode:03d} 대본 로드: {len(script):,}자")

        return {
            "ok": True,
            "episode": episode,
            "doc_id": doc_id,
            "doc_url": doc_info["doc_url"],
            "script": script,
            "char_count": len(script),
        }

    except Exception as e:
        print(f"[DOCS] 대본 가져오기 실패: {e}")
        return {"ok": False, "error": str(e)}


def update_doc_content(episode: int, content: str) -> Dict[str, Any]:
    """
    Google Docs 내용 업데이트 (전체 교체)

    Args:
        episode: 에피소드 번호
        content: 새 대본 내용

    Returns:
        {"ok": True, "char_count": 25000}
    """
    doc_info = get_episode_doc_by_number(episode)

    # 문서가 없으면 생성
    if not doc_info.get("ok"):
        return create_episode_doc(episode, initial_content=content)

    doc_id = doc_info["doc_id"]
    docs = get_docs_service()

    if not docs:
        return {"ok": False, "error": "Docs 서비스 연결 실패"}

    try:
        # 기존 내용 길이 확인
        doc = docs.documents().get(documentId=doc_id).execute()
        doc_content = doc.get('body', {}).get('content', [])

        # 마지막 인덱스 찾기
        end_index = 1
        for element in doc_content:
            if 'endIndex' in element:
                end_index = max(end_index, element['endIndex'])

        requests = []

        # 기존 내용 삭제 (1 이후부터)
        if end_index > 2:
            requests.append({
                'deleteContentRange': {
                    'range': {
                        'startIndex': 1,
                        'endIndex': end_index - 1
                    }
                }
            })

        # 새 내용 삽입
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': content
            }
        })

        docs.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()

        print(f"[DOCS] ✓ EP{episode:03d} 업데이트: {len(content):,}자")

        return {
            "ok": True,
            "episode": episode,
            "doc_id": doc_id,
            "doc_url": doc_info["doc_url"],
            "char_count": len(content),
        }

    except Exception as e:
        print(f"[DOCS] 업데이트 실패: {e}")
        return {"ok": False, "error": str(e)}


def _save_doc_url_to_sheet(episode: int, doc_url: str) -> bool:
    """시트에 대본URL 저장"""
    from .sheets import get_sheets_service, get_sheet_id, get_episode_by_number

    service = get_sheets_service()
    if not service:
        return False

    sheet_id = get_sheet_id()
    if not sheet_id:
        return False

    try:
        # 에피소드 행 찾기
        ep_data = get_episode_by_number(episode)
        if not ep_data:
            print(f"[DOCS] 에피소드 {episode} 없음, URL 저장 스킵")
            return False

        row_index = ep_data["_row_index"]

        # 헤더에서 대본URL 컬럼 찾기
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"{SHEET_NAME}!A2:AZ2"
        ).execute()
        headers = result.get('values', [[]])[0]

        if "대본URL" not in headers:
            print("[DOCS] '대본URL' 컬럼이 없습니다. 컬럼을 추가해주세요.")
            return False

        col_idx = headers.index("대본URL")
        col_letter = col_index_to_letter(col_idx)

        # URL 저장
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"{SHEET_NAME}!{col_letter}{row_index}",
            valueInputOption="RAW",
            body={"values": [[doc_url]]}
        ).execute()

        print(f"[DOCS] ✓ EP{episode:03d} URL 저장 완료")
        return True

    except Exception as e:
        print(f"[DOCS] URL 저장 실패: {e}")
        return False


def get_script_for_pipeline(episode: int) -> Dict[str, Any]:
    """
    영상 파이프라인용 대본 가져오기

    우선순위:
    1. Google Docs (대본URL이 있으면)
    2. 시트의 대본 컬럼

    Returns:
        {"ok": True, "script": "...", "source": "docs|sheet"}
    """
    from .sheets import get_episode_by_number

    ep_data = get_episode_by_number(episode)
    if not ep_data:
        return {"ok": False, "error": f"에피소드 {episode} 없음"}

    # 1) Docs에서 가져오기 시도
    if ep_data.get("대본URL"):
        doc_result = get_script_from_doc(episode)
        if doc_result.get("ok") and doc_result.get("script"):
            return {
                "ok": True,
                "script": doc_result["script"],
                "char_count": doc_result["char_count"],
                "source": "docs",
                "doc_url": doc_result["doc_url"],
            }

    # 2) 시트의 대본 컬럼
    script = ep_data.get("대본", "")
    if script:
        return {
            "ok": True,
            "script": script,
            "char_count": len(script),
            "source": "sheet",
        }

    return {"ok": False, "error": "대본이 없습니다 (Docs/시트 모두 비어있음)"}


# =====================================================
# CLI
# =====================================================

def main():
    """CLI 명령어"""
    import argparse

    parser = argparse.ArgumentParser(description="Google Docs 대본 관리")
    subparsers = parser.add_subparsers(dest="command")

    # create: 문서 생성
    create_parser = subparsers.add_parser("create", help="에피소드 Docs 생성")
    create_parser.add_argument("episode", type=int, help="에피소드 번호")
    create_parser.add_argument("--title", type=str, default="", help="에피소드 제목")

    # get: 대본 가져오기
    get_parser = subparsers.add_parser("get", help="Docs에서 대본 가져오기")
    get_parser.add_argument("episode", type=int, help="에피소드 번호")

    # update: 대본 업데이트
    update_parser = subparsers.add_parser("update", help="Docs 내용 업데이트")
    update_parser.add_argument("episode", type=int, help="에피소드 번호")
    update_parser.add_argument("--file", type=str, help="대본 파일 경로")

    args = parser.parse_args()

    if args.command == "create":
        result = create_episode_doc(args.episode, title=args.title)
        if result.get("ok"):
            print(f"✓ 문서 생성: {result['doc_url']}")
        else:
            print(f"✗ 실패: {result.get('error')}")

    elif args.command == "get":
        result = get_script_from_doc(args.episode)
        if result.get("ok"):
            print(f"✓ 대본 로드 ({result['char_count']:,}자)")
            print("-" * 50)
            print(result['script'][:1000])
            if result['char_count'] > 1000:
                print(f"\n... ({result['char_count']:,}자 중 1,000자만 표시)")
        else:
            print(f"✗ 실패: {result.get('error')}")

    elif args.command == "update":
        if args.file:
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
            result = update_doc_content(args.episode, content)
            if result.get("ok"):
                print(f"✓ 업데이트 완료 ({result['char_count']:,}자)")
            else:
                print(f"✗ 실패: {result.get('error')}")
        else:
            print("--file 옵션 필요")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
