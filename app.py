from flask import Flask, request, jsonify
from flask_cors import CORS  # CORS를 위한 임포트

app = Flask(__name__)
CORS(app)  # CORS 설정

# 로그인 정보 (하드코딩된 사용자 이름과 비밀번호)
users = {
    "test": "password"
}

@app.route('/')
def home():
    return jsonify({"message": "Welcome"})

@app.route('/login', methods=['POST'])
def login():
    print("Received request")
    print("Received data:", request.json)
    # JSON 데이터에서 사용자 이름과 비밀번호 추출
    username = request.json.get('username')
    password = request.json.get('password')

    # 하드코딩된 로그인 정보와 비교
    if username in users and users[username] == password:
        return jsonify({"success": True, "message": "Login successful"}), 200
    else:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
