import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
from urllib.parse import parse_qs, urlparse
import sqlite3

class DatabaseManager:
    def __init__(self, db_path="captions.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

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

    def _get_image(self, image_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, path, description, new_description, third_description 
                FROM images 
                WHERE id = ?
            ''', (image_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'path': row[1],
                    'description': row[2],
                    'new_description': row[3],
                    'third_description': row[4]
                }
            return None

    def _update_description(self, image_id, new_description, third_description):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE images
                SET new_description = ?,
                    third_description = ?
                WHERE id = ?
            ''', (new_description, third_description, image_id))
            conn.commit()
            return self._get_image(image_id)

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/api/image':
            query_params = parse_qs(parsed_path.query)
            image_id = query_params.get('id', [None])[0]
            
            if image_id:
                image = self._get_image(image_id)
                if image:
                    self._send_json_response(image)
                else:
                    self._send_json_response({"error": "Image not found"}, 404)
                return
            else:
                self._send_json_response({"error": "Image ID required"}, 400)
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
        if self.path == '/api/update-description':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                image_id = data.get('id')
                new_description = data.get('description')
                third_description = data.get('third_description')
                
                if not image_id or not new_description or not third_description:
                    self._send_json_response(
                        {"error": "Image ID, description, and third description required"}, 
                        400
                    )
                    return
                
                updated_image = self._update_description(image_id, new_description, third_description)
                
                if updated_image:
                    self._send_json_response({
                        "status": "success",
                        "image": updated_image
                    })
                else:
                    self._send_json_response(
                        {"error": "Image not found"}, 
                        404
                    )
                
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
    run()
