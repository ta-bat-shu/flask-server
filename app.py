from flask import Flask, request, jsonify
from flask_cors import CORS  # CORS를 위한 임포트

app = Flask(__name__)
CORS(app)  # CORS 설정

# 로그인 정보 (하드코딩된 사용자 이름과 비밀번호)
users = {
    "admin":{
        "password":"adminpassword",
        "role":"admin"
    },
    "user":{
    "password": "userpassword",
    "role":"user"
    }
}

url_database = {
    "https://m.site.naver.com/1uJri":True
}

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username in users and users[username]['password'] == password:
        # 로그인 성공, 역할에 따라 응답
        role = users[username]['role']
        return jsonify({
            "success": True,
            "message": "Login successful",
            "role": role
        })
    else:
        # 로그인 실패
        return jsonify({
            "success": False,
            "message": "Invalid username or password"
        }), 400

@app.route('/check_url', methods=['POST'])
def check_url():
    data = request.json
    url = data.get('url')
    
    if url in url_database:
        return jsonify({"status":"success", "message":"url is valid"}), 200
    else:
        return jsonify({"status":"error", "message":"invalid url"}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
