import os
import json
import psycopg2
from psycopg2.extras import Json

# PostgreSQL connection settings
conn = psycopg2.connect(
    host="postgres",     # must match service name declared in docker-compose.yml
    dbname="datawarehouse",
    user="ingest",
    password="pw1234",
    port="5432"
)
cur = conn.cursor()

# Root directory containing JSON files in subfolders
root_dir = os.path.abspath('../dataset/openalex')
#root_dir = '/dataset/openalex'  # e.g., './data'

if not os.path.exists(root_dir):
    raise FileNotFoundError(f"Directory not found: {root_dir}")
else:
    print("✅ Found files:", os.listdir(root_dir))
loaded_count = 0

# Walk through directories and read all JSON files
for dirpath, _, filenames in os.walk(root_dir):
    for filename in filenames:
        if filename.endswith('.json'):
            file_path = os.path.join(dirpath, filename)
            try:
                with open(file_path, 'r') as f:
                    content = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"Skipping file {file_path}: {e}")
                continue

            # Insert JSON into raw.openalex
            cur.execute("""
                INSERT INTO raw.openalex (folder_path, filename, data)
                VALUES (%s, %s, %s)
            """, (dirpath, filename, Json(content)))
            loaded_count += 1

# Finalize
conn.commit()
cur.close()
conn.close()
print(f"{loaded_count} JSON files are loaded into raw.openalex")