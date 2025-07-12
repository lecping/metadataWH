import psycopg2

conn = psycopg2.connect(
    host="postgres",     # ✅ must match service name
    port=5432,
    dbname="datawarehouse",
    user="ingest",
    password="pw1234"
)