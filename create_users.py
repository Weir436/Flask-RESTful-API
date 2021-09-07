from pymongo import MongoClient
import bcrypt

client = MongoClient("mongodb://127.0.0.1:27017")
db = client.playersDB      # select the database
users = db.users    # select the collection name

data = [
          { "name" : "Homer Simpson",
            "username" : "homer",  
            "password" : b"homer_s",
            "email" : "homer@springfield.net",
            "admin" : False
          },
          { "name" : "Marge Simpson",
            "username" : "marge",  
            "password" : b"marge_s",
            "email" : "marge@springfield.net",
            "admin" : True
          }
       ]

for new_user in data:
      new_user["password"] = bcrypt.hashpw(new_user["password"], bcrypt.gensalt())
      users.insert_one(new_user)
