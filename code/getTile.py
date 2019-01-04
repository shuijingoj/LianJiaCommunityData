# Longitude 经度
# Latitude   纬度

import math
from math import floor, pi, log, tan, atan, exp
from threading import Thread, Lock
import urllib.request as ur
import PIL.Image as pil
import io

MAP_URLS = {
    "google": "http://mt2.google.cn/vt/lyrs={style}&hl=zh-CN&gl=CN&src=app&x={x}&y={y}&z={z}",
    "amap": "http://wprd02.is.autonavi.com/appmaptile?style={style}&x={x}&y={y}&z={z}",
    "tencent_s": "http://p3.map.gtimg.com/sateTiles/{z}/{fx}/{fy}/{x}_{y}.jpg",
    "tencent_m": "http://rt0.map.gtimg.com/tile?z={z}&x={x}&y={y}&styleid=3"  }

COUNT=0
mutex=Lock()

#-----------------GCJ02到WGS84的纠偏与互转---------------------------
def transformLat(x, y):
    ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * math.pi) + 320 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
    return ret

def transformLon(x, y):
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
    return ret


def delta(lat, lon):
    ''' 
    Krasovsky 1940
    //
    // a = 6378245.0, 1/f = 298.3
    // b = a * (1 - f)
    // ee = (a^2 - b^2) / a^2;
    '''
    a = 6378245.0   #  a: 卫星椭球坐标投影到平面地图坐标系的投影因子。
    ee = 0.00669342162296594323   #  ee: 椭球的偏心率。
    dLat = transformLat(lon - 105.0, lat - 35.0)
    dLon = transformLon(lon - 105.0, lat - 35.0)
    radLat = lat / 180.0 * math.pi
    magic = math.sin(radLat)
    magic = 1 - ee * magic * magic
    sqrtMagic = math.sqrt(magic)
    dLat = (dLat * 180.0) / ((a * (1 - ee)) / (magic * sqrtMagic) * math.pi)
    dLon = (dLon * 180.0) / (a / sqrtMagic * math.cos(radLat) * math.pi)
    return {'lat': dLat, 'lon': dLon}

def outOfChina(lat, lon):
    if (lon < 72.004 or lon > 137.8347):
        return True
    if (lat < 0.8293 or lat > 55.8271):
        return True
    return False

def gcj_to_wgs(gcjLon,gcjLat):
    if outOfChina(gcjLat, gcjLon):
        return (gcjLon, gcjLat)
    d = delta(gcjLat, gcjLon)
    return (gcjLon - d["lon"],gcjLat - d["lat"])

def wgs_to_gcj(wgsLon,wgsLat):
    if outOfChina(wgsLat, wgsLon):
        return wgsLon, wgsLat
    d = delta(wgsLat, wgsLon);
    return wgsLon + d["lon"], wgsLat + d["lat"]

#--------------------------------------------------------------
# * 火星坐标系 (GCJ-02) 与百度坐标系 (BD-09) 的转换算法 * * 将 BD-09 坐标转换成GCJ-02 坐标 *

# 百度坐标 (BD-09) 转换为高德坐标 (GCJ-02)
# lon 经度，lat 纬度
def bd_To_Gcj(bd_lon, bd_lat):
    x = bd_lon - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * pi)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * pi)
    gg_lon = z * math.cos(theta)
    gg_lat = z * math.sin(theta)
    return gg_lon, gg_lat

#---------------------------------------------------------
'''
东经为正，西经为负。北纬为正，南纬为负
j经度 w纬度 z缩放比例[0-22] ,对于卫星图并不能取到最大，测试值是20最大，再大会返回404.
山区卫星图可取的z更小，不同地图来源设置不同。
'''
# 根据WGS-84 的经纬度获取谷歌地图中的瓦片坐标
def wgs84_to_tile(j, w, z):
    '''
    Get google-style tile cooridinate from geographical coordinate
    j : Longittude
    w : Latitude
    z : zoom
    '''
    isnum = lambda x: isinstance(x, int) or isinstance(x, float)
    if not(isnum(j) and isnum(w)):
        raise TypeError("j and w must be int or float!")

    if not isinstance(z, int) or z < 0 or z > 22:
        raise TypeError("z must be int and between 0 to 22.")

    if j < 0:
        j = 180 + j
    else:
        j += 180
    j /= 360  # make j to (0,1)

    w = 85.0511287798 if w > 85.0511287798 else w
    w = -85.0511287798 if w < -85.0511287798 else w
    w = log(tan((90 + w) * pi / 360)) / (pi / 180)
    w /= 180  # make w to (-1,1)
    w = 1 - (w + 1) / 2  # make w to (0,1) and left top is 0-point

    num = 2**z
    x = floor(j * num)
    y = floor(w * num)
    return x, y

class Downloader(Thread):
    # multiple threads downloader
    def __init__(self,index,count,urls,datas,update):
        # index 表示第几个线程，count 表示线程的总数，urls 代表需要下载url列表，datas代表要返回的数据列表。
        # update 表示每下载一个成功就进行的回调函数。
        super().__init__()
        self.urls=urls
        self.datas=datas
        self.index=index
        self.count=count
        self.update=update

    def download(self,url):
        HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.76 Safari/537.36'}
        header = ur.Request(url,headers=HEADERS)
        err=0
        while(err<3):
            try:
                data = ur.urlopen(header).read()
            except:
                err+=1
            else:
                return data
        # raise Exception("Bad network link.")
        print("连接错误，无法下载图片")

    def run(self):
        for i,url in enumerate(self.urls):
            if i%self.count != self.index:
                continue
            self.datas[i]=self.download(url)
            if mutex.acquire():
                self.update()
                mutex.release()

def geturl(source, x, y, z, style):
    '''
    Get the picture's url for download.
    style:
        m for map
        s for satellite
    source:
        google or amap or tencent
    x y:
        google-style tile coordinate system
    z:
        zoom 
    '''
    if source == 'google':
        furl = MAP_URLS["google"].format(x=x, y=y, z=z, style=style)
    elif source == 'amap':
        # for amap 6 is satellite and 7 is map.
        style = 6 if style == 'satellite' else 7
        furl = MAP_URLS["amap"].format(x=x, y=y, z=z, style=style)
    elif source == 'tencent':
        y = 2**z - 1 - y
        if style == 's':
            furl = MAP_URLS["tencent_s"].format(
                x=x, y=y, z=z, fx=floor(x / 16), fy=floor(y / 16))
        else:
            furl = MAP_URLS["tencent_m"].format(x=x, y=y, z=z)
    else:
        # raise Exception("Unknown Map Source ! ")
        print("未知地图源")

    return furl




def downpics(urls,multi=10):

    def makeupdate(s):
        def up():
            global COUNT
            COUNT+=1
            # print("\b"*30,end='')
            # print("DownLoading ... [{0}/{1}]".format(COUNT,s),end='')
        return up

    url_len=len(urls)
    datas=[None] * url_len
    if multi <1 or multi >20 or not isinstance(multi,int):
        # raise Exception("multi of Downloader shuold be int and between 1 to 20.")
        # print("multi of Downloader shuold be int and between 1 to 20.")
        multi = 8
    tasks=[Downloader(i,multi,urls,datas,makeupdate(url_len)) for i in range(multi)]
    for i in tasks:
        i.start()
    for i in tasks:
        i.join()

    return datas


def getpic(x1, y1, z, source, outfile, style='satellite'):
    '''
    依次输入图片中心的经度、纬度，缩放级别，地图源，输出文件，影像类型（默认为卫星图）
    获取区域内的瓦片并自动拼合图像。返回四个角的瓦片坐标
    '''
    pos1x, pos1y = wgs84_to_tile(x1, y1, z)
    print(pos1x, pos1y)
    lenx = leny = 4
    # print("Total number：{x} X {y}".format(x=lenx, y=leny))

    urls = [geturl(source, i, j, z, style) for j in range(pos1y - leny//2, pos1y + leny//2) for i in range(pos1x - lenx//2, pos1x + lenx//2)]

    datas = downpics(urls)

    # print("{0},{1}瓦片下载完成，等待合并".format(x1,y1))
    outpic = pil.new('RGB', (lenx * 256, leny * 256))
    for i, data in enumerate(datas):
        picio = io.BytesIO(data)
        small_pic = pil.open(picio)

        y, x = i // lenx, i % lenx
        outpic.paste(small_pic, (x * 256, y * 256))
    print("{0},{1}图片下载完成".format(x1, y1))
    # print('Pics Merged！ Exporting......')
    outpic.save(outfile)
    # print('Exported to file！')
    # return {"LT":(pos1x,pos1y),"RT":(pos2x,pos1y),"LB":(pos1x,pos2y),"RB":(pos2x,pos2y),"z":z}


if __name__ == '__main__':
    satellite_path = "E:/小区卫星图/"
    outfile =  satellite_path + "sample_map.png" 
    # sample_position = [114.134602,22.604004]
    sample_position = [113.898708,22.490612]
    # print(type(sample_position[0]))
    # 114.134602,22.604004  
    sample_position = bd_To_Gcj(*sample_position)
    # print(sample_position)
    # for amap 6 is satellite and 7 is map.
    getpic(*sample_position, 17, source='amap', style='satellite', outfile=outfile)