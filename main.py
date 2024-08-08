import sqlite3
from flask import Flask, request, jsonify, render_template
import os
import json

# Use the /tmp directory for the SQLite database in Vercel
DATABASE = '/tmp/sponsor_dashboard.db'

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
            request TEXT NOT NULL,
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
            request TEXT NOT NULL,
            total INTEGER NOT NULL,
            average REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_tables()

def query_db(query, args=(), one=False):
    conn = get_db()
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    conn.close()
    return (rv[0] if rv else None) if one else rv

app = Flask(__name__)

@app.route('/')
def form():
    return render_template('index.html')

@app.route('/submit-form-part1', methods=['POST'])
def submit_form_part1():
    try:
        data = request.form
        client = data.get('client')
        request_text = data.get('request')
        atRisk = int(data.get('atRisk'))
        quarter = int(data.get('quarter'))
        revenue = int(data.get('revenue'))
        comp = int(data.get('comp'))
        urgency = int(data.get('urgency'))

        conn = get_db()
        c = conn.cursor()
        c.execute('''INSERT INTO partial_requests (client, request, atRisk, quarter, revenue, comp, urgency)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (client, request_text, atRisk, quarter, revenue, comp, urgency))
        conn.commit()

        partial_requests = fetch_partial_requests()
        conn.close()

        return jsonify(partial_requests)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/submit-form-part2', methods=['POST'])
def submit_form_part2():
    try:
        data = request.form
        clientId = data.get('clientId')
        client_data = json.loads(data.get('clientData'))

        scout = int(data.get('scout'))
        country = int(data.get('country'))
        resources = int(data.get('resources'))
        strategic = int(data.get('strategic'))

        partial_request = query_db('SELECT * FROM partial_requests WHERE clientId = ?', [clientId], one=True)
        if partial_request is None:
            return jsonify({'error': 'Partial request not found'}), 404

        atRisk, quarter, revenue, comp, urgency = partial_request[3], partial_request[4], partial_request[5], partial_request[6], partial_request[7]
        total = atRisk + quarter + revenue + comp + urgency + scout + country + resources + strategic
        average = total / 9.0  # Adjusted for the new total number of factors

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




@app.route('/get-partial-requests', methods=['GET'])
def get_partial_requests():
    try:
        partial_requests = fetch_partial_requests()
        return jsonify(partial_requests)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    return [dict(clientId=row[0], client=row[1], request=row[2], atRisk=row[3], quarter=row[4], revenue=row[5])
            for row in partial_requests]

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
