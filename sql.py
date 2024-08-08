import sqlite3

def initialize_database():
    conn = sqlite3.connect('sponsor_dashboard.db')
    c = conn.cursor()

    # Drop existing tables if they exist
    c.execute('''DROP TABLE IF EXISTS partial_requests''')
    c.execute('''DROP TABLE IF EXISTS final_requests''')
    
    # Create table for partial requests with clientId as INTEGER PRIMARY KEY
    c.execute('''CREATE TABLE IF NOT EXISTS partial_requests
                 (clientId INTEGER PRIMARY KEY AUTOINCREMENT, 
                  client TEXT, 
                  request_text TEXT,  # Changed from request to request_text
                  atRisk INTEGER, 
                  quarter INTEGER, 
                  revenue INTEGER, 
                  comp INTEGER, 
                  urgency INTEGER)''')
    
    # Create table for final requests with clientId as INTEGER PRIMARY KEY
    c.execute('''CREATE TABLE IF NOT EXISTS final_requests
                 (clientId INTEGER PRIMARY KEY, 
                  client TEXT, 
                  request_text TEXT,  # Changed from request to request_text
                  total INTEGER, 
                  average REAL)''')
    
    conn.commit()
    conn.close()

initialize_database()

