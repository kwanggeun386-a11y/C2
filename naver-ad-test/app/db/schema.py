"""
SQLite 테이블 스키마 정의
PROJECT_RULES.txt 섹션 7 기준
"""

CREATE_ADVERTISERS = """
CREATE TABLE IF NOT EXISTS advertisers (
    advertiser_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    advertiser_name TEXT    NOT NULL UNIQUE,
    industry        TEXT,
    memo            TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""

CREATE_UPLOAD_FILES = """
CREATE TABLE IF NOT EXISTS upload_files (
    upload_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    advertiser_id     INTEGER NOT NULL,
    original_file_name TEXT,
    stored_file_path  TEXT,
    uploaded_at       TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    report_start_date TEXT,
    report_end_date   TEXT,
    upload_type       TEXT,
    file_hash         TEXT,
    row_count         INTEGER,
    status            TEXT    NOT NULL DEFAULT 'pending',
    FOREIGN KEY (advertiser_id) REFERENCES advertisers (advertiser_id)
);
"""

CREATE_DAILY_PERFORMANCE = """
CREATE TABLE IF NOT EXISTS daily_performance (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    advertiser_id        INTEGER NOT NULL,
    upload_id            INTEGER,
    date                 TEXT    NOT NULL,
    campaign_type        TEXT,
    campaign             TEXT,
    ad_group             TEXT,
    media                TEXT,
    search_term          TEXT,
    keyword              TEXT,
    impressions          REAL    NOT NULL DEFAULT 0,
    clicks               REAL    NOT NULL DEFAULT 0,
    cost                 REAL    NOT NULL DEFAULT 0,
    total_conversions    REAL    NOT NULL DEFAULT 0,
    total_revenue        REAL    NOT NULL DEFAULT 0,
    purchase_conversions REAL    NOT NULL DEFAULT 0,
    purchase_revenue     REAL    NOT NULL DEFAULT 0,
    created_at           TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (advertiser_id) REFERENCES advertisers (advertiser_id),
    FOREIGN KEY (upload_id)     REFERENCES upload_files (upload_id)
);
"""

CREATE_DAILY_SUMMARY = """
CREATE TABLE IF NOT EXISTS daily_summary (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    advertiser_id        INTEGER NOT NULL,
    date                 TEXT    NOT NULL,
    impressions          REAL    NOT NULL DEFAULT 0,
    clicks               REAL    NOT NULL DEFAULT 0,
    cost                 REAL    NOT NULL DEFAULT 0,
    ctr                  REAL    NOT NULL DEFAULT 0,
    cpc                  REAL    NOT NULL DEFAULT 0,
    total_conversions    REAL    NOT NULL DEFAULT 0,
    total_revenue        REAL    NOT NULL DEFAULT 0,
    total_cvr            REAL    NOT NULL DEFAULT 0,
    total_cpa            REAL    NOT NULL DEFAULT 0,
    total_roas           REAL    NOT NULL DEFAULT 0,
    purchase_conversions REAL    NOT NULL DEFAULT 0,
    purchase_revenue     REAL    NOT NULL DEFAULT 0,
    purchase_cvr         REAL    NOT NULL DEFAULT 0,
    purchase_cpa         REAL    NOT NULL DEFAULT 0,
    purchase_roas        REAL    NOT NULL DEFAULT 0,
    updated_at           TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE (advertiser_id, date),
    FOREIGN KEY (advertiser_id) REFERENCES advertisers (advertiser_id)
);
"""

CREATE_AI_ANALYSIS_RESULTS = """
CREATE TABLE IF NOT EXISTS ai_analysis_results (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    advertiser_id      INTEGER NOT NULL,
    analysis_type      TEXT,
    period_start       TEXT,
    period_end         TEXT,
    input_summary_json TEXT,
    ai_result_text     TEXT,
    model_name         TEXT,
    created_at         TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (advertiser_id) REFERENCES advertisers (advertiser_id)
);
"""

# 실행 순서 (외래키 의존성 고려)
ALL_SCHEMAS = [
    CREATE_ADVERTISERS,
    CREATE_UPLOAD_FILES,
    CREATE_DAILY_PERFORMANCE,
    CREATE_DAILY_SUMMARY,
    CREATE_AI_ANALYSIS_RESULTS,
]
