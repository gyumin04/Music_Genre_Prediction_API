import tensorflow
import keras
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from keras.regularizers import l2
from sklearn.utils.class_weight import compute_class_weight
import numpy as np

input_profiles_file = 'data/user_profiles.csv'
input_activities_file = 'data/user_activities.csv'

profiles_data = pd.read_csv(input_profiles_file) 
activities_data = pd.read_csv(input_activities_file) 

profiles_data = profiles_data[['User_ID', 'Gender', 'Age_Group', 'Preferred_Genres', 'MBTI_Type', 'E_I_Score', 'S_N_Score', 'T_F_Score', 'J_P_Score']]
activities_data = activities_data[['Activity_ID', 'User_ID', 'Track_ID', 'Genre', 'Is_Liked', 'Is_Subscribed', 'Comments_Count', 'Is_Added_To_Playlist']]


# 활동내역 기반 장르별 점수 계산
activities_data = activities_data.drop(['Track_ID', 'Activity_ID'], axis=1)


ALL_GENRES = ['Pop', 'Hiphop', 'Rock', 'Classic', 'EDM', 'Ballad', 'Jazz']

user_id = activities_data['User_ID'].drop_duplicates().tolist()
score_df = pd.DataFrame()

MAX_COMMENTS_COUNT = activities_data['Comments_Count'].max()

if MAX_COMMENTS_COUNT == 0:
    MAX_COMMENTS_COUNT = 1

for user_count in user_id:
    # 개수 | 좋아요 비율 | 구독 비율 | 댓글 비율 | 플레이리스트 추가 비율 | 점수
    genre_score = {genre: [0, 0, 0, 0] for i, genre in enumerate(ALL_GENRES)}

    user = activities_data[activities_data['User_ID'] == user_count]

    for j, genre in enumerate(ALL_GENRES):
        preferred_genres = user[user['Genre'] == genre]
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
    score["user_id"] = int(user_count)

    for k, genre in enumerate(ALL_GENRES):
        normalized_comments = genres_df.loc[genre, 3] / MAX_COMMENTS_COUNT
        score[genre] = (((genres_df.loc[genre, 1] * 0.3)
                        + (genres_df.loc[genre, 2] * 0.2)
                        + (normalized_comments * 0.1)
                        + (genres_df.loc[genre, 4] * 0.4)))

    score_series = pd.Series(score)
    score_df = pd.concat([pd.DataFrame(score_series).T, score_df], ignore_index=True)
    
score_df = score_df.sort_values(by='user_id', ascending=True)

# 사용자 프로필 데이터 전처리
# 'User_ID', 'Gender', 'Age_Group', 'Preferred_Genres', 'MBTI_Type', 'E_I_Score', 'S_N_Score', 'T_F_Score', 'J_P_Score'
genres_data = pd.DataFrame(profiles_data['Preferred_Genres'].apply(lambda x: x.split(',')))
profiles_data = profiles_data.drop(['MBTI_Type', 'Preferred_Genres'], axis=1)

ALL_GENRES_set = set(ALL_GENRES)

num_genres = 7
# 'Pop': 0, 'Hiphop': 1, 'Rock': 2, 'Classic': 3, 'EDM': 4, 'Ballad': 5, 'Jazz': 6
genre_to_index = {genre: i for i, genre in enumerate(ALL_GENRES)}

genre_encoded_data = pd.DataFrame(
    0, 
    index=genres_data.index,
    columns=[f'genre_{g}' for g in ALL_GENRES],
    dtype=np.float32
)

for index, genres_list in genres_data['Preferred_Genres'].items():
    for genre in genres_list:
        if genre in ALL_GENRES:
            column_name = f'genre_{genre}'
            genre_encoded_data.loc[index, column_name] = 1.0

final_df = pd.merge(
    profiles_data,
    score_df,
    left_on="User_ID",
    right_on="user_id",
    how='inner'
)
final_df = final_df.drop(columns=['user_id', 'User_ID'])

EPOCHS = 200
RANDOM_SEED = 42
REGULARIZER_VALUE = 0.0001

x_data = final_df
y_data = genre_encoded_data

x_train, x_val, y_train, y_val = train_test_split(
    x_data, y_data, 
    test_size=0.2, 
    random_state=RANDOM_SEED)

scaler = MinMaxScaler()
x_train_scaled = scaler.fit_transform(x_train.values)
x_val_scaled = scaler.transform(x_val.values)


model = keras.Sequential([
    keras.layers.Dense(64, activation="relu", kernel_regularizer=l2(REGULARIZER_VALUE)),
    keras.layers.Dense(48, activation="relu", kernel_regularizer=l2(REGULARIZER_VALUE)),
    keras.layers.Dense(32, activation="relu", kernel_regularizer=l2(REGULARIZER_VALUE)),
    keras.layers.Dense(7, activation="sigmoid")
])

model.compile(optimizer="RMSprop", metrics=["accuracy"],
              loss="binary_crossentropy")

print("************ TRAINING START ************")

early_stop = keras.callbacks.EarlyStopping(monitor='val_loss', patience=10)


history = model.fit(x_train_scaled, y_train, epochs=EPOCHS,
                    validation_data=(x_val_scaled, y_val),
                    callbacks=[early_stop])

keras.saving.save_model(model, 'model/model_Genre_Analyzer.keras')