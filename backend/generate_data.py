import pandas as pd
import random

USER_COUNT = 1000 
ACTIVITY_PER_USER = 60
GENRES = ['Pop', 'Hiphop', 'Rock', 'Classic', 'EDM', 'Ballad', 'Jazz']

MBTI_AXIS_PREFS = {
    'Pop':      {'E': 90, 'S': 80, 'T': 50, 'J': 70}, 
    'Hiphop':   {'E': 85, 'S': 75, 'T': 65, 'J': 55}, 
    'Rock':     {'E': 40, 'S': 60, 'T': 80, 'J': 45}, 
    'Classic':  {'E': 30, 'S': 40, 'T': 70, 'J': 85}, 
    'EDM':      {'E': 95, 'S': 90, 'T': 30, 'J': 60}, 
    'Ballad':   {'E': 50, 'S': 70, 'T': 20, 'J': 75}, 
    'Jazz':     {'E': 60, 'S': 50, 'T': 85, 'J': 50}, 
}

user_data = []
for i in range(1, USER_COUNT + 1):
    user_id = i
    gender = random.choice([0, 1]) 
    age_group = random.choice([10, 20, 30, 40, 50, 60]) 
    
    E_I = random.randint(20, 90)
    S_N = random.randint(20, 90)
    T_F = random.randint(20, 90)
    J_P = random.randint(20, 90)
    
    scores = {}
    for genre, prefs in MBTI_AXIS_PREFS.items():
        score_diff = (
            abs(E_I - prefs['E']) * 0.25 + 
            abs(S_N - prefs['S']) * 0.25 + 
            abs(T_F - prefs['T']) * 0.25 + 
            abs(J_P - prefs['J']) * 0.25 
        )
        scores[genre] = 100 - score_diff
    
    mbti_type = (
        ('E' if E_I >= 50 else 'I') +
        ('S' if S_N >= 50 else 'N') +
        ('T' if T_F >= 50 else 'F') +
        ('J' if J_P >= 50 else 'P')
    )
    
    sorted_genres = sorted(scores, key=scores.get, reverse=True)
    num_preferred = random.randint(1, 3)
    preferred_genres_list = sorted_genres[:num_preferred]
    
    preferred_genres_str = ",".join(preferred_genres_list) 
    
    user_data.append([
        user_id, gender, age_group, preferred_genres_str,
        mbti_type, E_I, S_N, T_F, J_P 
    ])

df_profile = pd.DataFrame(user_data, columns=[
    'User_ID', 'Gender', 'Age_Group', 'Preferred_Genres', 
    'MBTI_Type', 'E_I_Score', 'S_N_Score', 'T_F_Score', 'J_P_Score'
]).astype({'User_ID': 'int64', 'Gender': 'int64', 'Age_Group': 'int64', 
           'E_I_Score': 'int64', 'S_N_Score': 'int64', 'T_F_Score': 'int64', 'J_P_Score': 'int64'}) 

TRACK_POOL_SIZE = 1000
track_pool = []
tracks_per_genre = TRACK_POOL_SIZE // len(GENRES)
remainder = TRACK_POOL_SIZE % len(GENRES)

track_id_counter = 1
for genre in GENRES:
    num_tracks = tracks_per_genre + (1 if remainder > 0 else 0)
    for _ in range(num_tracks):
        track_pool.append({'Track_ID': f"Track_{track_id_counter}", 'Genre': genre})
        track_id_counter += 1
    if remainder > 0:
        remainder -= 1

df_track_pool = pd.DataFrame(track_pool)

activity_data = []
activity_id = 1
for user_id in df_profile['User_ID']:
    
    preferred_genres_str = df_profile[df_profile['User_ID'] == user_id]['Preferred_Genres'].iloc[0]
    preferred_genres = preferred_genres_str.split(',')
    
    if not preferred_genres or preferred_genres == ['']:
        activities = random.choices(GENRES, k=ACTIVITY_PER_USER)
        primary_genre = None
    else:
        primary_genre = preferred_genres[0]
        
        num_preferred_activities = int(ACTIVITY_PER_USER * 0.75)
        activities = []
        
        primary_tracks = df_track_pool[df_track_pool['Genre'] == primary_genre]['Track_ID'].tolist()
        activities.extend(random.choices(primary_tracks, k=int(num_preferred_activities * 0.5)))
        
        if len(preferred_genres) > 1:
            secondary_genres = preferred_genres[1:]
            secondary_tracks = df_track_pool[df_track_pool['Genre'].isin(secondary_genres)]['Track_ID'].tolist()
            activities.extend(random.choices(secondary_tracks, k=int(num_preferred_activities * 0.5)))
            
        non_preferred_genres = [g for g in GENRES if g not in preferred_genres]
        non_preferred_tracks = df_track_pool[df_track_pool['Genre'].isin(non_preferred_genres)]['Track_ID'].tolist()
        activities.extend(random.choices(non_preferred_tracks, k=ACTIVITY_PER_USER - len(activities)))

    for track_id in activities:
        genre = df_track_pool[df_track_pool['Track_ID'] == track_id]['Genre'].iloc[0]

        def set_activity_metrics(level):
            if level == 'Primary':
                is_liked = random.choices([1, 0], weights=[0.9, 0.1], k=1)[0]
                is_subscribed = random.choices([1, 0], weights=[0.7, 0.3], k=1)[0]
                comments_count = random.randint(1, 5) 
                is_added_to_playlist = random.choices([1, 0], weights=[0.8, 0.2], k=1)[0]
            elif level == 'Secondary':
                is_liked = random.choices([1, 0], weights=[0.5, 0.5], k=1)[0]
                is_subscribed = random.choices([1, 0], weights=[0.4, 0.6], k=1)[0]
                comments_count = random.randint(0, 1) 
                is_added_to_playlist = random.choices([1, 0], weights=[0.5, 0.5], k=1)[0]
            else:
                is_liked = random.choices([1, 0], weights=[0.1, 0.9], k=1)[0]
                is_subscribed = 0 
                comments_count = 0
                is_added_to_playlist = 0
            
            return is_liked, is_subscribed, comments_count, is_added_to_playlist

        if primary_genre and genre == primary_genre:
            level = 'Primary'
        elif primary_genre and genre in preferred_genres[1:]:
            level = 'Secondary'
        else:
            level = 'Non-Preferred'
            
        is_liked, is_subscribed, comments_count, is_added_to_playlist = set_activity_metrics(level)

        activity_data.append([
            activity_id, user_id, track_id, genre, 
            is_liked, is_subscribed, comments_count, is_added_to_playlist 
        ])
        activity_id += 1

df_activity = pd.DataFrame(activity_data, columns=[
    'Activity_ID', 'User_ID', 'Track_ID', 'Genre', 
    'Is_Liked', 'Is_Subscribed', 'Comments_Count', 'Is_Added_To_Playlist'
])

df_profile.to_csv('data/user_profiles.csv', index=False, encoding='utf-8')
df_activity.to_csv('data/user_activities.csv', index=False, encoding='utf-8')