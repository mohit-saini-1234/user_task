  
from flask import (
    Blueprint, g, request, abort, jsonify , Flask
)
from flask_user import roles_required

from passlib.hash import pbkdf2_sha256
import jwt
from flask_jwt_extended import ( JWTManager,jwt_optional ,
    jwt_required, create_access_token, get_current_user
)
from app.util import serialize_doc
import re
from bson.objectid import ObjectId
import requests
import datetime
from app import mongo
from app import token
from app.token import manager_required
import dateutil.parser
import json
from bson import json_util
from passlib.apps import custom_app_context as pwd_context

bp = Blueprint('user', __name__, url_prefix='/')


@bp.route('/register', methods=['POST'])
@jwt_optional
def register():
   role = request.json.get("role", "user")
   name = request.json.get("name", None)
   username = request.json.get("username", None)
   password = request.json.get("password", None)
   if not name or not username or not password:
       return jsonify({"msg": "Invalid Request"}), 400
 
   check_username = mongo.db.users.count({
       "username" : username 
   })
   if check_username > 0 :
       return jsonify({"msg": "already taken"}), 500

    
   id = mongo.db.users.insert_one({
       "role" : role ,
       "name": name,
       "password": pbkdf2_sha256.hash(password),
       "username": username
   }).inserted_id
   return jsonify(str(id))




@bp.route('/login', methods=['POST'])
def login():
    log_username = request.json.get("username", None)
    password = request.json.get("password", None)
    if not log_username:
        return jsonify(msg="Missing username parameter"), 400
    if not password:
        return jsonify(msg="Missing password parameter"), 400

    is_user = mongo.db.users.find_one({"username": log_username})
    if is_user is None:
        return jsonify(msg="username doesn't exists"), 400

    if not pbkdf2_sha256.verify(password, is_user["password"]):
        return jsonify(msg="password is wrong"), 400
    username1 = log_username
    expires = datetime.timedelta(days=1)
    access_token = create_access_token(identity=username1, expires_delta=expires)
    return jsonify(access_token=access_token), 200



@bp.route('/protected', methods=['GET'])
@jwt_required
def protected():
    current_user = get_current_user()
    current_user["_id"] = str(current_user["_id"])
    user = json.dumps(current_user,default=json_util.default)
    return user, 200


@bp.route('/profile', methods=['PUT', 'GET'])
@jwt_required
def profile():
    current_user = get_current_user()
    current_user["_id"] = str(current_user["_id"])
    user = current_user["_id"]
    return(str({"login as ": user})), 200


@bp.route("/update/<string:id>", methods=['PUT'])
@manager_required
def update_todo(id):

    if not request.json:
        abort(500)

    role = request.json.get("role", "user")
    username = request.json.get("username", "")

    if username is None:
        return jsonify(message="Invalid Request"), 500

    update_json = {}
    if role is not None:
        update_json["role"] = role

    if username is not None:
        update_json["username"] = username


    # match with Object ID
    ret = mongo.db.users.update({
        "_id": ObjectId(id)
    }, {
        "$set": update_json
    }, upsert=False)
    return jsonify(str(ret))

@bp.route("/del_todo/<string:id>", methods=["DELETE"])
@manager_required
def delete_todo(id):

    ret = mongo.db.tasks.remove({
        "_id" : ObjectId(id)
    })

    return jsonify(str(ret))  

   