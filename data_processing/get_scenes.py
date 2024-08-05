import re 
from datetime import timedelta
import pandas as pd
import os
from multiprocessing import Pool


def preprocess_subtitles(file_path):
    subs_name = os.listdir(file_path)
    print(subs_name)
    try:
        subs_name = [sub for sub in subs_name if (os.path.splitext(sub)[1] == '.csv' and 'scenes' not in sub) ][0]
    
        subs_file = os.path.join(file_path, subs_name)
        
        df = pd.read_csv(subs_file)
        df['start_time'] = pd.to_timedelta(df['start_time'])
        df['end_time'] = pd.to_timedelta(df['end_time'])
    except Exception as e:
        print(f'file reading error {e} in {subs_name}')
        return False

    scenes = []
    current_scene = []
    last_end_time = timedelta()
    try:
        for _,subtitle in df.iterrows():
            if subtitle['start_time'] - last_end_time > timedelta(minutes=0.5):
                if current_scene:
                    scenes.append(current_scene)
                    current_scene = []
            current_scene.append(subtitle['text'])
            last_end_time = subtitle['end_time']

        if current_scene:
            scenes.append(current_scene)

        scene_texts = []
        for scene in scenes:
            scene = [str(dailog) for dailog in scene]
            scene = ''.join(scene)
            scene_texts.append(scene)
        scene_texts = pd.DataFrame(scene_texts,columns=['scene'])
        scene_texts.to_csv(os.path.join(file_path,'scenes.csv'))
    except Exception as e:
        print(f'exception {e} in {subs_file} at {scene}')
        return False
    return True
if __name__ == '__main__':
    dir = 'subtitles_test'
    print('hi')
    subs_folds = os.listdir(dir)
    if '.DS_Store' in subs_folds:
        subs_folds.remove('.DS_Store')
    subs_folds = [os.path.join(dir,subs_fold) for subs_fold in subs_folds]
    with Pool(8) as pool:
        res = pool.map(preprocess_subtitles,subs_folds)
    failed = [suc for suc in res if not suc ]
    print(len(failed))
    
    
