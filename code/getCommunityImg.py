import os
import pandas as pd
import threading
 
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
    
    last_community = df_img['community_id'][0]         
    img_id = 1                                           # 图片命名为“小区ID+该小区的图片编号”
    for i in range(0, len(df_img)):
        recent_community = df_img['community_id'][i]
        if recent_community != last_community:           # 当前小区与上一条记录的小区不一致，重新开始编号
            img_id = 1
        urllib_download(save_path+str(df_img['community_id'][i])+'_%d.jpg'%img_id, df_img['img_url'][i])
        img_id += 1
        last_community = recent_community

if __name__ == '__main__':
    df = pd.read_csv('../70cities.csv', header=None)     # 读取70个大中城市列表
    cityList = df[df[2]=='y'][1]                         # 筛选出链家上带小区信息的城市
    city = 'sh'

    for city in cityList:                                # 多线程爬取小区景观图
        t = threading.Thread(target=getCommunityImg, args=('../community_data/%s/img.csv'%city, 'E:/小区景观图/%s/'%city))
        t.start()


