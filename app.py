from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

# MongoDB에 연결
client = MongoClient("mongodb://localhost:27017/")
admin_db = client["admin_data"]
user_db = client["user_data"]
bike_db = client["bike_data"]

admins_collection = admin_db["admins"]
users_collection = user_db["users"]
bikes_collection = bike_db["bikes"]

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    admin = admins_collection.find_one({"username": username})
    if admin and admin["password"] == password:
        return jsonify({"success": True, "message": "Login successful", "role": "admin"})
    user = users_collection.find_one({"username": username})
    if user and user["password"] == password:
        return jsonify({"success": True, "message": "Login successful", "role": "user"})
    return jsonify({"success": False, "message": "Invalid username or password"}), 400

# 1. QR 코드로 자전거 확인
@app.route('/check_bike', methods=['POST'])
def check_bike():
    data = request.get_json()
    bike_id = data.get('bike_id')
    
    print(data)
    print(bike_id)

    bike = bikes_collection.find_one({"bike_id": bike_id})
    if bike:
        # 자전거 ID 반환
        return jsonify({"status": "success", "message": "Bike found", "bike_id": bike_id}), 200
    else:
        return jsonify({"status": "error", "message": "Bike ID not found"}), 404

# 2. 자전거 대여 요청 처리
@app.route('/rent_bike', methods=['POST'])
def rent_bike():
    data = request.get_json()
    bike_id = data.get('bike_id')

    # 자전거가 DB에 있는지 확인하고 대여 가능 여부 확인
    bike = bikes_collection.find_one({"bike_id": "b001"})
    print(f"Found bike: {bike}")
    
    if bike:
        if bike["status"] == "available":
            # 대여 가능 시 상태를 "unavailable"로 변경
            bikes_collection.update_one({"bike_id": bike_id}, {"$set": {"status": "available"}})
            return jsonify({"status": "success", "message": "Bike rented successfully"}), 200
        else:
            return jsonify({"status": "error", "message": "Bike is currently unavailable"}), 403
    else:
        return jsonify({"status": "error", "message": "Bike ID not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
