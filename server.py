import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
from urllib.parse import parse_qs, urlparse

class ImageCaptionHandler(SimpleHTTPRequestHandler):
    def _send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _load_images(self):
        try:
            with open('./rsicd/dataset_rsicd.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"images": []}

    def _save_images(self, data):
        with open('./images.json', 'w') as f:
            json.dump(data, f, indent=2)

    def do_GET(self):
        # Parse the URL
        parsed_path = urlparse(self.path)
        
        # Handle API endpoints
        if parsed_path.path == '/api/images':
            images = self._load_images()
            self._send_json_response(images)
            return
        
        # Handle placeholder images
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

        # Serve static files
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
                new_caption = data.get('caption')
                
                images = self._load_images()
                
                found = False
                for image in images['images']:
                    if image['id'] == image_id:
                        image['description'] = new_caption
                        found = True
                        break
                
                if found:
                    self._save_images(images)
                    self._send_json_response({"status": "success"})
                else:
                    self._send_json_response(
                        {"status": "error", "message": "Image not found"},
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
    # Create images.json if it doesn't exist
    if not os.path.exists('./images.json'):
        with open('./images.json', 'w') as f:
            json.dump({"images": []}, f, indent=2)
    
    run()
