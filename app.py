from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
from cdcs import CDCS
import xml_parse_api
import os
import threading
import time

CDCS_HOSTNAME = os.environ.get('CDCS_HOSTNAME', "https://portal.meta-genome.org/")  
METAG_URL = os.environ.get('CORS_ORIGIN', "https://meta-genome.org") 
FRONTPAGE_USER = os.environ.get('FRONTPAGE_USER', "anonymous")
FRONTPAGE_PASS = os.environ.get('FRONTPAGE_PASS', "")
FRONTPAGE_TOKEN = os.environ.get('FRONTPAGE_TOKEN', "")
CACHE_TTL = int(os.environ.get('CACHE_TTL', 300))  # seconds

TEMPLATE = "mecha-metagenome-schema31"        # Make this to not have to be hard-coded
QUERY = "{\"$or\": [{\"$or\": [{\"map.metamaterial-material-info.bulk-density\": {\"$gt\": 0.0}}, {\"map.metamaterial-material-info.bulk-density.#text\": {\"$gt\": 0.0}}]}, {\"$or\": [{\"map.base-material-info.bulk-density\": {\"$gt\": 0.0}}, {\"map.base-material-info.bulk-density.#text\": {\"$gt\": 0.0}}]}]}"

# Every endpoint runs the same CDCS query, which makes 6+ requests to the
# portal, so cache the result. The first request in each worker fills the
# cache; after that it's refreshed in the background every CACHE_TTL seconds,
# and requests are always answered from the cache.
RETRY_AFTER = 60  # seconds before retrying a failed refresh
_cache = {'records': None, 'refresh_at': 0.0, 'refreshing': False}
_cache_lock = threading.Lock()


def get_curator():
    # Prefer a DRF token: Basic auth costs ~0.4s of password hashing on the
    # portal for every request pycdcs makes, while a token lookup is ~free.
    if FRONTPAGE_TOKEN:
        return CDCS(CDCS_HOSTNAME, username='', token=FRONTPAGE_TOKEN)
    return CDCS(CDCS_HOSTNAME, username=FRONTPAGE_USER, password=FRONTPAGE_PASS)


def fetch_records():
    return get_curator().query(template=TEMPLATE, mongoquery=QUERY, progress_bar=False)


def refresh_records():
    try:
        records = fetch_records()
    except Exception:
        # Keep the cached result and try again shortly
        app.logger.exception("CDCS cache refresh failed")
        with _cache_lock:
            _cache['refresh_at'] = time.monotonic() + RETRY_AFTER
            _cache['refreshing'] = False
        return
    with _cache_lock:
        _cache['records'] = records
        _cache['refresh_at'] = time.monotonic() + CACHE_TTL
        _cache['refreshing'] = False


def get_records():
    with _cache_lock:
        if _cache['records'] is None:
            # Nothing cached yet in this worker: fetch while holding the lock,
            # so concurrent first requests share one fetch
            _cache['records'] = fetch_records()
            _cache['refresh_at'] = time.monotonic() + CACHE_TTL
        elif time.monotonic() >= _cache['refresh_at'] and not _cache['refreshing']:
            _cache['refreshing'] = True
            threading.Thread(target=refresh_records, daemon=True).start()
        return _cache['records']

app = Flask(__name__)
CORS(app, origins=METAG_URL)

# Let browsers reuse responses for a minute, then use them while revalidating
# in the background. The ETag lets revalidation return 304 when nothing changed.
BROWSER_CACHE = "public, max-age=60, stale-while-revalidate=300"


@app.after_request
def add_cache_headers(response):
    if request.method == 'GET' and response.status_code == 200 and request.endpoint != 'index':
        response.headers['Cache-Control'] = BROWSER_CACHE
        response.add_etag()
        response.make_conditional(request)
    return response


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'routes': ['/avail_data', '/get_vals/<keyword>', '/get_pub/<pub_id>']
    })

@app.route('/avail_data', methods=['GET'])
def return_avail_data():
    with open('available_data.json', 'r') as f:
        data = json.load(f)
    
    return jsonify(data)

@app.route('/get_vals/<keyword>', methods=['GET'])
def get_data(keyword):
    
    my_query = get_records()
    
    list_data = []
    for i, row in my_query.iterrows():
        if row.workspace == 1:
            sub_id = row.id
            sub_xml = row.xml_content
            my_parse = xml_parse_api.xml_control(sub_xml)
            data = my_parse.inspect_xml_api(keyword)
            data["id"] = sub_id
            list_data.append(data)
        
    
    
    return jsonify(list_data)


@app.route('/get_pub/<pub_id>', methods=['GET'])
def get_publication(pub_id):

    my_query = get_records()
    sub_id = my_query[my_query['id'] == int(pub_id)].iloc[0]
    sub_xml = sub_id.xml_content
    my_parse = xml_parse_api.xml_control(sub_xml)
    data= my_parse.print_publication_details_api()
    
    img_url = data["img"]
    if img_url:

        img_pid = img_url.split('/')[-1]
        data["img_pid"] = img_pid
    else:

        data['img_pid'] = None
    
    return jsonify(data)



if __name__ == '__main__':
    app.run(debug=True)
