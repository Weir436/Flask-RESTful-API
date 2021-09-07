import json
import json,urllib.request
import pymongo
from pymongo import MongoClient

client = MongoClient("mongodb://127.0.0.1:27017")
db = client.FantasyPL # select the database
players = db["players"]

def getPlayerData():
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"

    data = urllib.request.urlopen(url).read()
    output = json.loads(data)

    playerList = []

    for player in output["elements"]:
        playerDict = {
            "first_name": player["first_name"],
            "second_name": player["second_name"],
            "team": player["team"],
            "goals_scored": player["goals_scored"],
            "assists": player["assists"],
            "goals_conceded": player["goals_conceded"],
            "code": player["code"],
            "position": player["element_type"]
        }

        playerList.append(playerDict)

    with open("players.json", "w") as fout:
        json.dump(playerList, fout)

getPlayerData()
