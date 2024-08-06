from flask import Flask, request, jsonify, render_template
import sqlite3
import os
import json

# Database Path
DATABASE = os.path.join(os.path.dirname(__file__), 'sponsor_dashboard.db')

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

def check_db_writability():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)")
        c.execute("INSERT INTO test (id) VALUES (1)")
        conn.commit()
        c.execute("DROP TABLE test")
        conn.commit()
        conn.close()
        print("Database is writable")
    except sqlite3.OperationalError as e:
        print(f"Database is not writable: {e}")

check_db_writability()

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

        conn = get_db()
        c = conn.cursor()
        c.execute('''INSERT INTO partial_requests (client, request, atRisk, quarter, revenue)
                     VALUES (?, ?, ?, ?, ?)''',
                  (client, request_text, atRisk, quarter, revenue))
        conn.commit()
        
        partial_requests = query_db('SELECT * FROM partial_requests')
        conn.close()
        
        return jsonify({'partialRequests': partial_requests})
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

        atRisk, quarter, revenue = partial_request[3], partial_request[4], partial_request[5]
        total = atRisk + quarter + revenue + scout + country + resources + strategic
        average = total / 7.0

        conn = get_db()
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO final_requests (clientId, client, request, total, average)
                     VALUES (?, ?, ?, ?, ?)''',
                  (clientId, client_data['client'], client_data['request'], total, average))
        c.execute('DELETE FROM partial_requests WHERE clientId = ?', [clientId])
        conn.commit()
        
        final_requests = query_db('SELECT * FROM final_requests ORDER BY total DESC')
        conn.close()
        
        return jsonify({'finalRequests': final_requests})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def query_db(query, args=(), one=False):
    conn = get_db()
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    conn.close()
    return (rv[0] if rv else None) if one else rv

if __name__ == '__main__':
    app.run(debug=True)
