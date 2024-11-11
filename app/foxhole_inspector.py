#!/usr/bin/env python3

import sqlite3
import json
from typing import List, Dict, Any, Optional, Tuple
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

    def get_user_by_secret(self, user_secret: str) -> Optional[Tuple[str, str]]:
        """
        Get user ID and screen name using user_secret.
        Returns tuple of (user_id, screen_name) or None if not found
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id, screen_name FROM users WHERE user_secret = ?",
                (user_secret,),
            )
            result = cursor.fetchone()
            if result:
                return result["id"], result["screen_name"]
            self.logger.warning("No user found for provided secret")
            return None
        except Exception as e:
            self.logger.error(f"Error fetching user by secret: {str(e)}")
            return None

    def inspect(
        self, user_secret: Optional[str] = None, hours: int = 24
    ) -> Dict[str, Any]:
        user_info = None
        user_id = None
        if user_secret:
            user_data = self.get_user_by_secret(user_secret)
            if user_data:
                user_id, screen_name = user_data
                user_info = {"id": user_id, "screen_name": screen_name}
            else:
                self.logger.warning("Invalid user_secret provided")

        results: Dict[str, Any] = {
            "inspection_time": datetime.now().isoformat(),
            "user_info": user_info,
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

    def format_text_output(self, results: Dict[str, Any]) -> None:
        """Format inspection results as human-readable text"""
        print("\n=== Foxhole Deployment Inspection ===")
        print(f"Time: {results['inspection_time']}")

        if results.get("user_info"):
            print("\n=== User Information ===")
            print(f"ID: {results['user_info']['id']}")
            print(f"Screen Name: {results['user_info']['screen_name']}")

        print("\n=== Database Status ===")
        db_info = results["database"]
        print(f"Size: {db_info['size_bytes'] / 1024 / 1024:.2f} MB")
        print("\nEntity Counts:")
        for entity, count in db_info["entity_counts"].items():
            print(f"  {entity}: {count}")

        if db_info.get("user_entities"):
            print("\nUser Entities:")
            for entity_type, entities in db_info["user_entities"].items():
                print(f"\n{entity_type.title()}:")
                for entity in entities:
                    print(f"  - {entity}")

        print("\n=== Redis Status ===")
        redis_info = results["redis"]
        if "error" not in redis_info:
            print(f"Memory Used: {redis_info['used_memory']}")
            print(f"Total Keys: {redis_info['total_keys']}")
            if redis_info.get("key_samples"):
                print("\nSample Keys:")
                for key in redis_info["key_samples"]:
                    print(f"  {key}")
        else:
            print(f"Error: {redis_info['error']}")

        print("\n=== MinIO Status ===")
        minio_info = results["minio"]
        if "error" not in minio_info:
            for bucket, info in minio_info["buckets"].items():
                print(f"\nBucket: {bucket}")
                print(f"Objects: {info['object_count']}")
                if info.get("recent_objects"):
                    print("Recent Objects:")
                    for obj in info["recent_objects"]:
                        print(f"  {obj}")
        else:
            print(f"Error: {minio_info['error']}")

        print("\n=== Filesystem Status ===")
        fs_info = results["filesystem"]
        if "error" not in fs_info:
            data_dir = fs_info["data_directory"]
            print(f"Path: {data_dir['path']}")
            print(f"Size: {data_dir['size_bytes'] / 1024 / 1024:.2f} MB")
            print("Contents:")
            for item in data_dir["contents"]:
                print(f"  {item}")
        else:
            print(f"Error: {fs_info['error']}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Inspect Foxhole Deployment")
    parser.add_argument("--user-secret", help="Filter by user secret")
    parser.add_argument(
        "--hours", type=int, default=24, help="Hours of recent activity to check"
    )
    parser.add_argument("--output", help="Output file path (default: stdout)")
    parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    args = parser.parse_args()

    inspector = FoxholeInspector()
    results = inspector.inspect(args.user_secret, args.hours)

    if args.format == "text":
        inspector.format_text_output(results)
    else:
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            print(f"Results written to {args.output}")
        else:
            print(json.dumps(results, indent=2))
