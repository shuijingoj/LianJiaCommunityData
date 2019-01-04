# 链家房产数据集

+ 70cities.csv  
   全国70个大中城市列表。其中第一列为城市；第二列为该城市在链家的英语缩写，0表示该城市在链家无分站；第三列标记该城市在链家是否有小区数据。

+ /community_data/(city)  
   保存从链家各城市分站中爬取的小区信息:
   1. baseinfo.csv  
      保存基本信息
   2. img.csv  
      保存各小区的景观图像url

+ /code  
   1. getCommunityImg.py  
      从链家上爬取各小区的景观图
   2. getSateliteImg.py  
      从高德地图上爬取各小区的卫星俯瞰图
   3. getTile.py  
      卫星俯瞰图像爬虫的基础代码