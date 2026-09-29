import http.server
import socketserver
import urllib.parse
import urllib.request
import json
import time
import os
from searoute import searoute

PORT = 8000

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="../frontend", **kwargs)

    def translate_path(self, path):
        parsed = urllib.parse.urlsplit(path)
        p = parsed.path
        if p.startswith('/frontend/'):
            p = p[len('/frontend'):]
        elif p == '/frontend':
            p = '/'

        aliases = {
            '/ports.html': '/ports_network.html',
            '/ports': '/ports_network.html',
            '/vessels.html': '/vessel_match.html',
            '/vessel.html': '/vessel_match.html',
            '/vessels': '/vessel_match.html',
            '/weather.html': '/weather_forecast.html',
            '/weather': '/weather_forecast.html',
            '/invoice.html': '/trip_invoice.html',
            '/cargo.html': '/trip_invoice.html',
            '/cargo': '/trip_invoice.html',
            '/invoice': '/trip_invoice.html',
            '/dashboard': '/dashboard.html',
        }
        if p in aliases:
            p = aliases[p]
        elif p != '/' and not os.path.splitext(p)[1]:
            frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))
            if os.path.exists(os.path.join(frontend_dir, p.lstrip('/') + '.html')):
                p = p + '.html'

        return super().translate_path(p)

    def end_headers(self):
        # Allow requests from any origin (file://, localhost, etc.)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        clean_path = parsed.path

        # Normalize /frontend/ prefix if requested
        if clean_path.startswith('/frontend/'):
            clean_path = clean_path[len('/frontend'):]
        elif clean_path == '/frontend':
            clean_path = '/'

        # Route aliases
        aliases = {
            '/ports.html': '/ports_network.html',
            '/ports': '/ports_network.html',
            '/vessels.html': '/vessel_match.html',
            '/vessel.html': '/vessel_match.html',
            '/vessels': '/vessel_match.html',
            '/weather.html': '/weather_forecast.html',
            '/weather': '/weather_forecast.html',
            '/invoice.html': '/trip_invoice.html',
            '/cargo.html': '/trip_invoice.html',
            '/cargo': '/trip_invoice.html',
            '/invoice': '/trip_invoice.html',
            '/dashboard': '/dashboard.html',
        }
        if clean_path in aliases:
            clean_path = aliases[clean_path]

        # Ignore missing favicon quietly
        if clean_path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
            return

        # Reconstruct self.path for SimpleHTTPRequestHandler
        self.path = f"{clean_path}?{parsed.query}" if parsed.query else clean_path

        if clean_path == '/api/route':
            query = urllib.parse.parse_qs(parsed.query)
            try:
                origin = [float(query['olon'][0]), float(query['olat'][0])]
                dest = [float(query['dlon'][0]), float(query['dlat'][0])]
                # searoute returns a GeoJSON LineString
                route = searoute(origin, dest)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(route).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))
        elif clean_path == '/api/fuel-prices':
            try:
                url = 'https://query1.finance.yahoo.com/v8/finance/chart/BZ=F?interval=1d&range=1d'
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode())
                    brent = data['chart']['result'][0]['meta']['regularMarketPrice']
                    prev = data['chart']['result'][0]['meta'].get('chartPreviousClose', brent)
                    change = round(brent - prev, 2)
                    vlsfo = round(brent * 6.75, 2)
                    mgo = round(brent * 7.75, 2)
                    ifo = round(brent * 5.25, 2)
                    res = {
                        'source': 'Yahoo Finance (Live Energy Commodities Exchange)',
                        'brent_crude_usd_bbl': brent,
                        'brent_change': change,
                        'vlsfo_usd_mt': vlsfo,
                        'mgo_usd_mt': mgo,
                        'ifo380_usd_mt': ifo,
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
                        'status': 'LIVE_ONLINE'
                    }
            except Exception as e:
                res = {
                    'source': 'Global Bunker Market Benchmark',
                    'brent_crude_usd_bbl': 97.70,
                    'brent_change': 0.0,
                    'vlsfo_usd_mt': 659.50,
                    'mgo_usd_mt': 757.20,
                    'ifo380_usd_mt': 512.90,
                    'timestamp': 'Fallback Reference Index',
                    'status': 'FALLBACK_CACHED',
                    'error': str(e)
                }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
        elif clean_path == '/api/ports':
            try:
                with open('ports_data.json', 'r') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))
        elif clean_path == '/api/vessels':
            try:
                with open('vessels_data.json', 'r') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))
        else:
            super().do_GET()

# To allow reusing the port if it was recently closed
class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

with ThreadedTCPServer(("", PORT), CustomHandler) as httpd:
    print(f"Intelligent Routing Server serving at port {PORT}")
    httpd.serve_forever()
