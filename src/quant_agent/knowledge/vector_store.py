"""Vector store for semantic search using sqlite-vec."""

import json
import sqlite3
import struct
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from quant_agent.core.config import get_settings


class VectorStore:
    def __init__(self, db_path: str | None = None) -> None:
        self._db: sqlite3.Connection | None = None
        self._settings = get_settings()
        self._db_path = db_path or self._settings.sqlite_db_path
        self._initialized = False
        self._dimension = self._settings.embedding_dimension

    def initialize(self) -> None:
        if self._initialized:
            return

        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(self._db_path)
        self._db.enable_load_extension(True)

        try:
            import sqlite_vec

            sqlite_vec.load(self._db)
        except ImportError as e:
            raise ImportError(
                f"sqlite-vec is required. Install with: pip install sqlite-vec\n{e}"
            ) from e

        self._db.enable_load_extension(False)
        self._create_tables()
        self._initialized = True

    def _create_tables(self) -> None:
        cursor = self._db.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT,
                category TEXT,
                published_date TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS document_vectors
            USING vec0(
                embedding FLOAT[{self._dimension}]
            )
        """)

        self._db.commit()

    async def get_embedding(self, text: str) -> list[float]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._settings.ollama_base_url}/api/embeddings",
                json={
                    "model": self._settings.embedding_model,
                    "prompt": text,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])

    def get_embedding_sync(self, text: str) -> list[float]:
        import httpx

        response = httpx.post(
            f"{self._settings.ollama_base_url}/api/embeddings",
            json={
                "model": self._settings.embedding_model,
                "prompt": text,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("embedding", [])

    def _serialize_embedding(self, embedding: list[float]) -> bytes:
        return struct.pack(f"<{len(embedding)}f", *embedding)

    async def add_document(
        self,
        doc_id: str,
        title: str,
        content: str,
        source: str | None = None,
        category: str | None = None,
        published_date: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not self._initialized:
            self.initialize()

        embedding = await self.get_embedding(content)
        metadata_json = json.dumps(metadata) if metadata else None

        import struct

        embedding_bytes = struct.pack(f"<{len(embedding)}f", *embedding)

        self._db.execute(
            """INSERT OR REPLACE INTO documents (id, title, content, source, category, published_date, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (doc_id, title, content, source, category, published_date, metadata_json),
        )

        self._db.execute(
            "INSERT INTO document_vectors (rowid, embedding) VALUES (?, ?)",
            (hash(doc_id) % (2**31), embedding_bytes),
        )

        self._db.commit()

    async def search_similar(
        self,
        query: str,
        category_filter: str | None = None,
        k: int = 5,
    ) -> list[dict[str, Any]]:
        if not self._initialized:
            self.initialize()

        query_embedding = await self.get_embedding(query)

        import struct

        query_bytes = struct.pack(f"<{len(query_embedding)}f", *query_embedding)

        if category_filter:
            cursor = self._db.execute(
                """
                SELECT
                    d.id, d.title, d.content, d.source, d.category, d.metadata,
                    vec_distance_cosine(v.embedding, ?) as distance
                FROM documents d
                JOIN document_vectors v ON d.id = v.rowid
                WHERE v.embedding MATCH ?
                    AND d.category = ?
                ORDER BY distance
                LIMIT ?
                """,
                (query_bytes, category_filter, k),
            )
        else:
            cursor = self._db.execute(
                """
                SELECT
                    d.id, d.title, d.content, d.source, d.category, d.metadata,
                    vec_distance_cosine(v.embedding, ?) as distance
                FROM documents d
                JOIN document_vectors v ON d.id = v.rowid
                WHERE v.embedding MATCH ?
                ORDER BY distance
                LIMIT ?
                """,
                (query_bytes, k),
            )

        results = []
        for row in cursor.fetchall():
            doc = {
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "source": row[3],
                "category": row[4],
                "metadata": json.loads(row[5]) if row[5] else {},
                "distance": row[6],
            }
            results.append(doc)

        return results

    def close(self) -> None:
        if self._db:
            self._db.close()
            self._db = None
            self._initialized = False
