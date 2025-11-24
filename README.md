# Music_Genre_Prediction_API
음악 스트리밍 사용자 활동 기반 선호 장르 예측 Flask API 포트폴리오 프로젝트

비용때문에 서비스 비활성화 중

Python 3.11, Gunicorn, Docker를 사용하여 Cloud Run에 컨테이너화된 방식으로 배포되었습니다.

URL: https://genre-prediction-service-815026823441.asia-northeast3.run.app

경로: /upload_with_json (POST)

## API를 사용하기 위해 필요한 입력 데이터 형식

#### json 요청 본문 1개, json 파일 1개, csv 파일 4개 필요

### json 요청 본문 구조
{

	"gender": 1, # 남자 : 1, 여자 : 0
	"age_group": 20, # 연령 ex) 24세 > 20
	"ei_score": 10, # mbti 점수 ex) ESTJ = 100, 100, 100, 100
	"sn_score": 55,
	"tf_score": 55,
	"jp_score": 45
	
}

### json 파일 1개, csv 파일 4개 준비

#### 1. google takeout(https://takeout.google.com/) 접속

#### 2. 모두 해제 선택
<img width="726" height="690" alt="image" src="https://github.com/user-attachments/assets/106f9153-756b-4b11-8e9d-bdba04cc5d58" />

#### 3. YouTube 및 YouTube Music 데이터 선택

	3-1. 체크박스 클릭

<img width="657" height="214" alt="image" src="https://github.com/user-attachments/assets/c7fba79d-8d8e-464a-911e-9c42df9bd3be" />

	3-2. 필요한 데이터 선택

<img width="322" height="705" alt="image" src="https://github.com/user-attachments/assets/5bbb32bc-0cc8-4be8-adb9-0eade269a935" />

	3-3. 시청기록 데이터 형식 선택 (html > json)

<img width="536" height="852" alt="image" src="https://github.com/user-attachments/assets/96d3d09b-9aa6-4911-89d3-1659042887be" />

#### 4. 데이터 다운로드

<img width="657" height="792" alt="image" src="https://github.com/user-attachments/assets/63a443f3-4415-49b6-b2e6-90c9295dabe6" />

### 5. 데이터 파일명 변경

시청 기록.json

	viewing_history.json

(가장 많이 듣는 재생목록)-동영상.csv

	playlist.csv

music library songs.csv

	music_library_songs.csv
	
구독정보.csv

	subscribed.csv

댓글.csv

	comment.csv


## 로컬 실행

pip install -r requirements.txt 후 python app.py

## 주의사항

시청기록 데이터 1000개(최대) 기준 약 1시간 소요

좋아요, 재생목록, 구독정보, 댓글 csv 파일 내용이 너무 적으면 json 요청 본문으로 장르명을 판단하기 떄문에 각 파일 내에 최소 데이터 10개는 있어야함



