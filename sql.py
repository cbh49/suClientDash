import sqlite3

def initialize_database():
    conn = sqlite3.connect('sponsor_dashboard.db')
    c = conn.cursor()
    
    # Create table for partial requests
    c.execute('''CREATE TABLE IF NOT EXISTS partial_requests
                 (clientId TEXT PRIMARY KEY, client TEXT, request TEXT, atRisk INTEGER, quarter INTEGER, revenue INTEGER)''')
    
    # Create table for final requests
    c.execute('''CREATE TABLE IF NOT EXISTS final_requests
                 (clientId TEXT PRIMARY KEY, client TEXT, request TEXT, total INTEGER, average REAL)''')
    
    conn.commit()
    conn.close()

initialize_database()
