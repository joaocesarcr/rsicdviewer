import os
import sqlite3
import csv
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
from urllib.parse import parse_qs, urlparse
from contextlib import closing

class DatabaseManager:
    def __init__(self, db_path='captions.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        with closing(sqlite3.connect(self.db_path)) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS images (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        path TEXT NOT NULL UNIQUE,
                        description TEXT,
                        new_description TEXT
                    )
                ''')
                conn.commit()
    
    def import_csv_data(self, csv_path):
        with closing(sqlite3.connect(self.db_path)) as conn:
            with closing(conn.cursor()) as cursor:
                with open(csv_path, 'r') as f:
                    csv_reader = csv.DictReader(f)
                    for row in csv_reader:
                        cursor.execute('''
                            INSERT INTO images (path, description, new_description)
                            VALUES (?, ?, ?)
                            ON CONFLICT(path) DO UPDATE SET
                                description = excluded.description,
                                new_description = excluded.new_description
                        ''', (
                            row['image_path'],
                            row['caption'],
                            row['caption']  # Initially set new_description same as caption
                        ))
                conn.commit()

class ImageCaptionHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.db = DatabaseManager()
        super().__init__(*args, **kwargs)

    def _send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _get_images(self):
        with closing(sqlite3.connect(self.db.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            with closing(conn.cursor()) as cursor:
                cursor.execute('SELECT * FROM images')
                rows = cursor.fetchall()
                return {'images': [dict(row) for row in rows]}

    def _update_description(self, image_id, new_description):
        with closing(sqlite3.connect(self.db.db_path)) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute('''
                    UPDATE images 
                    SET new_description = ?
                    WHERE id = ?
                ''', (new_description, image_id))
                conn.commit()
                
                cursor.execute('SELECT * FROM images WHERE id = ?', (image_id,))
                return dict(cursor.fetchone())

    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/images':
            images = self._get_images()
            self._send_json_response(images)
            return
        
        elif parsed_path.path.startswith('/api/placeholder/'):
            try:
                _, _, width, height = parsed_path.path.split('/')
                self.send_response(302)
                self.send_header('Location', f'https://via.placeholder.com/{width}x{height}')
                self.end_headers()
                return
            except Exception:
                self.send_error(400, "Invalid placeholder request")
                return

        else:
            if self.path == '/':
                self.path = '/index.html'
            return SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == '/api/save-caption':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                image_id = data.get('imageId')
                new_description = data.get('caption')
                
                if not image_id or not new_description:
                    self._send_json_response(
                        {"error": "Image ID and caption are required"},
                        400
                    )
                    return
                
                updated_image = self._update_description(image_id, new_description)
                
                self._send_json_response({
                    "status": "success",
                    "image": updated_image
                })
                
            except Exception as e:
                self._send_json_response(
                    {"status": "error", "message": str(e)},
                    500
                )
            return

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run(server_class=HTTPServer, handler_class=ImageCaptionHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Server running at http://localhost:{port}")
    httpd.serve_forever()

if __name__ == '__main__':
    db = DatabaseManager()
    
    # Import initial dataset if it exists
    if os.path.exists('captions.csv'):
        db.import_csv_data('captions.csv')
    
    run()
