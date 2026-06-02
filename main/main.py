from dataclasses import dataclass

from flask import Flask, abort, json, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
import requests
from producer import publish

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqldb://root:root@mysql_main:3306/main"
CORS(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

@dataclass
class Product(db.Model):
    id: int
    title: str
    image: str

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    title = db.Column(db.String(200))
    image = db.Column(db.String(200))
    

@dataclass
class ProductUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    product_id = db.Column(db.Integer)

    UniqueConstraint('user_id', 'product_id', name='user_product_unique')
    

@app.route("/api/products")
def index():
    products = Product.query.all()
    return jsonify(products)

@app.route("/api/products/<int:id>/like", methods=["POST"])
def like(id):
    

    try:
        req = requests.get('http://api-backend-1:8000/api/users', timeout=5)
        req.raise_for_status()

        user_data = req.json()
        user_id = user_data["id"]

        existing = ProductUser.query.filter_by(
            user_id=user_id,
            product_id=id
        ).first()
        
        if existing:
            return jsonify({"error": "You already liked this product!"}), 400


        product_user = ProductUser(user_id=user_id, product_id=id)
        db.session.add(product_user)
        db.session.commit()

        publish("product_liked", {"id": id, "user_id": user_id})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Could not reach user service: {e}"}), 502
    except ValueError:
        return jsonify({
            "error": "User service returned invalid response",
            "body": req.text   
        }), 502
    except:
        abort(400, 'You already liked this product!')
    

    return jsonify({"message": f"Product {id} liked successfully"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")