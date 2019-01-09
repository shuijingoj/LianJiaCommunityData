import os
import pandas as pd
import threading
import time
 
def urllib_download(save_path, img_url):
    from urllib.request import urlretrieve
    urlretrieve(img_url, save_path)     
 
def request_download(save_path, img_url):
    import requests
    r = requests.get(img_url)
    with open(save_path, 'wb') as f:
        f.write(r.content)                      
 
def chunk_download(save_path, img_url):
    import requests
    r = requests.get(img_url, stream=True)    
    with open(save_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=32):
            f.write(chunk)
 
def getCommunityImg(url_file, save_path):
    df_img = pd.read_csv(url_file, sep=';', error_bad_lines=False, warn_bad_lines=False)
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    
    start_row = len(os.listdir(save_path))

    img_id = 1                     # 图片命名为“小区ID+该小区的图片编号”
    if start_row == 0:             # 从头开始爬的情况
        last_community = df_img['community_id'][0]
    else:                          # 中断后继续上次进度的情况
        last_community = df_img['community_id'][start_row-1]
        if df_img['community_id'][start_row] == last_community:     # 上次中断时当前小区仍有图片未爬完
            while(os.path.exists(save_path+str(df_img['community_id'][start_row])+'_%d.jpg'%img_id)):   # 找到中断时的图片编号，接着继续爬
                img_id += 1   
    
    for i in range(start_row, len(df_img)):
        recent_community = df_img['community_id'][i]
        if recent_community != last_community:           # 当前小区与上一条记录的小区不一致，重新开始编号
            img_id = 1
        try:
            urllib_download(save_path+str(df_img['community_id'][i])+'_%d.jpg'%img_id, df_img['img_url'][i])
            img_id += 1
            last_community = recent_community
            print(time.asctime(time.localtime(time.time())), url_file, '%d/%d'%(len(os.listdir(save_path)), len(df_img)))
        except:
            print(recent_community, ' has image downloading fail.')

if __name__ == '__main__':
    df = pd.read_csv('../70cities.csv', header=None)     # 读取70个大中城市列表
    cityList = df[df[2]=='y'][1]                         # 筛选出链家上带小区信息的城市

    # 爬单城市
    # city = 'sh'
    # getCommunityImg('../community_data/%s/img.csv'%city, 'E:/小区景观图/%s/'%city)

    # 多线程爬取全部城市小区景观图
    # for city in cityList:                                
    #     t = threading.Thread(target=getCommunityImg, args=('../community_data/%s/img.csv'%city, 'E:/小区景观图/%s/'%city))
    #     t.start()

    # 输出爬取图片的数量情况
    for city in cityList:
        location_file = '../community_data/%s/img.csv'%city
        df_info = pd.read_csv(location_file, sep=';', error_bad_lines=False, warn_bad_lines=False)
        print(city,'%d/%d'%(len(os.listdir('E:/小区景观图/%s/'%city)), len(df_info)))
