from getTile import *
import pandas as pd
import os
import threading
import time

def getSateliteImg(location_file, save_path):
    df_info = pd.read_csv(location_file, sep=';', error_bad_lines=False, warn_bad_lines=False)
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    start_row = len(os.listdir(save_path))
    for i in range(start_row, len(df_info)):
        img_name = str(df_info['community_id'][i])+'.jpg'
        transformed_position = bd_To_Gcj(float(df_info['longitude'][i]), float(df_info['latitude'][i]))    
        getpic(*transformed_position, 17, source='amap', style='satellite', outfile=save_path+img_name)
        print(time.asctime(time.localtime(time.time())), location_file, '%d/%d'%(len(os.listdir(save_path)), len(df_info)))
    

if __name__ == '__main__':
    df = pd.read_csv('../70cities.csv', header=None)
    cityList = df[df[2]=='y'][1]    # 获取带有小区信息的城市缩写列表

    # 爬单城市
    # city = 'sh'
    # getSateliteImg('../community_data/%s/baseinfo.csv'%city, 'E:/小区卫星图/%s/'%city)

    # 多线程爬全部城市
    for city in cityList:
        t = threading.Thread(target=getSateliteImg, args=('../community_data/%s/baseinfo.csv'%city, 'E:/小区卫星图/%s/'%city))
        t.start()

    # 输出爬取图片的数量情况
    # for city in cityList:
        # location_file = '../community_data/%s/baseinfo.csv'%city
        # df_info = pd.read_csv(location_file, sep=';', error_bad_lines=False, warn_bad_lines=False)
        # print(city,'%d/%d'%(len(os.listdir('E:/小区卫星图/%s/'%city)), len(df_info)))