#!/usr/bin/env python3

import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import redis
from minio import Minio
import logging


class FoxholeInspector:
    def __init__(self) -> None:
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("FoxholeInspector")

        # Database is in the mounted volume at /app/data/db/app.db
        self.db_path = "/app/data/db/app.db"
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

        # Redis connection (using default port from docker-compose)
        self.redis_client = redis.Redis(host="redis", port=6379, db=0)

        # MinIO connection
        self.minio_client = Minio(
            "minio:9000",
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=False,
        )

    def inspect(self, user_id: Optional[str] = None, hours: int = 24) -> Dict[str, Any]:
        results = {
            "inspection_time": datetime.now().isoformat(),
            "database": self.inspect_database(user_id, hours),
            "redis": self.inspect_redis(),
            "minio": self.inspect_minio(),
            "filesystem": self.inspect_filesystem(),
            "errors": [],
        }
        return results

    def inspect_database(
        self, user_id: Optional[str] = None, hours: int = 24
    ) -> Dict[str, Any]:
        try:
            return {
                "path": self.db_path,
                "size_bytes": os.path.getsize(self.db_path),
                "tables": self.get_all_tables(),
                "entity_counts": self.get_entity_counts(user_id),
                "recent_activity": self.get_recent_activity(hours, user_id),
                "user_entities": self.get_user_entities(user_id) if user_id else None,
            }
        except Exception as e:
            self.logger.error(f"Database inspection error: {str(e)}")
            return {"error": str(e)}

    def inspect_redis(self) -> Dict[str, Any]:
        try:
            info = self.redis_client.info()
            keys = self.redis_client.keys("*")
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human"),
                "total_keys": len(keys),
                "key_samples": [k.decode() for k in keys[:10]],  # Sample of keys
            }
        except Exception as e:
            self.logger.error(f"Redis inspection error: {str(e)}")
            return {"error": str(e)}

    def inspect_minio(self) -> Dict[str, Any]:
        try:
            buckets = list(self.minio_client.list_buckets())
            bucket_info = {}
            for bucket in buckets:
                objects = list(self.minio_client.list_objects(bucket.name))
                bucket_info[bucket.name] = {
                    "object_count": len(objects),
                    "recent_objects": [obj.object_name for obj in objects[:5]],
                }
            return {"connected": True, "buckets": bucket_info}
        except Exception as e:
            self.logger.error(f"MinIO inspection error: {str(e)}")
            return {"error": str(e)}

    def inspect_filesystem(self) -> Dict[str, Any]:
        try:
            data_dir = "/app/data"
            return {
                "data_directory": {
                    "path": data_dir,
                    "size_bytes": self.get_dir_size(data_dir),
                    "contents": os.listdir(data_dir),
                }
            }
        except Exception as e:
            self.logger.error(f"Filesystem inspection error: {str(e)}")
            return {"error": str(e)}

    def get_user_entities(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        entities = {}
        for table in ["tasks", "topics", "people", "notes"]:
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT * FROM {table} WHERE user_id = ?", (user_id,))
            entities[table] = [dict(row) for row in cursor.fetchall()]
        return entities

    def get_all_tables(self) -> Dict[str, List[Dict[str, Any]]]:
        tables = {}
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for row in cursor.fetchall():
            table_name = row[0]
            cursor.execute(f"PRAGMA table_info({table_name});")
            tables[table_name] = [dict(row) for row in cursor.fetchall()]
        return tables

    def get_entity_counts(self, user_id: Optional[str] = None) -> Dict[str, int]:
        tables = ["tasks", "topics", "people", "notes", "users", "sidekick_threads"]
        counts = {}
        for table in tables:
            cursor = self.conn.cursor()
            query = f"SELECT COUNT(*) FROM {table}"
            if user_id and table != "users":
                cursor.execute(query + " WHERE user_id = ?", (user_id,))
            else:
                cursor.execute(query)
            counts[table] = cursor.fetchone()[0]
        return counts

    def get_recent_activity(
        self, hours: int, user_id: Optional[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        tables = ["tasks", "topics", "people", "notes"]
        activity = {}
        for table in tables:
            cursor = self.conn.cursor()
            query = f"""
            SELECT * FROM {table}
            WHERE 1=1
            {"AND user_id = ?" if user_id else ""}
            ORDER BY rowid DESC LIMIT 5
            """
            if user_id:
                cursor.execute(query, (user_id,))
            else:
                cursor.execute(query)
            activity[table] = [dict(row) for row in cursor.fetchall()]
        return activity

    @staticmethod
    def get_dir_size(path: str) -> int:
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total += os.path.getsize(fp)
        return total


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Inspect Foxhole Deployment")
    parser.add_argument("--user-id", help="Filter by user ID")
    parser.add_argument(
        "--hours", type=int, default=24, help="Hours of recent activity to check"
    )
    parser.add_argument("--output", help="Output file path (default: stdout)")
    parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    args = parser.parse_args()

    inspector = FoxholeInspector()
    results = inspector.inspect(args.user_id, args.hours)

    if args.format == "text":
        # Print human-readable format
        print("\n=== Foxhole Deployment Inspection ===")
        print(f"Time: {results['inspection_time']}")

        print("\n=== Database Status ===")
        db_info = results["database"]
        print(f"Size: {db_info['size_bytes'] / 1024 / 1024:.2f} MB")
        print("\nEntity Counts:")
        for entity, count in db_info["entity_counts"].items():
            print(f"  {entity}: {count}")

        print("\n=== Redis Status ===")
        redis_info = results["redis"]
        if "error" not in redis_info:
            print(f"Memory Used: {redis_info['used_memory']}")
            print(f"Total Keys: {redis_info['total_keys']}")
        else:
            print(f"Error: {redis_info['error']}")

        print("\n=== MinIO Status ===")
        minio_info = results["minio"]
        if "error" not in minio_info:
            for bucket, info in minio_info["buckets"].items():
                print(f"\nBucket: {bucket}")
                print(f"Objects: {info['object_count']}")
        else:
            print(f"Error: {minio_info['error']}")

    else:
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            print(f"Results written to {args.output}")
        else:
            print(json.dumps(results, indent=2))
