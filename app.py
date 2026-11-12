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
# portal, so cache the result rather than re-running it per request.
_cache = {'records': None, 'fetched': 0.0}
_cache_lock = threading.Lock()


def get_curator():
    # Prefer a DRF token: Basic auth costs ~0.4s of password hashing on the
    # portal for every request pycdcs makes, while a token lookup is ~free.
    if FRONTPAGE_TOKEN:
        return CDCS(CDCS_HOSTNAME, username='', token=FRONTPAGE_TOKEN)
    return CDCS(CDCS_HOSTNAME, username=FRONTPAGE_USER, password=FRONTPAGE_PASS)


def get_records():
    with _cache_lock:
        if _cache['records'] is None or time.monotonic() - _cache['fetched'] > CACHE_TTL:
            curator = get_curator()
            _cache['records'] = curator.query(template=TEMPLATE, mongoquery=QUERY, progress_bar=False)
            _cache['fetched'] = time.monotonic()
        return _cache['records']

app = Flask(__name__)
CORS(app, origins=METAG_URL)


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
