import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

#Creates new database every time
db_drop_and_create_all()

# End points

#the main endpoint thay show all drinks to customers which is public
@app.route('/drinks')
def getDrinks():
    drinks = []
    try:
        #Query the drinks from the database
        query=Drink.query.all()
        #format the drinks in the short format
        for i in query:
            drinks.append(i.short())
        #return the all drinks formated and 200 success
        return jsonify({
            "success": True,
            "drinks": drinks
        }),200
    #exception if there was an error in the request
    except:
        abort(500)

#end point to get the details of each drink wich only barista and manager have access to
@app.route('/drinks-detail')
#checking if the request is autherized and have get:drinks-detail autherization
@requires_auth('get:drinks-detail')
def getDrinksDetail(payload):
    try:
        drinks = []
        #query all drinks from the database
        query=Drink.query.all()
        #formating all drinks in long format
        for i in query:
            drinks.append(i.long())
        #returning the drinks and 200 success if no problem
        return jsonify({
            "success": True,
            "drinks": drinks
        }),200
    #aborting with 500 if there was a problem
    except:
        abort(500)

#end point to add a drink to the data base which only manager have access to do
@app.route('/drinks', methods=['POST'])
#checking if the request is autherized and have post:drinks autherization
@requires_auth('post:drinks')
def addDrinks(payload):
    try:
        #getting the data submited in the frontend
        form = request.get_json()
        #creating new drink with the data and inserting the new drink to the database
        newDrink = Drink(recipe=json.dumps(form['recipe']), title=form['title'])
        newDrink.insert()
        #returning the new created drink in long format with 200 success if there was no problem
        return jsonify({
            "success": True,
            "drinks": [newDrink.long()]
        }),200
    #aborting with 401 if the was problem in the form 
    except:
        abort(401)

#end point to update a single drink in the database
@app.route('/drinks/<id>', methods=['PATCH'])
#checking if the request is autherized and have patch:drinks autherization
@requires_auth('patch:drinks')
def editDrinks(payload,id):
    try:
        #getting the drink with the submited id from the database
        drink = Drink.query.filter_by(id=id).one_or_none()
        #making sure the drink is avilable
        if( drink == None):
            abort(404)
        #getting the new data from the form
        form = request.get_json()
        #updating the drink data
        drink.recipe = json.dumps(form.get('recipe'))
        drink.title = form.get('title')
        drink.update()
        #returning the new updated drink with 200 success if there was no problem
        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        }),200
    #aborting with 401 if there was problem in the form
    except:
        abort(401)

#end point to delete a drink in the database
@app.route('/drinks/<id>', methods=['DELETE'])
#checking if the request is autherized and have delete:drinks autherization
@requires_auth('delete:drinks')
def deleteDrinks(payload,id):
    try:
        #getting the drink  with the submitted id from the data base
        drink = Drink.query.filter_by(id=id).one_or_none()
        #making sure the drink is avilable
        if( drink == None):
            abort(404)
        #deleting the drink from the database
        drink.delete()
        #returning the id of the deleted drink and 200 success if there was no problem
        return jsonify({
                "success": True,
                "delete": id
            }),200
    #aborting with 401 if there was problem in deleting the drink
    except:
        abort(401)


# Error Handlers

#422 unprocessable error handler
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

#404 resource not found error handler
@app.errorhandler(404)
def resource_not_found(error):
    return jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404

#500 internal server error error handler
@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
                    "success": False, 
                    "error": 500,
                    "message": "internal server error"
                    }), 500

#400 bad request error handler
@app.errorhandler(400)
def bad_request(error):
    return jsonify({
                    "success": False, 
                    "error": 400,
                    "message": "bad request"
                    }), 400

#401 unathorized error handler
@app.errorhandler(401)
def unathorized(error):
    return jsonify({
                    "success": False, 
                    "error": 401,
                    "message": "unathorized"
                    }), 401

#Error handler for autherization error
@app.errorhandler(AuthError)
def auth_error_handler(authError):
    return jsonify({
                    "success": False, 
                    "error": authError.status_code,
                    "message": authError.error.get('description')
                    }), authError.status_code

