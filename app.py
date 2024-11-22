from flask import Flask, jsonify, request
from datetime import datetime
from flask_pymongo import PyMongo
from flask_cors import CORS
from bson import ObjectId
import gridfs

app = Flask(__name__)
CORS(app)

# MongoDB 설정
app.config["MONGO_URI"] = "mongodb://localhost:27017/admin"
mongo = PyMongo(app)
fs = gridfs.GridFS(mongo.db)


# 로그인 처리
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        # 요청 데이터 검증
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"success": False, "message": "Username and password are required"}), 400

        # 관리자 확인
        admin = mongo.db.admin.find_one({"adminId": username})
        if admin and admin["password"] == password:
            return jsonify({
                "success": True,
                "message": "Login successful",
                "role": "admin"
            }), 200

        # 사용자 확인
        user = mongo.db.users.find_one({"userId": username})
        if user and user["password"] == password:
            # 사용자 로그인 성공 시 tf_rent를 true로 설정
            mongo.db.users.update_one({"userId": username}, {"$set": {"tf_rent": True}})
            return jsonify({
                "success": True,
                "message": "Login successful",
                "role": "user",
                "tf_rent": True
            }), 200

        # 로그인 실패
        return jsonify({"success": False, "message": "Invalid username or password"}), 400

    except Exception as e:
        return jsonify({"success": False, "message": "Internal server error", "details": str(e)}), 500



# 자전거 대여 요청 처리
@app.route('/rent_bike', methods=['POST'])
def rent_bike():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        bike_id = data.get('bike_id')

        if not user_id or not bike_id:
            return jsonify({"status": "error", "message": "User ID and Bike ID are required"}), 400

        # 사용자 상태 확인
        user = mongo.db.users.find_one({"userId": user_id})
        if not user or not user.get("tf_rent", True):
            return jsonify({"status": "error", "message": "User cannot rent a bike"}), 403

        # 자전거 상태 확인
        bike = mongo.db.bicycles.find_one({"bikeId": bike_id})
        if not bike or bike.get("status") != "available":
            return jsonify({"status": "error", "message": "Bike is not available"}), 403

        # 상태 업데이트
        mongo.db.users.update_one({"userId": user_id}, {"$set": {"tf_rent": False}})
        mongo.db.bicycles.update_one({"bikeId": bike_id}, {"$set": {"status": "unavailable"}})

        return jsonify({"status": "success", "message": "Bike rented successfully"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error", "details": str(e)}), 500


# 자전거 반납 요청 처리
@app.route('/return_bike', methods=['POST'])
def return_bike():
    try:
        data = request.get_json()
        bike_id = data.get('bike_id')
        user_id = data.get('user_id')

        if not bike_id or not user_id:
            return jsonify({"status": "error", "message": "Bike ID and User ID are required"}), 400

        user = mongo.db.users.find_one({"userId": user_id})
        bike = mongo.db.bicycles.find_one({"bikeId": bike_id})

        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        if not bike:
            return jsonify({"status": "error", "message": "Bike not found"}), 404

        if bike.get("status") != "unavailable":
            return jsonify({"status": "error", "message": "Bike is not currently rented"}), 403

        # 상태 업데이트
        mongo.db.users.update_one({"userId": user_id}, {"$set": {"tf_rent": True}})
        mongo.db.bicycles.update_one({"bikeId": bike_id}, {"$set": {"status": "available"}})

        return jsonify({"status": "success", "message": "Bike returned successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error", "details": str(e)}), 500



# QR 코드로 자전거 확인
@app.route('/check_bike', methods=['POST'])
def check_bike():
    try:
        data = request.get_json()
        bike_id = data.get('bike_id')

        if not bike_id:
            return jsonify({"status": "error", "message": "QR code is empty"}), 400

        # 자전거 조회
        bike = mongo.db.bicycles.find_one({"bikeId": bike_id})

        if bike:
            if bike.get("status") == "available":
                return jsonify({"status": "success", "message": "Bike is available", "bike_id": bike_id}), 200
            else:
                return jsonify({"status": "error", "message": "Bike is not available"}), 403
        else:
            return jsonify({"status": "error", "message": "Bike not registered"}), 404

    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error", "details": str(e)}), 500

# 신고 정보 추가
@app.route('/reports', methods=['POST'])
def add_report():
    try:
        bike_id = request.form.get('bikeId')
        user_id = request.form.get('userId')
        report_category = request.form.get('category')
        report_content = request.form.get('contents')
        image = request.files.get('image')

        # 디버깅용 로그 추가
        print(f"Received data: bikeId={bike_id}, userId={user_id}, category={report_category}, contents={report_content}")
        print(f"Image received: {image is not None}")

        if not all([bike_id, user_id, report_category, report_content]):
            return jsonify({"error": "Missing required fields"}), 400

        if image:
            image_id = fs.put(image, filename=image.filename)
        else:
            image_id = None

        mongo.db.reports.insert_one({
            "bikeId": bike_id,
            "userId": user_id,
            "date": datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
            "category": report_category,
            "contents": report_content,
            "imageId": image_id
        })

        return jsonify({"message": "Report succeeded"}), 201
    except Exception as e:
        print(f"Error adding report: {str(e)}")  # 에러 출력
        return jsonify({"error": "Server error", "details": str(e)}), 500


# 신고 정보 조회
@app.route('/reports', methods=['GET'])
def get_reports():
    reports = mongo.db.reports.find({"imageId": {"$exists": True, "$ne": None}})
    report_list = []
    for report in reports:
        report_data = {
            "bikeId": report['bikeId'],
            "userId": report['userId'],
            "date": report['date'],
            "category": report['category'],
            "contents": report['contents'],
            "image": f"http://192.168.1.115:5000/image/{report['imageId']}" if report.get('imageId') else None
        }
        report_list.append(report_data)
    return jsonify(report_list), 200

# 이미지 반환
@app.route('/image/<image_id>', methods=['GET'])
def get_image(image_id):
    image = fs.find_one({"_id": ObjectId(image_id)})
    if image:
        return image.read(), 200, {'Content-Type': image.content_type}
    return jsonify({"error": "Image not found"}), 404

# 자전거 상태 가져오기
@app.route('/bikes', methods=['GET'])
def get_bikes():
    try:
        bikes = mongo.db.bicycles.find({}, {"bikeId": 1, "status": 1, "_id": 0})  # bikeId와 status만 가져오기
        bike_list = [{"bikeId": bike["bikeId"], "status": bike["status"]} for bike in bikes]
        return jsonify(bike_list), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch bikes", "details": str(e)}), 500
    
# 사용자 로그인 기록 가져오기
@app.route('/login_records', methods=['GET'])
def get_login_records():
    try:
        records = mongo.db.users.find({}, {"userId": 1, "_id": 0})  # userId만 가져오기
        login_records = [{"userId": record["userId"]} for record in records]
        return jsonify(login_records), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch login records", "details": str(e)}), 500
    

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
