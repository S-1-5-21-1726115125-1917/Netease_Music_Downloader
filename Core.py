import requests
from typing import Any
from types import FunctionType
import zipfile
from abc import ABC,abstractmethod
from io import BytesIO
import json
import mutagen.flac,mutagen.mp3
from _collections_abc import Iterator
from urllib.parse import urlparse
from pathlib import Path

from Structure import *

class Initnalizer(ABC):
    @abstractmethod
    def Initnalize(self)->None:...

    @property
    @abstractmethod
    def IsInitnalized(self)->bool:...

class StatusWriter(ABC):
    @abstractmethod
    def WriteStatus(self,Status:float)->None:...
    @abstractmethod
    def WriteInfo(self,Info:str)->None:...

class SongInfo(Initnalizer):
    ID:int
    Album:str
    Artist:str
    PictureURL:str
    Title:str
    URL:str
    
    @property
    @abstractmethod
    def Func(self)->FunctionType: ...

    def __init__(self,ID:int|str,WriteMeta=True,Pack=False,Level:str="standard"):
        self.ID:int|str=ID
        self.Album:str=""
        self.Artist:str=""
        self.PictureURL:str=""
        self.Title=""
        self.URL=""
        self.WriteMeta=WriteMeta
        self.Pack=Pack
        self.Level=Level
        self.Lrc:str=""
        self.TranslatedLrc:str=""
        self.Error:bool=False
        self.ErrorMessage:str="成功"
    
    @property
    def Format(self)->str:
        return Path(urlparse(self.URL).path).suffix.lstrip(".")
    
    @Format.setter
    def Format(self,Value:str)->None:
        raise AttributeError("Format属性是只读的")

    @property
    def IsInitnalized(self)->bool:
        return self.URL!=""
    
    @IsInitnalized.setter
    def IsInitnalized(self,Value:bool)->None:
        raise AttributeError("IsInitnalized属性是只读的")

    def __repr__(self)->str:
        return f"SongInfo({self.ID},{self.URL},{self.PictureURL})"
    
    __str__=__repr__

    def Initnalize(self)->None:
        try:
            Data:dict[Any,Any]=self.Func(self.ID,self.Level)
        except Exception as E:
            self.Error=True
            self.ErrorMessage=str(E)
            return
        
        if (Data["codes"]["lyric"]!=200 or 
           Data["codes"]["info"]!=200 or 
           Data["codes"]["link"]!=200):
            self.Error=True
            self.ErrorMessage="API返回结果为:\n"+json.dumps(Data,indent=4)
        
        try:
            if Data["data"]["audioUrl"]:
                print(repr(Data["data"]["audioUrl"]))
                self.URL=Data["data"]["audioUrl"]
            else:
                print("[Debug]无法获取链接")
                self.Error=True
                self.ErrorMessage="API返回结果为:\n"+json.dumps(Data,indent=4)+"\n其中URL为空"
            self.Album=Data["data"]["album"]
            self.Artist=Data["data"]["artists"]
            self.PictureURL=Data["data"]["picUrl"]
            self.Title=Data["data"]["name"]
            if Data["data"].get("tlyric",None)!=None:
                self.TranslatedLrc=Data["data"]["tlyric"] #现在有了
            else:
                self.TranslatedLrc=""
            self.Lrc=Data["data"]["lyric"]
        except Exception as E:
            self.ErrorMessage+="并且在尝试设置部分字段的值时失败，原因:"+str(E)
        print(Data)
    
    def Download(self,Path:str)->Iterator[tuple[float,str]]:
        Stream:requests.Response=requests.get(self.URL,stream=True)
        Stream.raise_for_status()
        TotalSize:int=int(Stream.headers.get("Content-Length",0))
        DownloadedSize:int=0
        ChunkSize:int=1024
        FilePath:str=Path
        Data:BytesIO=BytesIO()
        import time
        StartTime:float=time.time()
        for Chunk in Stream.iter_content(chunk_size=ChunkSize):
            Data.write(Chunk)
            DownloadedSize+=len(Chunk)
            Speed:float=DownloadedSize/(time.time()-StartTime) if (time.time()-StartTime)>0 else 0
            yield (DownloadedSize/TotalSize,f"已完成:{DownloadedSize/TotalSize:.2%} 速度:{Speed/1024/1024:.2f}MB/s")

        Data.seek(0)
        FileWriter=open(FilePath,"wb+")
        FileWriter.write(Data.read())
        FileWriter.seek(0)

        Mutagen:mutagen.flac=__import__(f"mutagen.{self.Format}",globals(),locals(),[self.Format],0) #瞎写的类型注解，实际上导入的是相应格式
        MetaWriter:mutagen.flac.FLAC|mutagen.mp3.MP3=Mutagen.Open(FileWriter)
        ImageData:BytesIO=BytesIO()
        ImageResp:requests.Response=requests.get(self.PictureURL,stream=True)
        ImageResp.raise_for_status()
        for Chunk in ImageResp.iter_content(chunk_size=ChunkSize):
            ImageData.write(Chunk)
        ImageData.seek(0)

        if self.WriteMeta:
            yield (1.0,"正在写入音频元数据...")
            if self.Format=="mp3":
                from mutagen.id3 import ID3,TIT2,TPE1,TALB,APIC
                MetaWriter.tags.add(TIT2(encoding=3,text=self.Title))
                MetaWriter.tags.add(TPE1(encoding=3,text=self.Artist.split("/")))
                MetaWriter.tags.add(TALB(encoding=3,text=self.Album))
                Picture=APIC(encoding=3,mime="image/jpeg",type=3,desc="Cover",data=ImageData.read())
                MetaWriter.tags.add(Picture)
            elif self.Format=="flac":
                MetaWriter["album"]=self.Album
                MetaWriter["artist"]=self.Artist.split("/")
                MetaWriter["title"]=self.Title
                MetaWriter["lyrics"]=self.Lrc #FLAC支持内联歌词
                Picture=Mutagen.Picture()
                Picture.data=ImageData.read()
                Picture.type=3
                Picture.mime=ImageResp.headers.get("Content-Type","image/jpeg")
                Picture.desc="Cover"
                MetaWriter.add_picture(Picture)
            else: #这mp4我还真不知道怎么处理了（Vivid返回的就是mp4）
                pass
        
        if self.Format=="flac" or self.Format=="mp4":
            MetaWriter.save(FilePath) #必须保存到文件才能写入
        else:
            MetaWriter.save(FilePath,v2_version=3)
        Data.close() #关闭内存文件
        FileWriter.seek(0)
        ImageData.seek(0)

        if self.Pack:
            yield (1.0,"正在打包...")
            ZipData:BytesIO=BytesIO()
            with zipfile.ZipFile(ZipData,"w",zipfile.ZIP_DEFLATED) as Zip:
                Zip.writestr("{} - {}.{}".format(self.Title,self.Artist.replace("/",";"),self.Format),FileWriter.read())
                
                if self.Lrc!="":
                    Zip.writestr("{} - {}.lrc".format(self.Title,self.Artist.replace("/",";")),self.Lrc)
                if self.TranslatedLrc!="":
                    Zip.writestr("{} - {}.translated.lrc".format(self.Title,self.Artist.replace("/",";")),self.TranslatedLrc)
                
                Zip.writestr("{} - {}.jpg".format(self.Title,self.Artist.replace("/",";")),ImageData.read())
                ImageData.close()
                Zip.writestr("Info.txt",f"歌名:{self.Title}\r\n作者:{self.Artist}\r\n专辑:{self.Album}\r\n音质:{[Key for Key,Value in LEVELS.items() if Value==self.Level][0]}\r\nID:{self.ID}\r\n下载自:网易云音乐\r\nAPI提供者:多个")
            
            ZipData.seek(0)
            with open(Path if Path.lower().endswith(".zip") else Path+".zip","wb") as F:
                F.write(ZipData.read())
            ZipData.close()
        
        FileWriter.close()
        ImageData.close()

        if self.Pack and not Path.lower().endswith(".zip"):
            import os
            os.remove(Path) #删除原文件
        
        yield (1.0,"完成!")
    