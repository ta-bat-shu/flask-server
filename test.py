import requests

url = "http://127.0.0.1:5000/login"

data = {
    "username": "test",
    "password": "password"
}

# POST 요청 보내기
response = requests.post(url, json=data)

# 상태 코드와 응답 내용 출력
print("Status Code:", response.status_code)  # 상태 코드 확인
print("Response JSON:", response.json())  # JSON 응답 확인