from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import jwt
import datetime
import bcrypt
from functools import wraps

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'mysecret'

client = MongoClient("mongodb://127.0.0.1:27017")
db = client.playersDB # select the database
players = db.players # select the collection 
users = db.users
blacklist = db.blacklist

def jwt_required(func):
    @wraps(func)
    def jwt_required_wrapper(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message' : 'Token is missing'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
        except:
            return jsonify({'message' : 'Token is invalid'}), 401

        bl_token = blacklist.find_one({"token" :token})
        if bl_token is not None:
            return make_response(jsonify({'message' : 'Token has been cancelled'}), 401)

        return func(*args, **kwargs)

    return jwt_required_wrapper

def admin_required(func):
    @wraps(func)
    def admin_required_wrapper(*args, **kwargs):
        token = request.headers['x-access-token']
        data = jwt.decode(token, app.config['SECRET_KEY'])

        if data["admin"]:
            return func(*args, **kwargs)
        else:
            return make_response(jsonify({'message' : 'Admin access required'}), 401)

    return admin_required_wrapper

#Retrieve all players
@app.route("/api/v1.0/players", methods=["GET"])
def show_all_players():
    page_num, page_size = 1, 800
    if request.args.get("pn"):
        page_num = int(request.args.get("pn"))
    if request.args.get("ps"):
        page_size = int(request.args.get("ps"))
    page_start = page_size * (page_num - 1)

    data_to_return = []
    for player in players.find( 
        {}, { "first_name":1, "second_name":1, "team":1, "goals_scored":1, "assists":1, "goals_conceded":1, "clean_sheets":1, "code":1, "position":1, "comments":1}
        ).skip(page_start).limit(page_size):
        player['_id'] = str(player['_id'])
        for comment in player['comments']:
            comment["_id"] = str(comment['_id'])
        data_to_return.append(player)

    return make_response(jsonify(data_to_return), 200)

#Retrieve players based on position value.
@app.route("/api/v1.0/players/position/<position>", methods=["GET"])
def show_players_by_position(position):
    page_num, page_size = 1, 800
    if request.args.get("pn"):
        page_num = int(request.args.get("pn"))
    if request.args.get("ps"):
        page_size = int(request.args.get("ps"))
    page_start = page_size * (page_num - 1)

    data_to_return = []
    for player in players.find( 
        {'position': position}, { "first_name":1, "second_name":1, "team":1, "goals_scored":1, "assists":1, "goals_conceded":1, "clean_sheets":1, "code":1, "position":1, "comments":1}
        ).skip(page_start).limit(page_size):
        player['_id'] = str(player['_id'])
        for comment in player['comments']:
            comment["_id"] = str(comment['_id'])
        data_to_return.append(player)

    return make_response(jsonify(data_to_return), 200)

#Retrieve players based on team and position values.
@app.route("/api/v1.0/players/<team>/<position>", methods=["GET"])
def show_players_by_team_and_position(team, position):
    page_num, page_size = 1, 800
    if request.args.get("pn"):
        page_num = int(request.args.get("pn"))
    if request.args.get("ps"):
        page_size = int(request.args.get("ps"))
    page_start = page_size * (page_num - 1)

    data_to_return = []
    for player in players.find( 
        {'team': team, 'position': position, }, { "first_name":1, "second_name":1, "team":1, "goals_scored":1, "assists":1, "goals_conceded":1, "clean_sheets":1, "code":1, "position":1, "comments":1}
        ).skip(page_start).limit(page_size):
        player['_id'] = str(player['_id'])
        for comment in player['comments']:
            comment["_id"] = str(comment['_id'])
        data_to_return.append(player)

    return make_response(jsonify(data_to_return), 200)

#Retrieve players with goals_scored value greater or equal to goals value.
@app.route("/api/v1.0/players/goals/<int:goals>", methods=["GET"])
def show_players_by_goals(goals):

    page_num, page_size = 1, 800
    if request.args.get("pn"):
        page_num = int(request.args.get("pn"))
    if request.args.get("ps"):
        page_size = int(request.args.get("ps"))
    page_start = page_size * (page_num - 1)

    data_to_return = []
    for player in players.find( 
        {"goals_scored": {"$gte": goals}}, { "first_name":1, "second_name":1, "team":1, "goals_scored":1, "assists":1, "goals_conceded":1, "clean_sheets":1, "code":1, "position":1, "comments":1}
        ).skip(page_start).limit(page_size):
        player['_id'] = str(player['_id'])
        for comment in player['comments']:
            comment["_id"] = str(comment['_id'])
        data_to_return.append(player)

    return make_response(jsonify(data_to_return), 200)

#Retrieve a single player.
@app.route("/api/v1.0/players/<string:id>", methods=["GET"])
def show_one_player(id):
    player = players.find_one(
        {'_id':ObjectId(id)},
        { "first_name":1, "second_name":1, "team":1, "goals_scored":1, "assists":1, "goals_conceded":1, "clean_sheets":1, "code":1, "position":1, "comments":1}
        )
    if player is not None:
        player['_id'] = str(player['_id'])
        for comment in player['comments']:
            comment['_id'] = str(comment['_id'])
        return make_response(jsonify(player), 200)
    else:
        return make_response( jsonify( {"error" : "Invalid player ID"} ), 404 )

#Add a new player.
@app.route("/api/v1.0/players", methods=["POST"])
@jwt_required
def add_player():
    if "first_name" in request.form and "second_name" in request.form and "team" in request.form and "goals_scored" in request.form and "assists" in request.form \
    and "goals_conceded" in request.form and "clean_sheets" in request.form and "code" in request.form and "position" in request.form:
        new_player = {"first_name" : request.form["first_name"], "second_name" : request.form["second_name"], "team" : request.form["team"], "goals_scored" : request.form["goals_scored"], 
        "assists" : request.form["assists"], "goals_conceded" : request.form["goals_conceded"],"clean_sheets" : request.form["clean_sheets"], "code" : request.form["code"], 
        "position" : request.form["position"], "comments" : []}
        new_player_id = players.insert_one(new_player)
        new_player_link = "http://localhost:5000/api/v1.0/players/" + str(new_player_id.inserted_id)
        return make_response(jsonify({"url": new_player_link}), 201)
    else:
        return make_response(jsonify({"error": "Missing form data"}), 404)

#Edit a player.
@app.route("/api/v1.0/players/<string:id>", methods=["PUT"])
@jwt_required
def edit_player(id):
    if "first_name" in request.form and "second_name" in request.form and "team" in request.form and "goals_scored" in request.form and "assists" in request.form \
    and "goals_conceded" in request.form and "clean_sheets" in request.form and "code" in request.form and "position" in request.form:
        result = players.update_one( {"_id" : ObjectId(id) }, {"$set" :  { "first_name" : request.form["first_name"], "second_name" : request.form["second_name"], "team" : request.form["team"],
        "goals_scored" : request.form["goals_scored"], "assists" : request.form["assists"], "goals_conceded" : request.form["goals_conceded"], "clean_sheets" : request.form["clean_sheets"],
        "code" : request.form["code"], "position" : request.form["position"],} })

        if result.matched_count == 1:
            edited_player_link = "http://localhost:5000/api/v1.0/players/" + id
            return make_response(jsonify( { "url":edited_player_link } ), 200)
        else:
            return make_response( jsonify({ "error":"Invalid player ID" } ), 404)
    else:
        return make_response( jsonify({ "error" : "Missing form data" } ), 404)

#Delete a player.
@app.route("/api/v1.0/players/<string:id>", methods=["DELETE"])
@jwt_required
@admin_required
def delete_player(id):
    result = players.delete_one({"_id" : ObjectId(id)})
    if result.deleted_count == 1:
        return make_response(jsonify({"message": "Player Deleted"}), 204)
    else:
        return make_response(jsonify({"error": "Invalid player ID"}), 404)

#Add a comment for a player.
@app.route("/api/v1.0/players/<string:player_id>/comments", methods=["POST"])
@jwt_required
def add_new_comment(player_id):
    if "username" in request.form and "text" in request.form and "rating" in request.form and "date" in request.form:
        new_comment = {"_id" : ObjectId(), "username" : request.form["username"], "text" : request.form["text"],"rating" : request.form["rating"], "date" : request.form["date"], "votes" : {"likes": 0}}
        players.update_one( { "_id" : ObjectId(player_id) }, { "$push": { "comments" : new_comment } } )
        new_comment_link = "http://localhost:5000/api/v1.0/players/" + player_id +"/comments/" + str(new_comment['_id'])
        return make_response( jsonify( { "url" : new_comment_link } ), 201 )
    else:
        return make_response( jsonify({ "error" : "Missing form data" } ), 404)

#Retrieve all comments for a player.
@app.route("/api/v1.0/players/<string:id>/comments", methods=["GET"]) 
def show_all_comments(id):
    data_to_return = []
    player = players.find_one({"_id" : ObjectId(id)}, { "comments" : 1, "_id" : 0 })

    if player is not None:
        for comment in player["comments"]:
            comment["_id"] = str(comment["_id"])
            data_to_return.append(comment) 
    else:
        return make_response(jsonify({"error": "Invalid player ID"}), 404)

    return make_response( jsonify(data_to_return ), 200)

#Retrieve a single comment for a player.
@app.route("/api/v1.0/players/<string:player_id>/comments/<string:comment_id>", methods=["GET"]) 
def show_one_comment(player_id, comment_id):
    player = players.find_one({ "comments._id" : ObjectId(comment_id) }, { "_id" : 0, "comments.$" : 1 })

    if player is None:
        return make_response(jsonify({"error" : "Invalid player ID or comment ID"}), 404)
    player['comments'][0]['_id'] = str(player['comments'][0]['_id'])

    return make_response( jsonify( player['comments'][0]), 200)

#Edit a comment for a player.
@app.route("/api/v1.0/players/<string:player_id>/comments/<string:comment_id>", methods=["PUT"]) 
@jwt_required
def edit_comment(player_id, comment_id): 
    if "username" in request.form and "text" in request.form and "rating" in request.form and "date" in request.form:
        edited_comment = {"comments.$.username" : request.form["username"], "comments.$.text" : request.form["text"], "comments.$.rating" : request.form['rating'], "comments.$.date" : request.form['date'] }
        result = players.update_one({ "comments._id" : ObjectId(comment_id) }, { "$set" : edited_comment } )
        edit_comment_url = "http://localhost:5000/api/v1.0/players/" + player_id + "/comments/" + comment_id

        if result.matched_count == 1:
            return make_response(jsonify({"url" : edit_comment_url}), 200)
        else:
            return make_response(jsonify({"error" : "Invalid player ID or comment ID"}), 404)
    else:
        return make_response( jsonify({ "error" : "Missing form data" } ), 404)

#Delete a comment for a player.
@app.route("/api/v1.0/players/<string:player_id>/comments/<string:comment_id>", methods=["DELETE"]) 
@jwt_required
@admin_required
def delete_comment(player_id, comment_id):      
    result = players.update_one( { "_id" : ObjectId(player_id) }, { "$pull" : { "comments" : { "_id" : ObjectId(comment_id) } } } ) 

    if result.matched_count == 1:
        return make_response(jsonify({"message": "Comment Deleted"}), 204)
    else:
        return make_response(jsonify({"error": "Invalid player ID or comment ID"}), 404)

#Login to the system.
@app.route('/api/v1.0/login', methods=['GET'])
def login():
    auth = request.authorization
    
    if auth:
        user = users.find_one({'username':auth.username})
        if user is not None:
            if bcrypt.checkpw(bytes(auth.password, 'UTF-8'), user["password"]):
                token = jwt.encode({'user' : auth.username, 'admin' : user["admin"], 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
                return make_response(jsonify({'token':token.decode('UTF-8')}), 200)
            else:
                return make_response(jsonify({'message':'Bad Password'}), 401)
        else:
                return make_response(jsonify({'message':'Bad Username'}), 401)
    return make_response(jsonify({'message':'Authentication Required'}), 401)

#Logout of the system.
@app.route('/api/v1.0/logout', methods=['GET'])
@jwt_required
def logout():
    token = None
    if 'x-access-token' in request.headers:
        token = request.headers['x-access-token']
    if not token:
        return make_response(jsonify({'message' : 'Token is missing'}), 401)
    else:
        blacklist.insert_one({"token":token})
        return make_response(jsonify({'message' : 'Logout successful'}), 200)

if __name__ == "__main__":
    app.run(debug=True)