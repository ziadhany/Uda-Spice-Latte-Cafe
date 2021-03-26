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

#db_drop_and_create_all()


@app.route('/drinks')
def get_drinks():
    drinks = Drink.query.order_by(Drink.id).all()
    if not drinks:
        abort(404)
    return jsonify({"success": True, "drinks": [drink.short() for drink in drinks]})


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(jwt):

    drinks = Drink.query.all()
    return jsonify({"success": True, "drinks": [drink.long() for drink in drinks]})


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drinks(jwt):
    req = request.get_json()
    if req.get('title') and req.get('recipe'):
        req_title = req.get('title')
        req_recipe = json.dumps(req.get('recipe'))
    else:
        abort(400)
    drinks = Drink(title=req_title, recipe=req_recipe)
    drinks.insert()
    return jsonify({"success": True, 'drinks': drinks.long()}), 200


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drinks(jwt, id):
    drink = Drink.query.get(id)
    if drink is None:
        abort(404)
    req = request.get_json()

    if 'title' in req:
        drink.title = req['title']
    if 'recipe' in req:
        drink.recipe = json.dumps(req['recipe'])

    drink.update()
    return jsonify({"success": True, "drinks": [drink.long()]}), 200


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, id):
    drink = Drink.query.get(id)
    if drink:
        drink.delete()
    else:
        abort(404)
    return jsonify({"success": True, "delete": id}), 200


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": "unprocessable"
                    }), 422


@app.errorhandler(404)
def page_not_found(error):
    return jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404


@app.errorhandler(400)
def page_not_found(error):
    return jsonify({
                    "success": False,
                    "error": 400,
                    "message": "Bad Request"
                    }), 400


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
                    "success": False,
                    "error": 401,
                    "message": "Unauthorized"
                    }), 401


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response