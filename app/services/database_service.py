import sqlite3
import os

DB_PATH = "analysis_history.db"


def initialize_database():
    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT,
            overall_score TEXT,
            frameworks TEXT,
            skills TEXT,
            analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_analysis(project_name, score, frameworks, skills):
    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        INSERT INTO analysis_history
        (project_name, overall_score, frameworks, skills)
        VALUES (?, ?, ?, ?)
        """,
        (
            project_name,
            str(score),
            ", ".join(frameworks),
            ", ".join([skill["skill_name"] for skill in skills])
        )
    )

    conn.commit()
    conn.close()


def get_all_analysis():
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.execute("""
        SELECT *
        FROM analysis_history
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows