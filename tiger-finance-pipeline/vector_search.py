
import os

import psycopg2
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

load_dotenv()

# Load a local AI embedding model (384 dimensions)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

documents = [
    ("finance", "Stock prices changed during today's trading session."),
    ("finance", "The company reported higher quarterly revenue."),
    ("technology", "Artificial intelligence improves semantic search."),
    ("technology", "Vector databases store numerical text embeddings."),
    ("weather", "Rainfall increased across the city this morning."),
]

conn = psycopg2.connect(
    host=os.environ["DB_HOST"],
    port=os.environ.get("DB_PORT", "5432"),
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    sslmode="require",
)

register_vector(conn)

try:
    with conn.cursor() as cur:
        for category, content in documents:
            embedding = model.encode(
                content, normalize_embeddings=True
            ).tolist()

            cur.execute(
                """
                INSERT INTO document_embeddings
                    (category, content, embedding)
                VALUES (%s, %s, %s)
                """,
                (category, content, embedding),
            )

    conn.commit()
    print("Documents and embeddings inserted successfully.")

    # Embed a natural-language search query
    query = "finding information about AI and vector databases"
    query_embedding = model.encode(
        query, normalize_embeddings=True
    ).tolist()

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, created_at, category, content,
                   embedding <=> %s AS distance
            FROM document_embeddings
            WHERE created_at >= NOW() - INTERVAL '30 days'
              AND category = %s
            ORDER BY embedding <=> %s
            LIMIT 5
            """,
            (query_embedding, "technology", query_embedding),
        )

        results = cur.fetchall()

    print("\nMost similar technology documents:")
    for row in results:
        print(f"\nCategory: {row[2]}")
        print(f"Content:  {row[3]}")
        print(f"Distance: {row[4]:.4f}")

finally:
    conn.close()
