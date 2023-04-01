from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
from cdcs import CDCS
import xml_parse_api
import os

PORTAL_URL =  os.environ.get('CDCS_HOSTNAME', "https://portal.meta-genome.org/")  
METAG_URL = os.environ.get('CORS_ORIGIN', "http://localhost:3000") 


app = Flask(__name__)
CORS(app, origins=METAG_URL)

@app.route('/avail_data', methods=['GET'])
def return_avail_data():
    with open('available_data.json', 'r') as f:
        data = json.load(f)
    
    return jsonify(data)

@app.route('/get_vals/<keyword>', methods=['GET'])
def get_data(keyword):
    
    curator = CDCS(PORTAL_URL, username='',)
    template = "mecha-metagenome-schema31"        # Make this to not have to be hard-coded
    query_dict1 = "{\"map.metamaterial-material-info\": {\"$exists\": true}}"
    query_dict ="{\"$or\": [{\"$or\": [{\"map.metamaterial-material-info.bulk-density\": {\"$gt\": 0.0}}, {\"map.metamaterial-material-info.bulk-density.#text\": {\"$gt\": 0.0}}]}, {\"$or\": [{\"map.base-material-info.bulk-density\": {\"$gt\": 0.0}}, {\"map.base-material-info.bulk-density.#text\": {\"$gt\": 0.0}}]}]}"
    
    #query_dict = "{\"map.\": {\"$exists\": true}}"
    my_query = curator.query(template=template, mongoquery=query_dict)
    
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

    curator = CDCS(PORTAL_URL, username='',)
    template = "mecha-metagenome-schema31"        # Make this to not have to be hard-coded
    query_dict = "{\"map.\": {\"$exists\": true}}"
    query_dict ="{\"$or\": [{\"$or\": [{\"map.metamaterial-material-info.bulk-density\": {\"$gt\": 0.0}}, {\"map.metamaterial-material-info.bulk-density.#text\": {\"$gt\": 0.0}}]}, {\"$or\": [{\"map.base-material-info.bulk-density\": {\"$gt\": 0.0}}, {\"map.base-material-info.bulk-density.#text\": {\"$gt\": 0.0}}]}]}"
    my_query = curator.query(template=template, mongoquery=query_dict)
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