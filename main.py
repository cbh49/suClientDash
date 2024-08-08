import sqlite3
from flask import Flask, request, jsonify, render_template
import os
import json

# Use the /tmp directory for the SQLite database in Vercel
if os.getenv("VERCEL_ENV"):
    # Running on Vercel
    DATABASE = '/tmp/sponsor_dashboard.db'
else:
    # Running locally
    DATABASE = './sponsor_dashboard.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

def create_tables():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS partial_requests (
            clientId INTEGER PRIMARY KEY AUTOINCREMENT,
            client TEXT NOT NULL,
            request_text TEXT NOT NULL,  # Changed from request to request_text
            atRisk INTEGER NOT NULL,
            quarter INTEGER NOT NULL,
            revenue INTEGER NOT NULL,
            comp INTEGER NOT NULL,
            urgency INTEGER NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS final_requests (
            clientId INTEGER PRIMARY KEY,
            client TEXT NOT NULL,
            request_text TEXT NOT NULL,  # Changed from request to request_text
            total INTEGER NOT NULL,
            average REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_tables()

app = Flask(__name__)

@app.route('/get-partial-requests', methods=['GET'])
def get_partial_requests():
    try:
        partial_requests = fetch_partial_requests()
        return jsonify(partial_requests)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def query_db(query, args=(), one=False):
    conn = get_db()
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def form():
    return render_template('index.html')

@app.route('/submit-form-part1', methods=['POST'])
def submit_form_part1():
    try:
        print("Received form submission")  # Confirm function is called

        # Try to retrieve and print the entire form data
        try:
            data = request.form
            print("Form data received:", data)  # Print the entire form data for debugging
        except Exception as data_error:
            print(f"Error accessing form data: {data_error}")
            return jsonify({'error': f'Error accessing form data: {data_error}'}), 500

        client = data.get('client')
        request_text = data.get('request_text')  # Changed from request to request_text

        # Print received values to debug
        print(f"Client: {client}")
        print(f"Request Text: {request_text}")

        # Insert dummy values for testing if necessary
        atRisk = 0
        quarter = 0
        revenue = 0
        comp = 0
        urgency = 0

        conn = get_db()
        c = conn.cursor()
        try:
            c.execute('''INSERT INTO partial_requests (client, request_text, atRisk, quarter, revenue, comp, urgency)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (client, request_text, atRisk, quarter, revenue, comp, urgency))
            conn.commit()
            print("Data inserted successfully")  # Confirm successful insertion
        except Exception as db_error:
            print(f"Database Insertion Error: {db_error}")
            return jsonify({'error': f'Database Insertion Error: {db_error}'}), 500

        # Fetch the clientId of the newly inserted record
        clientId = c.lastrowid
        print(f"Generated clientId: {clientId}")  # Check what clientId is being generated

        conn.close()

        # Fetch the updated list of partial requests
        partial_requests = fetch_partial_requests()

        # Ensure that the clientId is correctly added to the response
        for request in partial_requests:
            if request['client'] == client and request['request_text'] == request_text:
                request['clientId'] = clientId

        return jsonify(partial_requests)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/submit-form-part2', methods=['POST'])
def submit_form_part2():
    try:
        data = request.form
        clientId = data.get('clientId')
        client_data = json.loads(data.get('clientData'))

        print(f"Received clientId: {clientId}")
        print(f"Received clientData: {client_data}")

        scout = int(data.get('scout'))
        country = int(data.get('country'))
        resources = int(data.get('resources'))
        strategic = int(data.get('strategic'))

        print(f"Received clientId: {clientId}")
        print(f"Received clientData: {client_data}")

        partial_request = query_db('SELECT * FROM partial_requests WHERE clientId = ?', [clientId], one=True)
        if partial_request is None:
            return jsonify({'error': 'Partial request not found'}), 404

        atRisk, quarter, revenue, comp, urgency = partial_request[3], partial_request[4], partial_request[5],partial_request[6], partial_request[7]
        total = atRisk + quarter + revenue + comp + urgency + scout + country + resources + strategic
        average = total / 9.0

        conn = get_db()
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO final_requests (clientId, client, request, total, average)
                     VALUES (?, ?, ?, ?, ?)''',
                  (clientId, client_data['client'], client_data['request'], total, average))
        c.execute('DELETE FROM partial_requests WHERE clientId = ?', [clientId])
        conn.commit()

        final_requests = query_db('SELECT * FROM final_requests ORDER BY total DESC')
        conn.close()

        return jsonify(final_requests)
    except Exception as e:
        return jsonify({'error': str(e)}), 500



def fetch_partial_requests():
    partial_requests = query_db('SELECT * FROM partial_requests')
    return [dict(clientId=row[0], client=row[1], request=row[2], atRisk=row[3], quarter=row[4], revenue=row[5], comp=row[6], urgency=row[7])
            for row in partial_requests]

@app.route('/get-final-requests', methods=['GET'])
def get_final_requests():
    try:
        final_requests = query_db('SELECT * FROM final_requests ORDER BY total DESC')
        return jsonify(final_requests)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete-entry/<int:clientId>', methods=['DELETE'])
def delete_entry(clientId):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM final_requests WHERE clientId = ?', [clientId])
        conn.commit()
        final_requests = query_db('SELECT * FROM final_requests ORDER BY total DESC')
        conn.close()
        return jsonify(final_requests)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def fetch_partial_requests():
    partial_requests = query_db('SELECT * FROM partial_requests')
    return [dict(clientId=row[0], client=row[1], request=row[2], atRisk=row[3], quarter=row[4], revenue=row[5], comp=row[6], urgency=row[7])
            for row in partial_requests]

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
