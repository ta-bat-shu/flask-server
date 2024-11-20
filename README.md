# 자전거 대여 및 관리 시스템 API

이 API는 자전거 대여 및 관리 시스템을 위한 Flask 서버입니다. MongoDB를 사용하여 데이터를 저장하고, GridFS를 통해 이미지 파일을 관리합니다.

---

## API 명세서

### 1. 로그인

- **URL**: `/login`
- **메서드**: `POST`
- **요청 본문**:
    ```json
    {
        "username": "사용자 이름",
        "password": "비밀번호"
    }
    ```
- **응답**:
  - 성공:
    ```json
    {
        "success": true,
        "message": "Login successful",
        "role": "admin" or "user"
    }
    ```
  - 실패:
    ```json
    {
        "success": false,
        "message": "Invalid username or password"
    }
    ```

### 2. 자전거 확인

- **URL**: `/check_bike`
- **메서드**: `POST`
- **요청 본문**:
    ```json
    {
        "bike_id": "자전거 ID"
    }
    ```
- **응답**:
  - 성공:
    ```json
    {
        "status": "success",
        "message": "Bike found",
        "bike_id": "자전거 ID"
    }
    ```
  - 실패:
    ```json
    {
        "status": "error",
        "message": "Bike ID not found"
    }
    ```

### 3. 자전거 대여 요청

- **URL**: `/rent_bike`
- **메서드**: `POST`
- **요청 본문**:
    ```json
    {
        "bike_id": "자전거 ID"
    }
    ```
- **응답**:
  - 성공:
    ```json
    {
        "status": "success",
        "message": "Bike rented successfully"
    }
    ```
  - 실패:
    ```json
    {
        "status": "error",
        "message": "Bike is currently unavailable"
    }
    ```

### 4. 자전거 반납 요청

- **URL**: `/return_bike`
- **메서드**: `POST`
- **요청 본문**:
    ```json
    {
        "bike_id": "자전거 ID"
    }
    ```
- **응답**:
  - 성공:
    ```json
    {
        "status": "success",
        "message": "Bike returned successfully"
    }
    ```
  - 실패:
    ```json
    {
        "status": "error",
        "message": "Bike is already available"
    }
    ```

### 5. 신고 정보 추가

- **URL**: `/reports`
- **메서드**: `POST`
- **폼 데이터**:
  - `bikeId`: 자전거 ID
  - `userId`: 사용자 ID
  - `category`: 신고 카테고리
  - `contents`: 신고 내용
  - `image`: 이미지 파일
- **응답**:
  - 성공:
    ```json
    {
        "message": "Report succeeded"
    }
    ```

### 6. 신고 정보 삭제

- **URL**: `/reports`
- **메서드**: `DELETE`
- **요청 본문**:
    ```json
    {
        "bikeId": "자전거 ID"
    }
    ```
- **응답**:
  - 성공:
    ```json
    {
        "message": "Deleted report"
    }
    ```
  - 실패:
    ```json
    {
        "error": "This report doesn't exist"
    }
    ```

### 7. 모든 신고 정보 조회

- **URL**: `/reports`
- **메서드**: `GET`
- **응답**:
    ```json
    [
        {
            "bikeId": "자전거 ID",
            "userId": "사용자 ID",
            "date": "신고 날짜",
            "category": "신고 카테고리",
            "contents": "신고 내용",
            "image": "이미지 URL (선택적)"
        }
    ]
    ```

### 8. 이미지 로드

- **URL**: `/image/<image_id>`
- **메서드**: `GET`
- **응답**:
  - 성공: 이미지 파일
  - 실패:
    ```json
    {
        "error": "Image not found"
    }
    ```

---

## 함수 설명

- `login()`: 사용자 로그인 처리
- `check_bike()`: 자전거 ID로 자전거 확인
- `rent_bike()`: 자전거 대여 요청 처리
- `return_bike()`: 자전거 반납 요청 처리
- `update_bicycle()`: 자전거 상태 업데이트
- `get_admin()`: 관리자 정보 조회
- `get_user()`: 사용자 정보 조회
- `add_report()`: 신고 정보 추가
- `delete_report()`: 신고 정보 삭제
- `get_all_reports()`: 모든 신고 정보 조회
- `get_image()`: 이미지 파일 로드

---

## DB 구성

### 1. Users Index
- **userId**: 로그인 시 필요한 유저 아이디 [Unique]
- **password**: 로그인 시 필요한 비밀번호

### 2. Admin Index
- **adminId**: 관리자 로그인 시 필요한 관리자 아이디 [Unique]
- **password**: 관리자 로그인 시 필요한 관리자 비밀번호

### 3. Bicycles Index
- **bikeId**: 자전거 고유번호 [Unique]
- **status**: 자전거 상태 (대여 가능, 대여 불가능)

### 4. Reports Index
- **bikeId**: 자전거 고유번호 [Unique]
- **userId**: 유저 아이디 (작성자) [Unique]
- **date**: 신고 전송한 날짜와 시간
- **category**: 신고 유형 (고장 등)
- **contents**: 신고 상세 내용
- **imageId**: 이미지를 불러오기 위한 고유 이미지 아이디 [Unique]

### 5. GridFS: 이미지 관리를 위한 GridFS 라이브러리

#### fs.files Index
- **filename**: 파일 이름
- **chunkSize**: 청크 크기
- **length**: 이미지 전체 크기 [byte]
- **uploadDate**: 이미지가 업로드된 날짜와 시간

#### fs.chunks
- **files_id**: 이미지 고유 아이디 [ObjectId, Unique]
- **data**: 실제 이미지 데이터
