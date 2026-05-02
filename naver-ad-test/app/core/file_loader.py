"""
CSV / XLSX / XLS 파일 로더
PROJECT_RULES.txt 섹션 9 기준
"""
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
CSV_ENCODINGS = ["utf-8-sig", "cp949", "euc-kr", "utf-8"]


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """공통 정제: 컬럼명 공백 제거 / 빈 행 제거 / 빈 컬럼 제거"""
    df = df.copy()

    # 컬럼명 앞뒤 공백 제거
    df.columns = [str(c).strip() for c in df.columns]

    # 완전히 비어 있는 컬럼 제거
    df = df.dropna(axis=1, how="all")

    # 완전히 비어 있는 행 제거
    df = df.dropna(axis=0, how="all")

    # 인덱스 초기화
    df = df.reset_index(drop=True)

    return df


def _load_csv(path: Path) -> pd.DataFrame:
    """CSV 파일 읽기. 인코딩을 순서대로 시도."""
    last_error = None
    for encoding in CSV_ENCODINGS:
        try:
            df = pd.read_csv(str(path), encoding=encoding, dtype=str)
            logger.info(f"CSV 인코딩 성공: {encoding} ({path.name})")
            return df
        except (UnicodeDecodeError, LookupError) as e:
            last_error = e
            logger.debug(f"인코딩 실패 ({encoding}): {e}")
            continue
        except Exception as e:
            raise RuntimeError(f"CSV 읽기 실패: {e}") from e
    raise RuntimeError(
        f"CSV 인코딩 자동 감지 실패 ({path.name}). "
        f"시도한 인코딩: {CSV_ENCODINGS}. 마지막 오류: {last_error}"
    )


def _load_excel(path: Path) -> pd.DataFrame:
    """XLSX / XLS 파일 읽기."""
    try:
        df = pd.read_excel(str(path), dtype=str)
        logger.info(f"Excel 읽기 성공: {path.name}")
        return df
    except Exception as e:
        raise RuntimeError(f"Excel 읽기 실패 ({path.name}): {e}") from e


def load_file(path: Path) -> dict:
    """
    파일을 읽고 정제된 DataFrame을 반환.

    반환:
        {
            "success": bool,
            "df": pd.DataFrame or None,
            "error": str or None,
        }
    """
    if not isinstance(path, Path):
        path = Path(path)

    if not path.exists():
        return {"success": False, "df": None, "error": f"파일을 찾을 수 없습니다: {path}"}

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return {
            "success": False,
            "df": None,
            "error": f"지원하지 않는 파일 형식입니다: {ext} (지원: {', '.join(SUPPORTED_EXTENSIONS)})",
        }

    try:
        if ext == ".csv":
            df = _load_csv(path)
        else:
            df = _load_excel(path)

        df = _clean_dataframe(df)
        logger.info(f"파일 로드 완료: {path.name} ({len(df)}행, {len(df.columns)}컬럼)")
        return {"success": True, "df": df, "error": None}

    except RuntimeError as e:
        return {"success": False, "df": None, "error": str(e)}
    except Exception as e:
        return {"success": False, "df": None, "error": f"예상치 못한 오류: {e}"}
