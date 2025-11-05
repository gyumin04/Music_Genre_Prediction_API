import pandas as pd
import numpy as np
import random
from sklearn.preprocessing import MultiLabelBinarizer


N_USERS = 1000
ALL_GENRES = ['Pop', 'Hiphop', 'Rock', 'Classic', 'EDM', 'Ballad', 'Jazz']
user_ids = np.arange(1, N_USERS + 1)

total_listen_time_min = np.random.randint(500, 5001, N_USERS)

likes_count = np.random.randint(10, 301, N_USERS)

skip_rate_perc = np.round(np.random.uniform(0.05, 0.80, N_USERS), 2)

access_device = random.choices(['Mobile', 'PC', 'Tablet'], weights=[0.55, 0.35, 0.10], k=N_USERS)

peak_time_access_perc = np.round(np.random.uniform(0.1, 0.9, N_USERS), 2)


def assign_genres(time, skip, peak):
    genres = set()

    if time > 3000 and skip < 0.4:
        genres.add(random.choice(['Pop', 'Ballad']))
        genres.add(random.choice(['Jazz', 'Classic']))
    
    if peak > 0.65:
        genres.add(random.choice(['Ballad', 'Jazz', 'Classic']))

    if skip > 0.6 and time < 1500:
        genres.add(random.choice(['Hiphop', 'EDM', 'Rock']))

    if not genres:
        genres.add(random.choice(ALL_GENRES))
    
    return sorted(list(genres)[:random.randint(1, 3)])

preferred_genres = [
    assign_genres(total_listen_time_min[i], skip_rate_perc[i], peak_time_access_perc[i])
    for i in range(N_USERS)
]

data = pd.DataFrame({
    'user_id': user_ids,
    'total_listen_time_min': total_listen_time_min,
    'likes_count': likes_count,
    'skip_rate_perc': skip_rate_perc,
    'access_device': access_device,
    'peak_time_access_perc': peak_time_access_perc,
    'preferred_genres': preferred_genres
})

output_path = 'data/user_listening_data.csv'
data.to_csv(output_path, index=False)

print(f" 가상 데이터셋 생성 완료! 파일 경로: {output_path}")
print(f" 총 {N_USERS}개 사용자 데이터 저장.")
print("\n--- 데이터 미리보기 ---")
print(data.head())