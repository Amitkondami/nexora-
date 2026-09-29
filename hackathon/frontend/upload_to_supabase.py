import json
import psycopg2
from psycopg2.extras import execute_values
import urllib.parse

# URL-encode the password since it contains an @ symbol
password = urllib.parse.quote_plus("Helloworld0703@gmail.com")
DB_URL = f"postgresql://postgres:{password}@db.rrgwnlfefzcstdtmpojt.supabase.co:5432/postgres"

def main():
    print("Connecting to Supabase PostgreSQL database...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
    except Exception as e:
        print("Failed to connect via direct DB port:", e)
        print("Using the alternate pooler URL just in case...")
        try:
            # Fallback to pooler format
            fallback_url = f"postgresql://postgres.rrgwnlfefzcstdtmpojt:{password}@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"
            conn = psycopg2.connect(fallback_url)
            cur = conn.cursor()
        except Exception as e2:
            print("Fallback failed as well:", e2)
            return

    # Create the table schema
    create_table_query = """
    CREATE TABLE IF NOT EXISTS ports (
        id SERIAL PRIMARY KEY,
        wpi_port_id INTEGER,
        wpi_port_name TEXT,
        state TEXT,
        country TEXT,
        latitude FLOAT,
        longitude FLOAT,
        channel_depth_min_m FLOAT,
        channel_depth_max_m FLOAT,
        anchorage_depth_min_m FLOAT,
        anchorage_depth_max_m FLOAT,
        cargo_pier_depth_min_m FLOAT,
        cargo_pier_depth_max_m FLOAT,
        oil_terminal_depth_min_m FLOAT,
        oil_terminal_depth_max_m FLOAT,
        mean_tidal_range_m FLOAT,
        entrance_restriction_tide BOOLEAN,
        entrance_restriction_heavy_swell BOOLEAN,
        entrance_restriction_ice BOOLEAN,
        entrance_restriction_other BOOLEAN,
        max_vessel_size TEXT,
        point_of_interest TEXT,
        port_size TEXT
    );
    """
    print("Creating ports table...")
    cur.execute(create_table_query)
    conn.commit()

    # Clear existing data just in case
    cur.execute("TRUNCATE TABLE ports;")
    conn.commit()

    print("Loading optimized_ports.json...")
    with open("optimized_ports.json", "r") as f:
        data = json.load(f)

    ports = data.get("ports", [])
    if not ports:
        print("No ports found in JSON.")
        return

    # Prepare data for insertion
    columns = list(ports[0].keys())
    query = f"INSERT INTO ports ({','.join(columns)}) VALUES %s"

    values = []
    for p in ports:
        values.append(tuple(p.get(col) for col in columns))

    print(f"Uploading {len(values)} ports to Supabase...")
    execute_values(cur, query, values)
    conn.commit()
    
    cur.close()
    conn.close()
    print("Successfully uploaded all ports to Supabase!")

if __name__ == "__main__":
    main()
