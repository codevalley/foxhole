import sqlite3
import json
from typing import List, Dict, Any, Optional, TypedDict
import argparse
from datetime import datetime


class TableData(TypedDict):
    data: Dict[str, List[Dict[str, Any]]]
    user_id: str
    export_time: str


class DBInspector:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def get_all_tables(self) -> List[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [row[0] for row in cursor.fetchall()]

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        return [dict(row) for row in cursor.fetchall()]

    def query_table(
        self, table_name: str, user_id: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        query = f"SELECT * FROM {table_name}"
        if user_id:
            query += " WHERE user_id = ?"
            cursor.execute(query + f" LIMIT {limit}", (user_id,))
        else:
            cursor.execute(query + f" LIMIT {limit}")

        return [dict(row) for row in cursor.fetchall()]

    def get_entity_counts(self, user_id: Optional[str] = None) -> Dict[str, int]:
        tables = ["tasks", "topics", "people", "notes"]
        counts = {}

        for table in tables:
            cursor = self.conn.cursor()
            query = f"SELECT COUNT(*) FROM {table}"
            if user_id:
                query += " WHERE user_id = ?"
                cursor.execute(query, (user_id,))
            else:
                cursor.execute(query)

            counts[table] = cursor.fetchone()[0]

        return counts

    def check_recent_activity(
        self, hours: int = 24, user_id: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        tables = ["tasks", "topics", "people", "notes"]
        activity = {}

        for table in tables:
            cursor = self.conn.cursor()
            # Assuming each table has a created_at or updated_at field
            # Adjust the timestamp field based on your schema
            timestamp_field = "updated_at" if table == "notes" else "created_at"

            query = f"""
                SELECT * FROM {table}
                WHERE datetime({timestamp_field}) >= datetime('now', '-{hours} hours')
            """
            if user_id:
                query += " AND user_id = ?"
                cursor.execute(query, (user_id,))
            else:
                cursor.execute(query)

            activity[table] = [dict(row) for row in cursor.fetchall()]

        return activity

    def export_user_data(self, user_id: str, output_path: Optional[str] = None) -> None:
        if not output_path:
            output_path = (
                f"user_data_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

        data: TableData = {
            "user_id": user_id,
            "export_time": datetime.now().isoformat(),
            "data": {},
        }

        tables = ["tasks", "topics", "people", "notes"]
        for table in tables:
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT * FROM {table} WHERE user_id = ?", (user_id,))
            data["data"][table] = [dict(row) for row in cursor.fetchall()]

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

    def close(self) -> None:
        self.conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Foxhole SQLite Database")
    parser.add_argument("--db-path", required=True, help="Path to SQLite database file")
    parser.add_argument("--user-id", help="Filter by user ID")
    parser.add_argument(
        "--export", action="store_true", help="Export user data to JSON"
    )
    parser.add_argument(
        "--hours", type=int, default=24, help="Hours of recent activity to check"
    )

    args = parser.parse_args()

    inspector = DBInspector(args.db_path)

    print("\nDatabase Tables:")
    tables = inspector.get_all_tables()
    for table in tables:
        print(f"- {table}")

    print("\nEntity Counts:")
    counts = inspector.get_entity_counts(args.user_id)
    for table, count in counts.items():
        print(f"{table}: {count}")

    if args.user_id:
        print(f"\nRecent Activity (last {args.hours} hours) for user {args.user_id}:")
        activity = inspector.check_recent_activity(args.hours, args.user_id)
        for table, records in activity.items():
            print(f"\n{table}: {len(records)} records")
            for record in records[:5]:  # Show first 5 records
                print(f"  - {record}")

        if args.export:
            inspector.export_user_data(args.user_id)
            print(f"\nExported user data to user_data_{args.user_id}_*.json")

    inspector.close()


if __name__ == "__main__":
    main()
