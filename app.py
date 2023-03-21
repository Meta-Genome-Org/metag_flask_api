from flask import Flask, jsonify, request, send_file
import requests
from flask_cors import CORS
import json
from cdcs import CDCS
import xml_parse_api
import os
import config

app = Flask(__name__)
CORS(app, origins="http://localhost:3000")

@app.route('/avail_data', methods=['GET'])
def return_avail_data():
    with open('available_data.json', 'r') as f:
        data = json.load(f)
    
    return jsonify(data)

@app.route('/get_vals/<keyword>', methods=['GET'])
def get_data(keyword):
    
    curator = CDCS('https://portal.meta-genome.org/', username="")
    template = "mecha-metagenome-schema31"        # Make this to not have to be hard-coded
    query_dict1 = "{\"map.metamaterial-material-info\": {\"$exists\": true}}"
    query_dict ="{\"$or\": [{\"$or\": [{\"map.metamaterial-material-info.bulk-density\": {\"$gt\": 0.0}}, {\"map.metamaterial-material-info.bulk-density.#text\": {\"$gt\": 0.0}}]}, {\"$or\": [{\"map.base-material-info.bulk-density\": {\"$gt\": 0.0}}, {\"map.base-material-info.bulk-density.#text\": {\"$gt\": 0.0}}]}]}"
    
    #query_dict = "{\"map.\": {\"$exists\": true}}"
    my_query = curator.query(template=template, mongoquery=query_dict)
    #print(my_query) 
    list_data = []
    for i, row in my_query.iterrows():
        if row.workspace == 1:
            sub_id = row.id
            sub_xml = row.xml_content
            my_parse = xml_parse_api.xml_control(sub_xml)
            data = my_parse.inspect_xml_api(keyword)
            data["id"] = sub_id
            list_data.append(data)
        
    json_data = json.dumps(list_data)
    
    return json_data


    # call meta-genome and get all avail submissions
    # iteratively pass each sub xml to xml_parse_api to retreive this list:
    # [ID, [values, values...], units, type,  measure]
    # make list of dicts^
    # new_dict = {"id": sub_list[0], "value": sub_list[1], "type": sub_list[2]}
    # turn into this json object :
    # [{"id": 0, "values": [64, 99.7...], "units":"MPa", "type": "base material", "measure" :"tensile.."}]
    # get all subs...remove "values":none on both side simultaneously... i.e, go down 0, then 1 and remove both together.
    # new json for looping through each values list to make column 0 and 1 the same length.
@app.route('/get_pub/<pub_id>', methods=['GET'])
def get_publication(pub_id):

    curator = CDCS('https://portal.meta-genome.org/', username="")
    template = "mecha-metagenome-schema31"        # Make this to not have to be hard-coded
    #query_dict = "{\"map.metamaterial-material-info\": {\"$exists\": true}}"
    query_dict = "{\"map.\": {\"$exists\": true}}"
    my_query = curator.query(template=template)
    sub_id = my_query[my_query['id'] == int(pub_id)].iloc[0]
    sub_xml = sub_id.xml_content
    my_parse = xml_parse_api.xml_control(sub_xml)
    data= my_parse.print_publication_details_api()
    
    img_url = data["img"]
    img_pid = img_url.split('/')[-1]
    data["img_pid"] = img_pid
    
    json_data = json.dumps(data)

    print(json_data)
    return json_data

@app.route('/get_img/<pid>', methods=['GET'])
def get_img(pid):
    print(pid)
    print("https://portal.meta-genome.org/pid/rest/local/cdcs/"+pid)
    img_response = requests.get("https://portal.meta-genome.org/pid/rest/local/cdcs/"+pid)
    
    if img_response.status_code == 200:

        file_name = img_response.headers.get('Content-Disposition')
        file_type = file_name.split(".")[-1]
    else:
        file_name = "unknown"
        file_type = "unknown"

    img_file = send_file(
        img_response.content,
        mimetype=file_type
    )
    print("ERROR HERE?")
    return img_file

if __name__ == '__main__':
    app.run(debug=True)