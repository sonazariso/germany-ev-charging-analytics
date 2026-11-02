-- Apply after DuckDB is installed and once the ETL phase begins.
-- Limits are for DuckDB and do NOT cap total Python / Tableau / macOS RAM usage.
SET memory_limit = '2GB';
SET threads = 4;
SET temp_directory = './data/tmp/duckdb';
SET max_temp_directory_size = '2GB';
