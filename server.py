import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
from urllib.parse import parse_qs, urlparse
from datetime import datetime

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

    def _load_captions_history(self):
        try:
            with open('./captions_history.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"captions": []}

    def _save_captions_history(self, data):
        with open('./captions_history.json', 'w') as f:
            json.dump(data, f, indent=2)

    def do_GET(self):
        # Parse the URL
        parsed_path = urlparse(self.path)
        
        # Handle API endpoints
        if parsed_path.path == '/api/images':
            images = self._load_images()
            self._send_json_response(images)
            return
        
        # Add endpoint to get caption history for an image
        elif parsed_path.path == '/api/captions-history':
            query_params = parse_qs(parsed_path.query)
            image_id = query_params.get('imageId', [None])[0]
            
            if image_id:
                captions_history = self._load_captions_history()
                image_captions = [c for c in captions_history['captions'] 
                                if c['imageId'] == image_id]
                self._send_json_response({"captions": image_captions})
                return
            else:
                self._send_json_response({"error": "Image ID required"}, 400)
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
                
                # Load current captions history
                captions_history = self._load_captions_history()
                
                # Create new caption entry
                caption_entry = {
                    "imageId": image_id,
                    "caption": new_caption,
                    "timestamp": datetime.now().isoformat(),
                }
                
                # Add new caption to history
                captions_history['captions'].append(caption_entry)
                
                # Save updated history
                self._save_captions_history(captions_history)
                
                # Also update the current caption in the original dataset
                images = self._load_images()
                for image in images['images']:
                    if image['id'] == image_id:
                        image['description'] = new_caption
                        break
                
                self._send_json_response({
                    "status": "success",
                    "caption": caption_entry
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
    # Create captions_history.json if it doesn't exist
    if not os.path.exists('./captions_history.json'):
        with open('./captions_history.json', 'w') as f:
            json.dump({"captions": []}, f, indent=2)
    
    run()
