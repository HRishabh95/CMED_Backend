import flask
from flask import request, jsonify
import json
import signal
from flask_cors import CORS
from pymongo import MongoClient
from utils.index_csv import *
from core import argsparser


app = flask.Flask(__name__)
CORS(app)
app.config["DEBUG"] = True

ARGS = argsparser.prepare_args()
mongo_url = 'mongodb://%s:%s@%s:%s' % (ARGS.mongo_user,ARGS.mongo_password,ARGS.mongo_host,ARGS.mongo_port)
client = MongoClient(mongo_url)
dbname=ARGS.db_name
coll_name=ARGS.collection_name
mongo_build=ARGS.mongo_build
mongo_clean=ARGS.mongo_clean

#@app.before_first_request
def before_first_request_func():
    print("Building Mongo")
    ids = mongoimport(ARGS.dummy_data_path, dbname, coll_name, client)

#@atexit.register
def cleanup():
    print("Cleaning up")
    db=client[dbname]
    db.drop_collection(coll_name)

#Clean the mongo before starting
if mongo_clean:
    cleanup()

# Building Mongo with data
if mongo_build:
    before_first_request_func()

# Get all the list of patients in the database
@app.route('/get_patient_list', methods=['GET'])
def get_patient_list():
    result=mongofind_all_specific_col(dbname,client,coll_name,column='Name')
    return jsonify(result)

#Get patients with specific name and specific dob
@app.route('/get_patients', methods=['GET'])
def get_patient():

    request_args = request.get_json(force=True)
    name=''
    if 'name' in list(request_args.keys()):
        name=request_args['name']
        if name:
            name={"$regex": name, '$options': 'i'}

    dob=''
    if 'dob' in list(request_args.keys()):
        dob=request_args['dob']
        if dob:
            #dob = '%s-%s-%s' % (dob.split("-")[0], dob.split("-")[1], dob.split("-")[2])
            dob=dob
    conditions=''
    if 'condition' in list(request_args.keys()):
        conditions=request_args['condition']
        if conditions:
            conditions = {"$regex": conditions, '$options': 'i'}

    query={'name':name,'dob':dob,'texts':conditions}
    result=mongofind_all_specific_cond(dbname,client,coll_name,query)

    return jsonify(result)

# POST Results for queries
@app.route('/post_queries', methods=['POST'])
def post_queries():
    coll_name_queries='patient_queries'
    request_args = request.get_json(force=True)
    pid,query=request_args['id'],request_args['query']
    query1,query2=query.split("|")[0],query.split("|")[1]
    result=mongoimport_onesent(pid,query1,query2,dbname,client,coll_name_queries)
    return jsonify(json.dumps(result))


app.run(host=ARGS.host, port=ARGS.port)
