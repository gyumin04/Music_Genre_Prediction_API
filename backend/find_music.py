import pylast
import time
import random
import pandas as pd
import json
import subprocess
import re
import os
from dotenv import load_dotenv

def find_music(viewimg_json, playlist_csv, like_video_csv, subscribed_csv, comment_csv):
    load_dotenv()

    VIEWING_JSON = viewimg_json

    # 시청기록 파일 불러오기
    with open(VIEWING_JSON, 'r', encoding='utf-8') as f:
        viewing_data = json.load(f)

    filtered_music_data = [
        item 
        for item in viewing_data 
        if item.get("header") == "YouTube Music"
    ]

    music_data_df = pd.DataFrame(filtered_music_data)

    music_url_list = music_data_df['titleUrl'].tolist()

    # 데이터 개수 제한
    if len(music_url_list) > 1000:
        music_url_list = music_url_list[:1000]

    title = []
    channel_name = []
    url = []

    # 영상 제목 및 채널명 추출 함수
    def get_metadata_or_skip(video_id):
        try:
            command = [
                'yt-dlp', 
                '--skip-download', 
                '--print-json', 
                video_id
            ]
            
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            
            metadata = json.loads(result.stdout)
            return metadata
        
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.lower()

            if 'private' in error_message or 'paid' in error_message or 'sign in' in error_message:
                print(f"ID {video_id}: 프리미엄/접근 불가 동영상으로 판단되어 제외합니다.")
                return None
            else:
                print(f"ID {video_id}: 알 수 없는 오류 발생: {e.stderr}")
                return None
            
        except json.JSONDecodeError:
            print(f"ID {video_id}: 메타데이터 디코딩 실패. 제외합니다.")
            return None

    # backoff 함수
    def matadata_request_with_exponential_backoff(video_id, max_retries=5):
        
        INITIAL_DELAY = 1
        MAX_DELAY = 60
        
        for attempt in range(max_retries):
            try:
                matadata = get_metadata_or_skip(video_id)
                return matadata

            except Exception as e:
                
                error_message = str(e)
                
                print(f"API 오류 발생: {error_message}")
                
                if attempt < max_retries - 1:
                    delay_time = min(INITIAL_DELAY * (2 ** attempt) + random.random(), MAX_DELAY)
                    
                    print(f"    {delay_time:.2f}초 후 재시도합니다...")
                    time.sleep(delay_time)
                else:
                    print("최대 재시도 횟수 초과. 작업을 중단합니다.")
                    return []
        return []

    # 영상 제목 및 채널명 추출
    for i in range(len(music_url_list)):
        info_dict = matadata_request_with_exponential_backoff(music_url_list[i])
        if info_dict != None:
            title.append(info_dict.get('title'))
            channel_name.append(info_dict.get('channel'))
            url.append(music_url_list[i])

            print(f"시청기록 분석중 : {((i+1)/len(music_url_list))*100}%")

    dict_tc = {
        "title" : title,
        "channel_name" : channel_name,
        "url" : url
    }

    music_data = pd.DataFrame(dict_tc)

    artist_data = music_data["channel_name"].tolist()
    track_data = music_data["title"].tolist()
    url_data = music_data["url"].tolist()

    # API KEY
    API_KEY = os.getenv("API_KEY")
    API_SECRET = os.getenv("API_SECRET")

    if not API_KEY:
        raise ValueError("API_KEY 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")

    if not API_SECRET:
        raise ValueError("API_SECRET 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")

    network = pylast.LastFMNetwork(
        api_key=API_KEY, 
        api_secret=API_SECRET
    )

    # 장르 선택을 위한 genre map
    GENRE_MAP = {
        'Pop': [
            'pop', 'pop rock', 'synthpop', 'j-pop', 'k-pop', 
            'dance pop', 'teen pop', 'mainstream', 'bubblegum pop'
        ],
        'Hiphop': [
            'hip hop', 'rap', 'trap', 'r&b', 'gangsta rap', 
            'abstract hip hop', 'conscious hip hop', 'old school'
        ],
        'Rock': [
            'rock', 'classic rock', 'indie rock', 'alternative rock', 'hard rock', 
            'metal', 'punk', 'emo', 'grunge', 'prog rock', 'glam rock', 'shoegaze'
        ],
        'Classic': [
            'classical', 'orchestral', 'opera', 'baroque', 'romantic', 
            'chamber music', 'symphony'
        ],
        'EDM': [
            'electronic', 'edm', 'dance', 'trance', 'house', 
            'techno', 'dubstep', 'ambient', 'idm', 'drum and bass'
        ],
        'Ballad': [
            'ballad', 'slow', 'acoustic', 'love songs', 'soft rock', 
            'k-ballad'
        ],
        'Jazz': [
            'jazz', 'smooth jazz', 'fusion', 'bebop', 'swing', 
            'dixieland', 'big band', 'vocal jazz'
        ]
    }

    # 장르 추출 함수
    def classify_genre(track_name, artist_name, network, top_n_tags=5):
        
        genre_scores = {genre: 0 for genre in GENRE_MAP.keys()}
        
        try:
            track = network.get_track(artist_name, track_name)
            top_tags = track.get_top_tags(limit=top_n_tags)
            
            if not top_tags:
                artist = network.get_artist(artist_name)
                artist_tags = artist.get_top_tags(limit=5)
                for tag_info in artist_tags:
                    tag_name = tag_info.item.get_name().lower() 
                    tag_weight = int(tag_info.weight)
                    
                    for macro_genre, sub_genres in GENRE_MAP.items():
                        if tag_name in sub_genres:
                            genre_scores[macro_genre] += tag_weight
                            
            else:
                for tag_info in top_tags:
                    tag_name = tag_info.item.get_name().lower() 
                    tag_weight = int(tag_info.weight)
                    
                    for macro_genre, sub_genres in GENRE_MAP.items():
                        if tag_name in sub_genres:
                            genre_scores[macro_genre] += tag_weight
            
            if max(genre_scores.values()) == 0:
                return 0
            
            final_genre = max(genre_scores, key=genre_scores.get)
            return final_genre

        except Exception as e:
            return 0
        
    # backoff 함수
    def request_with_exponential_backoff(artist_name, track_name, network, max_retries=5):
        
        INITIAL_DELAY = 1
        MAX_DELAY = 60
        
        for attempt in range(max_retries):
            try:
                genre = classify_genre(track_name, artist_name, network)
                return genre

            except pylast.WSError as e:
                
                error_message = str(e)
                
                print(f"API 오류 발생: {error_message}")
                
                if attempt < max_retries - 1:
                    delay_time = min(INITIAL_DELAY * (2 ** attempt) + random.random(), MAX_DELAY)
                    
                    print(f"    {delay_time:.2f}초 후 재시도합니다...")
                    time.sleep(delay_time)
                else:
                    print("최대 재시도 횟수 초과. 작업을 중단합니다.")
                    return []
        return []

    find_data = {
        'title' : [],
        'genre' : [],
        'url' : [],
        'channel_name' : []
    }

    not_find_data = {
        'title' : [],
        'artist' : [],
        'genre' : [],
        'url' : [],
        'channel_name' : []
    }

    # 장르 데이터 추출
    for i in range(len(artist_data)):
        genre_data = request_with_exponential_backoff(artist_data[i], track_data[i], network)
        if genre_data != 0:
            find_data['genre'].append(genre_data)
            find_data['title'].append(track_data[i])
            find_data['url'].append(url_data[i])
            find_data['channel_name'].append(artist_data[i])
            print(f"노래 데이터 찾는 중 - 1 : {((i+1)/len(artist_data))*100}%")
        elif "cover" in track_data[i].lower() or "해석" in track_data[i].lower() or "가사" in track_data[i].lower() or "자막" in track_data[i].lower():
            print(f"노래 데이터 찾는 중 - 1 : {((i+1)/len(artist_data))*100}%")
        else:
            not_find_data['genre'].append(genre_data)
            not_find_data['artist'].append(artist_data[i])
            not_find_data['title'].append(track_data[i])
            not_find_data['url'].append(url_data[i])
            not_find_data['channel_name'].append(artist_data[i])
            print(f"노래 데이터 찾는 중 - 1 : {((i+1)/len(artist_data))*100}%")

    # 데이터 평탄화를 위한 패턴 지정
    pattern_1 = r'\s*\(.*?\)' # ()
    pattern_2 = r'\s*\[.*?\]' # []
    pattern_3 = r'\s*\【.*?\】' # 【】
    pattern_4 = r'\s*\「.*?\」' # 「」 
    pattern_5 = r'\s*\（.*?\）' #（）
    pattern_6 = r'\s*\{.*?\}' # {}
    pattern_7 = r'\s*\『.*?\』' # 『』
    pattern_8 = r'[^\w\s]'
    pattern_9 = r'\s(remix|acoustic|live|cover)\s*.*?$'
    pattern_10 = r'\sft\.?.*?$|\sfeat\.?.*?$'
    
    # 데이터 평탄화
    for i in range(len(not_find_data['artist'])):
        not_find_data['title'][i] = re.sub(pattern_1, "", not_find_data['title'][i])
        not_find_data['title'][i] = re.sub(pattern_2, "", not_find_data['title'][i])
        not_find_data['title'][i] = re.sub(pattern_3, "", not_find_data['title'][i])
        not_find_data['title'][i] = re.sub(pattern_4, "", not_find_data['title'][i])
        not_find_data['title'][i] = re.sub(pattern_5, "", not_find_data['title'][i])
        not_find_data['title'][i] = re.sub(pattern_6, "", not_find_data['title'][i])
        not_find_data['title'][i] = re.sub(pattern_7, "", not_find_data['title'][i])
        not_find_data['title'][i] = re.sub(pattern_8, "", not_find_data['title'][i])
        not_find_data['title'][i] = re.sub(pattern_9, "", not_find_data['title'][i])
        not_find_data['title'][i] = re.sub(pattern_10, "", not_find_data['title'][i])
        not_find_data['title'][i] = not_find_data['title'][i].lower().replace("mv", "")
        not_find_data['title'][i] = not_find_data['title'][i].lower().replace("m/v", "")
        not_find_data['title'][i] = not_find_data['title'][i].lower().replace("official music video", "")
        not_find_data['title'][i] = not_find_data['title'][i].lower().replace("music video", "")

        not_find_data["artist"][i] = not_find_data["artist"][i].lower().replace("official", "")
        not_find_data["artist"][i] = not_find_data["artist"][i].lower().replace("musuc", "")
        not_find_data["artist"][i] = not_find_data["artist"][i].lower().replace("youtube", "")
        not_find_data["artist"][i] = not_find_data["artist"][i].lower().replace("channel", "")
        not_find_data["artist"][i] = not_find_data["artist"][i].lower().replace("- topic", "")
        not_find_data["artist"][i] = re.sub(pattern_8, "", not_find_data["artist"][i])
        not_find_data["artist"][i] = not_find_data["artist"][i].split(" ")

    final_data = {
        'title' : [],
        'genre' : [],
        'url' : [],
        'channel_name' : []
    }

    two_genre_data = {
        'title' : [],
        'genre' : [],
        'url' : [],
        'channel_name' : []
    }

    # 장르 데이터 추출
    for i in range(len(not_find_data['title'])):
        genre = []
        artist = []
        if type(not_find_data['artist'][i]) == list:
            for j in range(len(not_find_data['artist'][i])):
                genre.append(request_with_exponential_backoff(not_find_data["artist"][i][j], not_find_data['title'][i], network))
            final_data['genre'].append(genre)
            final_data['title'].append(not_find_data['title'][i])
            final_data['url'].append(not_find_data['url'][i])
            final_data['channel_name'].append(not_find_data['channel_name'][i])
            print(f"노래 데이터 찾는 중 - 2 : {((i+1)/len(not_find_data['artist']))*100}%")
        else:
            final_data['genre'].append(request_with_exponential_backoff(not_find_data["artist"][i], not_find_data['title'][i], network))
            final_data['title'].append(not_find_data['title'][i])
            final_data['url'].append(not_find_data['url'][i])
            final_data['channel_name'].append(not_find_data['channel_name'][i])
            print(f"노래 데이터 찾는 중 - 2 : {((i+1)/len(not_find_data['artist']))*100}%")

    # 공백값 및 이상값 제거
    for i in range(len(final_data['genre'])):
        for j in range(len(final_data['genre'][i])):
            try:
                if 1 in final_data['genre'][i]: 
                    final_data['genre'][i].remove(1)
                if 0 in final_data['genre'][i]:
                    final_data['genre'][i].remove(0)
            except Exception as e:
                print(e)
        for k in range(len(final_data['genre'][i]) - 1, 0, -1):
            if final_data['genre'][i][k] == final_data['genre'][i][k-1]:
                final_data['genre'][i] = final_data['genre'][i][k]
        if type(final_data['genre'][i]) == list:
            if len(final_data['genre'][i]) > 1:
                for l in range(len(final_data['genre'][i]) - 1, 0, -1):
                    two_genre_data['genre'].append(final_data['genre'][i][l])
                    two_genre_data['title'].append(final_data['title'][i])
                    two_genre_data['url'].append(final_data['url'][i])
                    two_genre_data['channel_name'].append(final_data['channel_name'][i])
            elif len(final_data['genre'][i]) == 1:
                two_genre_data['genre'].append(final_data['genre'][i][0])
                two_genre_data['title'].append(final_data['title'][i])
                two_genre_data['url'].append(final_data['url'][i])
                two_genre_data['channel_name'].append(final_data['channel_name'][i])
        

    # 데이터 병합
    final_data = pd.DataFrame(final_data)
    find_data = pd.DataFrame(find_data)
    two_genre_data = pd.DataFrame(two_genre_data)
    final_df = pd.concat([final_data, find_data, two_genre_data], axis=0)

    final_df = final_df[final_df['genre'].apply(type) != list]
    final_df = final_df.reset_index(drop=True)

    # 사용자 활동기록 데이터 전처리
    PLAYLIST_CSV = playlist_csv
    LIKE_VIDEO_CSV = like_video_csv
    SUBSCRIBED_CSV = subscribed_csv
    COMMENT_CSV = comment_csv

    playlist_data = pd.read_csv(PLAYLIST_CSV)
    like_video_data = pd.read_csv(LIKE_VIDEO_CSV)
    subscribed_data = pd.read_csv(SUBSCRIBED_CSV)
    comment_data = pd.read_csv(COMMENT_CSV)

    fianl_data_url = final_df['url'].to_list()
    playlist_data_list = playlist_data["동영상 ID"].to_list()
    like_video_data_list = like_video_data["동영상 ID"].to_list()
    subscribed_data_list = subscribed_data["채널 제목"].to_list()
    comment_video_list = comment_data["동영상 ID"].to_list()
    comment_data_dict = {}

    df_len = len(fianl_data_url)

    activitie_data = {'Is_Liked' : [0 for i in range(df_len)],
                    'Is_Subscribed' : [0 for i in range(df_len)],
                    'Comments_Count' : [0 for i in range(df_len)],
                    'Is_Added_To_Playlist' : [0 for i in range(df_len)]}

    for i in range(len(comment_video_list)):
        if comment_video_list[i] in comment_data_dict.keys():
            comment_data_dict[comment_video_list[i]] += 1
        else:
            comment_data_dict[comment_video_list[i]] = 1

    for i in range(df_len):
        final_df_url = fianl_data_url[i].replace("https://music.youtube.com/watch?v=", "")
        if final_df_url in playlist_data_list:
            activitie_data['Is_Added_To_Playlist'][i] = 1
        if final_df_url in like_video_data_list:
            activitie_data['Is_Liked'][i] = 1
        if final_df_url in subscribed_data_list:
            activitie_data['Is_Subscribed'][i] = 1
        if final_df_url in comment_data_dict.keys():
            activitie_data['Comments_Count'][i] = comment_data_dict[final_df_url]

    activitie_df = pd.DataFrame(activitie_data)
    final_final_df = pd.concat([final_df, activitie_df], axis=1)
    final_final_df = final_final_df.drop(["title", "url", "channel_name"], axis=1)

    final_final_df.to_csv('user_info/user_activities.csv', index=False, encoding='utf-8')

    # 장르별 선호도 점수 계산
    ALL_GENRES = ['Pop', 'Hiphop', 'Rock', 'Classic', 'EDM', 'Ballad', 'Jazz']

    MAX_COMMENTS_COUNT = final_final_df['Comments_Count'].max()

    if MAX_COMMENTS_COUNT == 0:
        MAX_COMMENTS_COUNT = 1

    genre_score = {genre: [0, 0, 0, 0, 0] for i, genre in enumerate(ALL_GENRES)}

    for i, genre in enumerate(ALL_GENRES):
        preferred_genres = final_final_df[final_final_df['genre'] == genre]
        len_genres = len(preferred_genres)
        if len_genres == 0:
            genre_count = [0, 0, 0, 0, 0]
        else:
            genre_count = [len_genres, 
                        preferred_genres['Is_Liked'].sum()/len_genres, 
                        preferred_genres['Is_Subscribed'].sum()/len_genres, 
                        preferred_genres['Comments_Count'].sum()/len_genres,
                        preferred_genres['Is_Added_To_Playlist'].sum()/len_genres]
        genre_score[genre] = genre_count

    genres_df = pd.DataFrame(genre_score).T
    score = {genre: 0 for i, genre in enumerate(ALL_GENRES)}

    for j, genre in enumerate(ALL_GENRES):
        normalized_comments = genres_df.loc[genre, 3] / MAX_COMMENTS_COUNT
        score[genre] = (((genres_df.loc[genre, 1] * 0.3)
                        + (genres_df.loc[genre, 2] * 0.2)
                        + (normalized_comments * 0.1)
                        + (genres_df.loc[genre, 4] * 0.4)))
        
    return score