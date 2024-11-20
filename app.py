from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from datetime import datetime
import gridfs
from bson import ObjectId
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# MongoDB 설정
app.config["MONGO_URI"] = "mongodb://localhost:27017/admin"
mongo = PyMongo(app)
fs = gridfs.GridFS(mongo.db)

# 로그인 처리
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    admin = get_admin(username)
    if admin and admin["password"] == password:
        return jsonify({"success": True, "message": "Login successful", "role": "admin"})

    user = get_user(username)
    if user and user["password"] == password:
        return jsonify({"success": True, "message": "Login successful", "role": "user"})

    return jsonify({"success": False, "message": "Invalid username or password"}), 400

# QR 코드로 자전거 확인 (큐싱 방지)
@app.route('/check_bike', methods=['POST'])
def check_bike():
    try:
        data = request.get_json()  # 요청 데이터를 JSON 형식으로 가져오기
        print(f"Received request data: {data}")  # 수신된 요청 데이터를 출력하여 디버깅

        bike_id = data.get('bike_id')  # QR 코드로 전송된 bike_id 확인

        # 입력된 QR 코드 검증
        if not bike_id:
            print("Error: bike_id is missing from the request")
            return jsonify({"status": "error", "message": "QR 코드가 비어 있습니다."}), 400

        # 자전거 ID 형식 검증 (예: b001, b002 형식)
        if not bike_id.startswith('b') or not bike_id[1:].isdigit() or len(bike_id) != 4:
            print(f"Warning: Invalid bike_id format - {bike_id}")
            return jsonify({"status": "warning", "message": "큐싱 의심: 올바르지 않은 QR 코드 형식"}), 400

        # MongoDB에서 자전거 ID 확인 (bikeId 필드로 조회)
        bike = mongo.db.bicycles.find_one({"bikeId": bike_id})
        print(f"MongoDB query result: {bike}")  # DB에서 조회한 결과 출력

        if bike:
            # 자전거가 대여 가능한 상태인지 확인
            if bike.get("status") == "available":
                print(f"Success: Bike {bike_id} is available for rent")
                return jsonify({"status": "success", "message": "Bike is available for rent", "bike_id": bike_id}), 200
            else:
                print(f"Error: Bike {bike_id} is currently unavailable")
                return jsonify({"status": "error", "message": "Bike is currently unavailable"}), 403
        else:
            print(f"Warning: Bike {bike_id} not found in the database")
            return jsonify({"status": "warning", "message": "큐싱 의심: 등록되지 않은 QR 코드입니다."}), 404
    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({"status": "error", "message": "서버 내부 오류 발생", "details": str(e)}), 500


# 자전거 대여 요청 처리
@app.route('/rent_bike', methods=['POST'])
def rent_bike():
    try:
        data = request.get_json()
        print(f"Received rent bike request: {data}")  # 요청 데이터 디버깅

        bike_id = data.get('bikeId')
        if not bike_id:
            print("Error: bikeId is missing in the request")
            return jsonify({"status": "error", "message": "QR 코드가 비어 있습니다."}), 400

        bike = mongo.db.bicycles.find_one({"bikeId": bike_id})
        print(f"MongoDB query result: {bike}")  # DB 조회 결과 디버깅

        if bike:
            if bike["status"] == "available":
                update_bicycle(bike_id, "available")
                return jsonify({"status": "success", "message": "Bike rented successfully"}), 200
            else:
                return jsonify({"status": "error", "message": "Bike is currently unavailable"}), 403
        else:
            print(f"Error: Bike {bike_id} not found in the database")
            return jsonify({"status": "error", "message": "Bike ID not found"}), 404
    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({"status": "error", "message": "서버 내부 오류 발생", "details": str(e)}), 500

# 자전거 반납 요청 처리
@app.route('/return_bike', methods=['POST'])
def return_bike():
    data = request.get_json()
    bike_id = data.get('bikeId')

    if not bike_id:
        return jsonify({"status": "error", "message": "QR 코드가 비어 있습니다."}), 400

    bike = mongo.db.bicycles.find_one({"bikeId": bike_id})
    if bike:
        if bike["status"] == "unavailable":
            update_bicycle(bike_id, "available")
            return jsonify({"status": "success", "message": "Bike returned successfully"}), 200
        else:
            return jsonify({"status": "error", "message": "Bike is already available"}), 403
    else:
        return jsonify({"status": "error", "message": "Bike ID not found"}), 404

# 자전거 정보 업데이트 (상태 변경)
def update_bicycle(bike_id, status):
    mongo.db.bicycles.update_one({"bikeId": bike_id}, {"$set": {"status": status}})
    return jsonify({"message": "Updated bike status successfully"}), 200

# 관리자 정보 조회
def get_admin(admin_id):
    return mongo.db.admin.find_one({"adminId": admin_id})

# 사용자 정보 조회
def get_user(user_id):
    return mongo.db.users.find_one({"userId": user_id})

# 신고 정보 추가
@app.route('/reports', methods=['POST'])
def add_report():
    try:
        bike_id = request.form.get('bikeId')
        user_id = request.form.get('userId')
        report_category = request.form.get('category')
        report_content = request.form.get('contents')
        image = request.files.get('image')

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
