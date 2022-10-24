import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import desc, exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

with app.app_context():
    db_drop_and_create_all()

# ROUTES

#####################################################################################
#
#    Endpoint pour recuperer la liste courte des boissons
#
#####################################################################################
@app.route('/drinks')
def show_drinks():
    selection = Drink.query.order_by(Drink.id).all()
    
    drinks = [drink.short() for drink in selection]
    
    return jsonify({
        "success": True,
        "drinks": drinks
    })
    

#####################################################################################
#
#    Endpoint pour recuperer la liste des boissons avec les details
#
#####################################################################################
@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
@requires_auth('get:drinks-detail')
def show_drinks_with_detail(payload):
    selection = Drink.query.order_by(Drink.id).all()
    
    drinks = [drink.long() for drink in selection]
    
    return jsonify({
        "success": True,
        "drinks": drinks
    })
    


#####################################################################################
#
#    Endpoint pour pour ajouter une nouvell boisson
#
#####################################################################################
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_new_drink():
    body = request.get_json()

    new_title = body.get('title', None)
    new_recipe = body.get('recipe', None)
    
    if new_title is None or new_recipe is None:
        abort(400)
        
    drink = Drink(title=new_title, recipe=new_recipe)
    
    with app.app_context():
        drink.insert()
    
    try :
         drink = Drink.query.order_by(Drink.id, desc).first()
         return jsonify({
        "success": True,
        "drinks": drink
             })
         
    except Exception as e:
        print(e)


#####################################################################################
#
#    Endpoint pour mettre à jour les info d'une boisson
#
#####################################################################################
@app.route('/drinks/<int:drink_id>', methods=["PATCH"])
@requires_auth('patch:drinks')
def update_drink(drink_id):
     body = request.get_json()
    
     try :
        drink = Drink.query.filter_by(id=drink_id).one_or_none()
        
        if drink is None:
            abort(404)
            
        else:
            drink.title = body.get('title')
            drink.recipe = body.get('recipe')
            drink.update()
            return jsonify({
                "success": True,
                "drinks": drink
            })
            
     except Exception as e:
         print(e)
        
#####################################################################################
#
#    Endpoint pour supprimer une boisson
#
#####################################################################################
@app.route('/drinks/<int:drink_id>', methods=["DELETE"])
@requires_auth('delete:drinks')
def delete_drink(drink_id):
    body = request.get_json()
    
    try :
        drink = Drink.query.filter_by(id=drink_id).one_or_none()
        
        if drink is None:
            abort(404)
            
        else:
           
            drink.delete()
            return jsonify({
                "success": True,
                "delete": drink.id
            })
            
    except Exception as e:
        print(e)

#####################################################################################
#
#    Error Handler
#
#####################################################################################


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422



@app.errorhandler(404)
def not_found(error):
    return jsonify({
         'success': False,
         'error': 404,
         'message': 'Not found'
    }), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": 'Bad request'
    }), 400

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "error": 405,
        "message": 'method not allowed'
    }), 405
    
@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "internal server error"
    }), 500
'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(AuthError)
def server_error(error):
    return jsonify({
        "success": False,
        "error": AuthError.status_code,
        "message": AuthError.error
    }), AuthError.status_code
if __name__ == "__main__":
    app.debug = True
    app.run()
