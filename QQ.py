API_ADDR_LINK_QQ:str="https://api.vkeys.cn/v2/music/tencent/geturl"
API_ADDR_LYRIC_QQ:str="https://api.vkeys.cn/v2/music/tencent/lyric"
import requests
import time
from typing import Any

SETTINGS_QQ:dict[str,bool]={
    "Pack":False,
    "WriteMeta":True
}

LEVELS_QQ:dict[str,Any]={
    "试听":1, #?我为什么要加这个?
    "48kbps":2,
    "96kbps":3,
    "192kbps":4,
    "96kbps(OGG)":5,
    "128kbps":6,
    "128kbps(OGG)":7,
    "标准(320kbps)":8,
    "不知道":9,#------以上全部是有损------#
    "无损(SQ)":10,
    "Hi-Res":11,#不知道腾讯有没有,反正我是看不到的
    "杜比全景声":12,#幽默,恐怕你没见过256kbps还m4a的杜比吧?
    "臻品全景声":13,#与网易一致,但是腾讯更黑
    "臻品母带2.0":14,#?什么玩意这是?
    "AI伴奏消音(试验)":15,#...懒得吐槽了自己看吧
    "AI人声消音(试验)":16,#...懒得吐槽了自己看吧x2
    "不知道x2":17,
}

from Core import (SongInfo as AbsSongInfo,FunctionType)

def GetSongInfo(ID:int|str,Level:int)->dict[str,Any]:
    LyricResp:dict[str,Any]=requests.get(
        url=API_ADDR_LYRIC_QQ,
        params={
            "mid":ID
        }
    ).json()
    LinkResp:dict[str,Any]=requests.get(
        url=API_ADDR_LINK_QQ,
        params={
            "mid":ID,
            "quality":Level
        }
    ).json()

    ReturnCode:dict[str,int]={
        "lyric":LyricResp["code"],
        "info":LinkResp["code"],
        "link":LinkResp["code"]
    }
    print(LinkResp)
    Lyric:str=LyricResp["data"]["lrc"]
    TranslatedLyric:str=LyricResp["data"]["trans"]
    Name:str=LinkResp["data"]["song"]
    Artists:str="/".join([Item["name"] for Item in LinkResp["data"]["singer_list"]])
    AlbumName:str=LinkResp["data"]["album"]
    PictureURL:str=LinkResp["data"]["cover"]
    Link:str=LinkResp["data"]["url"]
    return {
        "data":{
            "album":AlbumName,
            "artists":Artists,
            "picUrl":PictureURL,
            "name":Name,
            "audioUrl":Link,
            "tlyric":TranslatedLyric,
            "lyric":Lyric
        },
        "codes":ReturnCode,
        "time":time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
    }

class SongInfo(AbsSongInfo):
    @property
    def Func(self)->FunctionType:
        return GetSongInfo


from Template import (
    Template as AbsTemplate,
    DownloaderPage as AbsDownliaderPage
)

class Template(AbsTemplate):
    @property
    def SongInfoType(self)->type:
        return SongInfo

    @property
    def Settings(self)->dict[str,Any]:
        return SETTINGS_QQ

class DownloaderPage(AbsDownliaderPage):
    @property
    def TemplateType(self)->type:
        return Template
    
    @property
    def Levels(self)->dict[str,Any]:
        return LEVELS_QQ