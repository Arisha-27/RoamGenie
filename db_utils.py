import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json

def init_db():
    """Initialize database with all required tables"""
    conn = sqlite3.connect('roamgenie.db')
    cursor = conn.cursor()
    
    # Flight searches table (enhanced)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS flight_searches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        origin TEXT NOT NULL,
        destination TEXT NOT NULL,
        departure_date TEXT NOT NULL,
        return_date TEXT NOT NULL,
        duration_days INTEGER,
        budget_preference TEXT,
        flight_class TEXT,
        estimated_price REAL,
        search_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        user_session_id TEXT,
        search_status TEXT DEFAULT 'completed'
    )
    ''')
    
    # Contacts table (enhanced)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        firstName TEXT NOT NULL,
        secondName TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT,
        source TEXT DEFAULT 'web_form',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_interaction DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'active',
        notes TEXT
    )
    ''')
    
    # Events/activity log table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        event_data TEXT,
        user_identifier TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT,
        user_agent TEXT
    )
    ''')
    
    # System metrics table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS system_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        metric_name TEXT NOT NULL,
        metric_value REAL NOT NULL,
        metric_type TEXT DEFAULT 'counter',
        recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        additional_data TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

# ============= ORIGINAL FUNCTIONS (Enhanced) =============

def log_flight_search(origin, destination, departure_date, return_date, 
                     duration_days, budget_preference, flight_class, estimated_price=None):
    """Log flight search (original function enhanced)"""
    conn = sqlite3.connect('roamgenie.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO flight_searches 
    (origin, destination, departure_date, return_date, duration_days, 
     budget_preference, flight_class, estimated_price)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (origin, destination, departure_date, return_date, duration_days,
          budget_preference, flight_class, estimated_price))
    
    conn.commit()
    conn.close()

def log_event(event_type, event_data=None, user_identifier=None):
    """Log system events"""
    conn = sqlite3.connect('roamgenie.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO events (event_type, event_data, user_identifier)
    VALUES (?, ?, ?)
    ''', (event_type, str(event_data) if event_data else None, user_identifier))
    
    conn.commit()
    conn.close()

def get_total_searches_count():
    """Get total number of flight searches"""
    conn = sqlite3.connect('roamgenie.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM flight_searches")
    count = cursor.fetchone()[0]
    
    conn.close()
    return count

def get_top_destinations(limit=10):
    """Get top destinations by search count"""
    conn = sqlite3.connect('roamgenie.db')
    
    query = '''
    SELECT destination, COUNT(*) as count 
    FROM flight_searches 
    GROUP BY destination 
    ORDER BY count DESC 
    LIMIT ?
    '''
    
    df = pd.read_sql_query(query, conn, params=[limit])
    conn.close()
    return df

def get_top_departures(limit=10):
    """Get top departure cities by search count"""
    conn = sqlite3.connect('roamgenie.db')
    
    query = '''
    SELECT origin, COUNT(*) as count 
    FROM flight_searches 
    GROUP BY origin 
    ORDER BY count DESC 
    LIMIT ?
    '''
    
    df = pd.read_sql_query(query, conn, params=[limit])
    conn.close()
    return df

def get_searches_over_time():
    """Get search counts over time"""
    conn = sqlite3.connect('roamgenie.db')
    
    query = '''
    SELECT DATE(created_at) as date, COUNT(*) as count 
    FROM flight_searches 
    GROUP BY DATE(created_at) 
    ORDER BY date DESC
    LIMIT 30
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def fetch_recent_searches(limit=50):
    """Fetch recent flight searches"""
    conn = sqlite3.connect('roamgenie.db')
    
    query = '''
    SELECT * FROM flight_searches 
    ORDER BY created_at DESC 
    LIMIT ?
    '''
    
    df = pd.read_sql_query(query, conn, params=[limit])
    conn.close()
    return df

def fetch_contacts(limit=100):
    """Fetch contacts from CRM"""
    conn = sqlite3.connect('roamgenie.db')
    
    query = '''
    SELECT * FROM contacts 
    ORDER BY created_at DESC 
    LIMIT ?
    '''
    
    try:
        df = pd.read_sql_query(query, conn, params=[limit])
    except:
        # If table doesn't exist or is empty, return empty DataFrame
        df = pd.DataFrame()
    
    conn.close()
    return df

# ============= NEW ENHANCED FUNCTIONS =============

def get_recent_searches_count(days=7):
    """Get number of searches in last N days"""
    conn = sqlite3.connect('roamgenie.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT COUNT(*) FROM flight_searches 
    WHERE created_at >= date('now', '-{} days')
    '''.format(days))
    
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_average_trip_duration():
    """Get average trip duration"""
    conn = sqlite3.connect('roamgenie.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT AVG(duration_days) FROM flight_searches WHERE duration_days IS NOT NULL")
    avg_duration = cursor.fetchone()[0]
    
    conn.close()
    return avg_duration if avg_duration else 0

def get_budget_distribution():
    """Get budget preference distribution"""
    conn = sqlite3.connect('roamgenie.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT budget_preference, COUNT(*) as count 
    FROM flight_searches 
    WHERE budget_preference IS NOT NULL
    GROUP BY budget_preference 
    ORDER BY count DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_class_distribution():
    """Get flight class distribution"""
    conn = sqlite3.connect('roamgenie.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT flight_class, COUNT(*) as count 
    FROM flight_searches 
    WHERE flight_class IS NOT NULL
    GROUP BY flight_class 
    ORDER BY count DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_monthly_searches():
    """Get searches for current month"""
    conn = sqlite3.connect('roamgenie.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT COUNT(*) FROM flight_searches 
    WHERE created_at >= date('now', 'start of month')
    ''')
    
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_weekly_growth_rate():
    """Calculate weekly growth rate"""
    conn = sqlite3.connect('roamgenie.db')
    cursor = conn.cursor()
    
    # This week
    cursor.execute('''
    SELECT COUNT(*) FROM flight_searches 
    WHERE created_at >= date('now', '-7 days')
    ''')
    this_week = cursor.fetchone()[0]
    
    # Last week
    cursor.execute('''
    SELECT COUNT(*) FROM flight_searches 
    WHERE created_at >= date('now', '-14 days') 
    AND created_at < date('now', '-7 days')
    ''')
    last_week = cursor.fetchone()[0]
    
    conn.close()
    
    if last_week == 0:
        return 0
    
    growth_rate = ((this_week - last_week) / last_week) * 100
    return growth_rate

def fetch_all_searches():
    """Fetch all flight searches for export"""
    conn = sqlite3.connect('roamgenie.db')
    
    query = '''
    SELECT 
        origin as "Departure City",
        destination as "Destination",
        departure_date as "Departure Date",
        return_date as "Return Date",
        duration_days as "Trip Duration (Days)",
        budget_preference as "Budget Preference",
        flight_class as "Flight Class",
        estimated_price as "Estimated Price",
        created_at as "Search Date"
    FROM flight_searches 
    ORDER BY created_at DESC
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def generate_analytics_summary():
    """Generate analytics summary for export"""
    conn = sqlite3.connect('roamgenie.db')
    
    # Summary statistics
    summary_data = []
    
    # Total searches
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM flight_searches")
    total_searches = cursor.fetchone()[0]
    summary_data.append(["Total Flight Searches", total_searches])
    
    # Total contacts
    cursor.execute("SELECT COUNT(*) FROM contacts")
    total_contacts = cursor.fetchone()[0]
    summary_data.append(["Total CRM Contacts", total_contacts])
    
    # Top destination
    cursor.execute('''
    SELECT destination, COUNT(*) as count 
    FROM flight_searches 
    GROUP BY destination 
    ORDER BY count DESC 
    LIMIT 1
    ''')
    top_dest = cursor.fetchone()
    if top_dest:
        summary_data.append(["Top Destination", f"{top_dest[0]} ({top_dest[1]} searches)"])
    
    # Top departure
    cursor.execute('''
    SELECT origin, COUNT(*) as count 
    FROM flight_searches 
    GROUP BY origin 
    ORDER BY count DESC 
    LIMIT 1
    ''')
    top_origin = cursor.fetchone()
    if top_origin:
        summary_data.append(["Top Departure City", f"{top_origin[0]} ({top_origin[1]} searches)"])
    
    # Most popular budget
    cursor.execute('''
    SELECT budget_preference, COUNT(*) as count 
    FROM flight_searches 
    WHERE budget_preference IS NOT NULL
    GROUP BY budget_preference 
    ORDER BY count DESC 
    LIMIT 1
    ''')
    top_budget = cursor.fetchone()
    if top_budget:
        summary_data.append(["Most Popular Budget", f"{top_budget[0]} ({top_budget[1]} searches)"])
    
    # Average trip duration
    cursor.execute("SELECT AVG(duration_days) FROM flight_searches WHERE duration_days IS NOT NULL")
    avg_duration = cursor.fetchone()[0]
    if avg_duration:
        summary_data.append(["Average Trip Duration", f"{avg_duration:.1f} days"])
    
    conn.close()
    
    # Convert to DataFrame and then CSV
    df = pd.DataFrame(summary_data, columns=["Metric", "Value"])
    return df.to_csv(index=False)

# ============= ADMIN FUNCTIONS =============

def log_enhanced_flight_search(origin, destination, departure_date, return_date, 
                             duration_days, budget_preference, flight_class, 
                             estimated_price=None, user_session_id=None):
    """Enhanced flight search logging with session tracking"""
    conn = sqlite3.connect('roamgenie.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO flight_searches 
    (origin, destination, departure_date, return_date, duration_days, 
     budget_preference, flight_class, estimated_price, user_session_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (origin, destination, departure_date, return_date, duration_days,
          budget_preference, flight_class, estimated_price, user_session_id))
    
    conn.commit()
    conn.close()

def log_enhanced_contact(firstName, secondName, email, phone, source='web_form'):
    """Enhanced contact logging with duplicate handling"""
    conn = sqlite3.connect('roamgenie.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO contacts (firstName, secondName, email, phone, source)
        VALUES (?, ?, ?, ?, ?)
        ''', (firstName, secondName, email, phone, source))
        
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Email already exists, update instead
        cursor.execute('''
        UPDATE contacts 
        SET firstName=?, secondName=?, phone=?, last_interaction=CURRENT_TIMESTAMP
        WHERE email=?
        ''', (firstName, secondName, phone, email))
        conn.commit()
        return False
    finally:
        conn.close()

def get_flight_analytics():
    """Get comprehensive flight analytics for admin dashboard"""
    conn = sqlite3.connect('roamgenie.db')
    
    query = '''
    SELECT 
        fs.*,
        DATE(fs.created_at) as search_date,
        strftime('%Y-%m', fs.created_at) as search_month,
        strftime('%w', fs.created_at) as day_of_week,
        strftime('%H', fs.created_at) as hour_of_day
    FROM flight_searches fs 
    WHERE fs.created_at >= date('now', '-90 days')
    ORDER BY fs.created_at DESC
    '''
    
    df = pd.read_sql_query(query, conn)
    
    if not df.empty:
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['search_date'] = pd.to_datetime(df['search_date'])
    
    conn.close()
    return df

def get_admin_summary_stats():
    """Get summary statistics for admin dashboard"""
    conn = sqlite3.connect('roamgenie.db')
    cursor = conn.cursor()
    
    stats = {}
    
    # Total counts
    cursor.execute("SELECT COUNT(*) FROM flight_searches")
    stats['total_searches'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM contacts")
    stats['total_contacts'] = cursor.fetchone()[0]
    
    # Recent activity (last 24 hours)
    cursor.execute("""
    SELECT COUNT(*) FROM flight_searches 
    WHERE created_at >= datetime('now', '-1 day')
    """)
    stats['searches_24h'] = cursor.fetchone()[0]
    
    cursor.execute("""
    SELECT COUNT(*) FROM contacts 
    WHERE created_at >= datetime('now', '-1 day')
    """)
    stats['contacts_24h'] = cursor.fetchone()[0]
    
    # Top destinations this month
    cursor.execute("""
    SELECT destination, COUNT(*) as count 
    FROM flight_searches 
    WHERE created_at >= date('now', 'start of month')
    GROUP BY destination 
    ORDER BY count DESC 
    LIMIT 5
    """)
    stats['top_destinations'] = cursor.fetchall()
    
    # Average trip duration
    cursor.execute("SELECT AVG(duration_days) FROM flight_searches WHERE duration_days IS NOT NULL")
    avg_duration = cursor.fetchone()[0]
    stats['avg_trip_duration'] = round(avg_duration, 1) if avg_duration else 0
    
    conn.close()
    return stats

def initialize_admin_system():
    """Initialize the complete system"""
    init_db()
    
    # Log system startup
    log_event('system_startup', {'timestamp': datetime.now().isoformat()})
    
    print("✅ RoamGenie database system initialized successfully!")

# Initialize on import
try:
    initialize_admin_system()
except Exception as e:
    print(f"⚠️ Warning: Could not initialize database: {e}")

# ============= UTILITY FUNCTIONS =============

def backup_database():
    """Create a backup of the database"""
    import shutil
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"roamgenie_backup_{timestamp}.db"
    
    try:
        shutil.copy('roamgenie.db', backup_name)
        return backup_name
    except Exception as e:
        print(f"Backup failed: {e}")
        return None

def get_database_info():
    """Get database information and statistics"""
    conn = sqlite3.connect('roamgenie.db')
    cursor = conn.cursor()
    
    info = {}
    
    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    info['tables'] = tables
    
    # Get row counts for each table
    table_counts = {}
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        table_counts[table] = cursor.fetchone()[0]
    info['table_counts'] = table_counts
    
    # Database file size
    import os
    if os.path.exists('roamgenie.db'):
        info['file_size_mb'] = round(os.path.getsize('roamgenie.db') / (1024*1024), 2)
    
    conn.close()
    return info
def get_database_info():
    """Get database information and statistics"""
    conn = sqlite3.connect('roamgenie.db')
    cursor = conn.cursor()
    
    info = {}
    
    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    info['tables'] = tables
    
    # Get row counts for each table
    table_counts = {}
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            table_counts[table] = cursor.fetchone()[0]
        except:
            table_counts[table] = 0
    info['table_counts'] = table_counts
    
    # Database file size
    import os
    if os.path.exists('roamgenie.db'):
        info['file_size_mb'] = round(os.path.getsize('roamgenie.db') / (1024*1024), 2)
    else:
        info['file_size_mb'] = 0
    
    conn.close()
    return info

def backup_database():
    """Create a backup of the database"""
    import shutil
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"roamgenie_backup_{timestamp}.db"
    
    try:
        shutil.copy('roamgenie.db', backup_name)
        return backup_name
    except Exception as e:
        print(f"Backup failed: {e}")
        return None
def get_flight_analytic():
    """Get comprehensive flight analytics for admin dashboard"""
    conn = sqlite3.connect('roamgenie.db')
    
    query = '''
    SELECT 
        fs.*,
        DATE(fs.created_at) as search_date,
        strftime('%Y-%m', fs.created_at) as search_month,
        strftime('%w', fs.created_at) as day_of_week,
        strftime('%H', fs.created_at) as hour_of_day
    FROM flight_searches fs 
    WHERE fs.created_at >= date('now', '-90 days')
    ORDER BY fs.created_at DESC
    '''
    
    df = pd.read_sql_query(query, conn)
    
    if not df.empty:
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['search_date'] = pd.to_datetime(df['search_date'])
    
    conn.close()
    return df
