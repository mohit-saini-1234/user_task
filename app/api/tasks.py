
from flask import (
    Blueprint, g, request, abort, jsonify , Flask
)
from app.token import manager_required
from bson.objectid import ObjectId
import datetime
import dateutil.parser
from app import mongo
from app import token
import jwt
from flask_jwt_extended import ( JWTManager,jwt_optional ,
    jwt_required, create_access_token, get_current_user
)
from app.util import serialize_doc

bp = Blueprint('tasks', __name__, url_prefix='')


@bp.route('/task_collection', methods=['POST'])
@manager_required
def task_collection():
    task = request.json.get("task", None)
    description = request.json.get("description", None)

    if not task or not description :
           return jsonify({"msg": "Invalid Request"}), 400
    check_task = mongo.db.all_task.count({
       "task" : task 
   })
    if check_task > 0 :
       return jsonify({"msg": "task already in collection"}), 500
    id = mongo.db.all_task.insert_one({
       "task": task,
       "description" : description
   }).inserted_id
    return jsonify(str(id))
        


@bp.route('/assign_tasks', methods=['POST'])
@manager_required
def assign_tasks():
   user_id = request.json.get("user_id", None)
   due = request.json.get("due", None)
   task_id = request.json.get("task_id" , None)
   status = request.json.get("status" , None)

   if due is not None:
        due = datetime.datetime.strptime(due, "%d-%m-%Y")
   else:
        due = datetime.datetime.now()


   if not user_id or not task_id :
       return jsonify({"msg": "Invalid Request"}), 400
 
   check_task = mongo.db.all_task.count({
       "task_id" : task_id 
   })
   if check_task > 0 :
       return jsonify({"msg": "task already assign"}), 500

    
   id = mongo.db.all_task.insert_one({
       "user_id": user_id,
       "due" : due,
       "task_id" : task_id ,
       "status"  : status
   }).inserted_id
   return jsonify(str(id))


@bp.route("/task_update/<string:id>", methods=['PUT'])
@manager_required
def task_update(id):

    if not request.json:
        abort(500)

    task = request.json.get("task", None)
    description = request.json.get("description", None)
    
    update_json = {}
    if task is not None:
        update_json["task"] = task

    if description is not None:
        update_json["description"] = description
    
    
    # match with Object ID
    ret = mongo.db.all_task.update({
        "_id": ObjectId(id)
    }, {
        "$set": update_json
    }, upsert=False)
    return jsonify(str(ret))

@bp.route("/assigned_update/<string:id>", methods=['PUT'])
@manager_required
def assigned_update(id):
    if not request.json:
        abort(500)
    user_id = request.json.get("user_id", None)
    due = request.json.get("due", None)
    task_id = request.json.get("task_id ")

    if user_id is None or  task_id is None :
        return jsonify(message="Invalid Request"), 500
    
    if due is not None:
        update_json["due"] = datetime.datetime.strptime(due, "%d-%m-%Y")
    
    if task_id is not None:
        update_json["task_id"] = task_id
    
    ret = mongo.db.all_task.update({
        "_id": ObjectId(id)
    }, {
        "$set": update_json
    }, upsert=False)
    return jsonify(str(ret))

@bp.route("/get_task", methods=["GET"])
@jwt_required
def get_task():

    user_id = request.json.get("user_id", None)
    q = mongo.db.all_task.find({
        "user_id" : user_id
    })  
    tasks = []
    for x in q:
        tasks.append(serialize_doc(x))
    return jsonify(tasks) 

@bp.route("/task_info/<string:id>", methods=["GET"])
@jwt_required
def task_info(id):
    q = mongo.db.all_task.find({
        "_id" : ObjectId(id)
    })  
    tasks = []
    for x in q:
        
       tasks.append(serialize_doc(x))
    return jsonify(tasks) 

@bp.route("/delete/<string:id>", methods=["DELETE"])
@manager_required
def delete_todo(id):

    ret = mongo.db.all_task.remove({
        "_id" : ObjectId(id)
    })

    return jsonify(str(ret))  
 

   