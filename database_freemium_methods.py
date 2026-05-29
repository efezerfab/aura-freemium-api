import os
import psycopg2
import psycopg2.extras
from typing import Optional

DATABASE_URL = os.environ.get("DATABASE_URL", "")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema_freemium.sql")

STATUS_TIMESTAMP_MAP = {
    "processed":   "processed_at",
    "report_sent": "report_sent_at",
    "upsell_sent": "upsell_sent_at",
}


class FreemiumDatabase:
    def _conn(self):
        return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)

    def init_table(self):
        """Create the freemium_leads table if it doesn't exist."""
        with open(SCHEMA_PATH, "r") as f:
            sql = f.read()
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()

    def save_lead(self, lead: dict) -> Optional[int]:
        """
        Insert a new lead. Returns the new row id, or None if duplicate
        (idempotent — safe to call on TikTok retries).
        """
        sql = """
            INSERT INTO freemium_leads
                (email, full_name, current_role, location, career_goal,
                 salary_expectation, tiktok_lead_id, tiktok_form_id,
                 tiktok_ad_id, tiktok_campaign_id, raw_payload)
            VALUES
                (%(email)s, %(full_name)s, %(current_role)s, %(location)s,
                 %(career_goal)s, %(salary_expectation)s, %(tiktok_lead_id)s,
                 %(tiktok_form_id)s, %(tiktok_ad_id)s, %(tiktok_campaign_id)s,
                 %(raw_payload)s::jsonb)
            ON CONFLICT (tiktok_lead_id) DO NOTHING
            RETURNING id;
        """
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, lead)
                row = cur.fetchone()
            conn.commit()
        return row["id"] if row else None

    def update_status(self, lead_id: int, status: str):
        """Update lead status and stamp the appropriate timestamp column."""
        ts_col = STATUS_TIMESTAMP_MAP.get(status)
        if ts_col:
            sql = f"""
                UPDATE freemium_leads
                SET status = %s, {ts_col} = NOW()
                WHERE id = %s;
            """
        else:
            sql = "UPDATE freemium_leads SET status = %s WHERE id = %s;"
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (status, lead_id))
            conn.commit()

    def get_lead_by_id(self, lead_id: int) -> Optional[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM freemium_leads WHERE id = %s;", (lead_id,))
                return cur.fetchone()

    def get_pending_leads(self) -> list:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM freemium_leads WHERE status = 'pending' ORDER BY created_at ASC;"
                )
                return cur.fetchall()

    def get_all_leads(self, limit: int = 100) -> list:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM freemium_leads ORDER BY created_at DESC LIMIT %s;",
                    (limit,)
                )
                return cur.fetchall()


db = FreemiumDatabase()
