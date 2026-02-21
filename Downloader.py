#我只是一只快乐的API Caller:(
#另外有个功能正常的:https://blog.cyrui.cn/netease/api/getMusicUrl.php
#但是返回格式非常阴间，我是不可能用在这里的，然而由于tmetu.cn的暴似，导致我不得不去上面这个了（悲）
API_ADDR:str="https://www.tmetu.cn/api/music/api.php" #R.I.P
API_ADDR_LRC:str="https://blog.cyrui.cn/netease/api/getLyric.php"
API_ADDR_INFO:str="https://blog.cyrui.cn/netease/api/getSongDetail.php"
API_ADDR_LINK:str="https://blog.cyrui.cn/netease/api/getMusicUrl.php"
LEVELS:dict[str,str]={
    "标准":"standard",
    "极高":"exhigh",
    "无损(CD)":"lossless",
    "Vivid":"vivid", #(这啥?我不知道啊?打都打不开,12声道干啥去了?)
    "Hi-Res":"hires",
    "高清环绕声":"sky", #(这个纯扯淡)
    "沉浸环绕声":"jyeffect", #(扯淡x2)
    "超清母带(最高)":"jymaster" #(扯淡x3,甚至还用AI造假,发行商根本没发行过这个音质)
    #然而相对QQ音乐的所谓“AI伴唱模式”“AI5.1音质”而言，网易还是太拟人了
}
SETTINGS:dict[str,bool]={
    "Pack":False,
    "WriteMeta":True
}

import requests
from typing import Any
import zipfile
from abc import ABC,abstractmethod
from io import BytesIO
import json
import mutagen.flac,mutagen.m4a,mutagen.mp3
from _collections_abc import Iterator
from urllib.parse import urlparse
import time

from Structure import *

def GetSongInfo(ID:int,Level:str)->dict[Any,Any]:
    LyricResp:dict[Any,Any]=requests.get(
        url=API_ADDR_LRC,
        params={
            "id":ID
        }
    ).json()
    InfoResp:dict[Any,Any]=requests.get(
        url=API_ADDR_INFO,
        params={
            "id":ID
        }
    ).json()
    LinkResp:dict[Any,Any]=requests.get(
        url=API_ADDR_LINK,
        params={
            "id":ID,
            "level":Level
        }
    ).json()
    ReturnCode:dict[str,int]={
        "lyric":LyricResp["code"],
        "info":InfoResp["code"],
        "link":LinkResp["code"]
    } #这下正常了
    Lyric:str=LyricResp["lrc"]["lyric"]
    TranslatedLyric:str=LyricResp["tlyric"]["lyric"]
    Name:str=InfoResp["songs"][0]["name"]
    Artists:str="/".join([Item["name"] for Item in InfoResp["songs"][0]["ar"]]) #我真是服了这个阴间格式了
    AlbumName:str=InfoResp["songs"][0]["al"]["name"]
    PictureURL:str=InfoResp["songs"][0]["al"]["picUrl"]
    Link:str=LinkResp["data"][0]["url"]
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
    def __init__(self,ID:int,WriteMeta=True,Pack=False,Level:str="standard"):
        self.ID:int=ID
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
            Data:dict[Any,Any]=GetSongInfo(self.ID,self.Level)
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
    

#UI
#1908182683
#2735521247

from win32more.winui3 import XamlApplication,XamlClass,XamlType,xaml_typename
from win32more._winrt import unbox_value
from win32more.Windows.UI.Xaml.Interop import TypeKind
from win32more.Microsoft.UI.Xaml import Window,RoutedEventArgs,Thickness,Visibility
from win32more.Windows.Foundation import IInspectable,Uri
from win32more.Windows.Storage.Pickers import FileSavePicker
from win32more.Microsoft.UI.Xaml.Controls import (
    NavigationView,NavigationViewSelectionChangedEventArgs,NavigationViewItem,Frame,
    Page,Grid,TextBox,ComboBoxItem,SelectionChangedEventArgs,ComboBox,StackPanel,Image,ProgressRing,MediaPlayerElement,
    NavigationViewDisplayModeChangedEventArgs,NavigationViewBackRequestedEventArgs,NavigationViewDisplayMode
)
from win32more.Microsoft.UI.Xaml.Media.Imaging import BitmapImage
from win32more.Microsoft.UI.Xaml.Markup import XamlReader
from win32more.Microsoft.UI.Windowing import (
    TitleBarHeightOption,
    OverlappedPresenter
)
try:
    from typing_extensions import override
except ModuleNotFoundError:
    from typing import override

from pathlib import Path

import asyncio

class DownloadInfo(XamlClass,StackPanel):
    def __init__(self):
        super().__init__(own=True)
        self.InitializeComponent()

    def InitializeComponent(self)->None:
        self.LoadComponentFromFile(Path(__file__).with_name("DownloadInfo.xaml"))
    
    def WriteStatus(self,Status:float)->None:
        self.StatusBar.Value=Status*100
    
    def WriteInfo(self,Info:str)->None:
        self.StatusText.Text=Info

class Loading(XamlClass,Grid):
    def __init__(self,PlaceHolderText:str):
        super().__init__(own=True)
        self.InitializeComponent()
        self.Ring:ProgressRing
        self.Ring.IsActive=True
        self.PlaceHolderText:TextBox
        self.PlaceHolderText.Text=PlaceHolderText
    
    def InitializeComponent(self)->None:
        self.LoadComponentFromFile(Path(__file__).with_name("Loading.xaml"))

class Template(XamlClass,Grid):
    def __init__(self,ID:str,Level:str):
        super().__init__(own=True)
        self.InitializeComponent()
        self.ID:str=ID
        self._Level:str=Level
        self.Initnialized:bool=False
        asyncio.create_task(self.InitializeInfo()) #异步初始化
    
    def InitializeComponent(self)->None:
        self.LoadComponentFromFile(Path(__file__).with_name("Template.xaml"))
    
    async def InitializeInfo(self)->None:
        self.Info:SongInfo=SongInfo(int(self.ID),Level=self._Level,Pack=SETTINGS["Pack"],WriteMeta=SETTINGS["WriteMeta"])
        Loop=asyncio.get_event_loop()
        await Loop.run_in_executor(None,self.Info.Initnalize)
        if self.Info.Error:
            self.ErrorBox.IsOpen=True
            self.ErrorBox.Message=self.Info.ErrorMessage
            self.DownloadButton.IsEnabled=False
            self.InfoContent.Visibility=Visibility.Collapsed
        
        self.Title.Text=self.Info.Title
        self.Artist.Text=self.Info.Artist
        self.Album.Text=self.Info.Album
        self.Format.Text=self.Info.Format
        print(self.Info.URL,self.Info.Format)
        try:
            TempBitmap:BitmapImage=BitmapImage()
            TempBitmap.UriSource=Uri(self.Info.PictureURL)
            TempImage=Image()
            TempImage.Source=TempBitmap
            self.Cover.Child=TempImage
        except:
            pass
        self.Level.Text=self._Level
        try:
            XamlSource:str="<MediaPlayerElement xmlns=\"http://schemas.microsoft.com/winfx/2006/xaml/presentation\" xmlns:x=\"http://schemas.microsoft.com/winfx/2006/xaml\" AreTransportControlsEnabled=\"True\" AutoPlay=\"False\" HorizontalAlignment=\"Center\" Source=\"{}\"/>".format(self.Info.URL.replace("&","&amp;"))
            print(self.Info.URL)
            print(XamlSource)
            print(self.Info)
            TempMediaPlayerElement:MediaPlayerElement=MediaPlayerElement(own=True,move=XamlReader.Load(XamlSource))
            self.AudioPlayer.Child=TempMediaPlayerElement
        except:
            pass
        self.Initnialized=True

    async def OnDownloadClick(self,sender:IInspectable,args:RoutedEventArgs):
        if not self.Initnialized:
            print("[WARN] 信息未初始化完成，无法下载")
            args.Handled=False
            return
        

        DefaultName:str="{} - {}.{}".format(self.Info.Title,self.Info.Artist.replace("/",";"),self.Info.Format)
        from tkinter import Tk,filedialog
        TempWindow:Tk=Tk()
        TempWindow.withdraw()
        TempWindow.iconbitmap(default="Program\\favicon.ico")
        SavePath:str=filedialog.asksaveasfilename(
            parent=TempWindow,
            title="选择保存位置",
            initialfile=DefaultName,
            filetypes=[(f"{self.Info.Format.upper()}音频文件",f"*.{self.Info.Format}"),("所有文件","*.*")]
        )
        TempWindow.destroy()
        if SavePath=="":
            print("[WARN] 未选择保存位置，取消下载")
            args.Handled=False
            return
        StatusArea:DownloadInfo=DownloadInfo()
        self.StatusArea.Child=StatusArea
        Loop=asyncio.get_event_loop()
        def UpdateUI(Status:float,Info:str):
            StatusArea.WriteStatus(Status)
            StatusArea.WriteInfo(Info)
        
        def StartDownload():
            import time
            LastUpdate=0
            for (Status,Info) in self.Info.Download(SavePath):
                Now=time.time()
                if Now-LastUpdate>0.1 or Status==1.0:
                    Loop.call_soon_threadsafe(UpdateUI,Status,Info)
                    LastUpdate=Now

        Loop.run_in_executor(None,StartDownload)
        args.Handled=True

class DownloaderPage(XamlClass,Page):
    def __init__(self):
        super().__init__(own=True)
        self.InitializeComponent()
        self.InputBox:TextBox
        self.LevelSelect:ComboBox
        self.InfoContent:StackPanel
        self.SelectedLevel:str=""
    
    def InitializeComponent(self)->None:
        self.LoadComponentFromFile(Path(__file__).with_suffix(".HomePage.xaml"))
    
    async def OnDownloadButtonClick(self,sender:IInspectable,args:RoutedEventArgs):
        if self.SelectedLevel=="":
            print("[WARN] 未选择音质，无法解析")
            args.Handled=False
            return
        if self.InputBox.Text=="":
            print("[WARN] 未输入ID，无法解析")
            args.Handled=False
            return
        if not self.InputBox.Text.isdigit():
            print("[WARN] ID必须为数字，无法解析")
            args.Handled=False
            return
        _Loading=Loading("正在获取歌曲信息...")
        self.InfoContent.Children.Clear()
        self.InfoContent.Children.Append(_Loading)
        _Template=Template(self.InputBox.Text,self.SelectedLevel)
        while not _Template.Initnialized:
            await asyncio.sleep(0.1)
        
        self.InfoContent.Children.Clear()
        self.InfoContent.Children.Append(_Template)
        args.Handled=True
    
    def LevelChanged(self,sender:IInspectable,args:SelectionChangedEventArgs)->None:
        _ComboBox:ComboBox=sender.as_(ComboBox)
        Text:ComboBoxItem=unbox_value(_ComboBox.SelectedValue)
        print(sender,args)
        if Text in LEVELS:
            print(f"[INFO] 选择了音质:{Text}({LEVELS[Text]})")
            self.SelectedLevel=LEVELS[Text]
        else:
            print(f"[WARN] 选择了未知音质:{Text}")
        args.Handled=True

class SettingsPage(XamlClass,Page):
    """
    最后完工的页面\n
    在完工之前连一点存在感都没有
    """
    def __init__(self):
        super().__init__(own=True)
        self.InitializeComponent()
        print(dir(self.WriteMetaSetting),dir(self.PackSetting))
    
    def InitializeComponent(self)->None:
        self.LoadComponentFromFile(Path(__file__).with_suffix(".SettingsPage.xaml"))

    def OnWriteMetaToggled(self,sender:IInspectable,args:RoutedEventArgs):
        SETTINGS["WriteMeta"]=self.WriteMetaSetting.IsOn
        args.Handled=True

    def OnPackToggled(self,sender:IInspectable,args:RoutedEventArgs):
        SETTINGS["Pack"]=self.PackSetting.IsOn
        args.Handled=True

class MainWindow(XamlClass,Window):
    def __init__(self):
        super().__init__(own=True)
        self.InitializeComponent()
        self.MainNavView:NavigationView
        self.ContentFrame:Frame
        self.AppTitleBar:Grid
        Presenter:OverlappedPresenter=OverlappedPresenter.Create()
        Presenter.IsAlwaysOnTop=True
        self.AppWindow.SetIcon(Path(__file__).with_name("favicon.ico").as_posix().replace("/","\\"))
        self.Title="冈易云音乐下载器" #不是WinUI Desktop!!我不叫WinUI Desktop!!
        self.AppWindow.SetPresenter(Presenter)
    
    def InitializeComponent(self)->None:
        self.LoadComponentFromFile(Path(__file__).with_suffix(".xaml"))
    
    def OnWindowLoaded(self,sender:IInspectable,args:RoutedEventArgs)->None:
        self.MainNavView.SelectedItem=self.MainNavView.MenuItems[0] #自动触发选择事件
        args.Handled=True

    def OnNavigationSelectionChanged(self,sender:IInspectable,args:NavigationViewSelectionChangedEventArgs)->None:
        TagName:str=unbox_value(args.SelectedItem.as_(NavigationViewItem).Tag)
        print("[INFO] Navigate to page:"+TagName)
        self.ContentFrame.Navigate(xaml_typename(TagName,TypeKind.Custom))
    
    def OnBackRequested(self,sender:IInspectable,args:NavigationViewBackRequestedEventArgs):
        args.Handled=True
        pass #NotImplemented
    
    def OnDisplayModeChanged(self,sender:IInspectable,args:NavigationViewDisplayModeChangedEventArgs):
        if self.MainNavView.DisplayMode==NavigationViewDisplayMode.Minimal:
            self.AppTitleBar.Margin=Thickness(96,0,0,0)
        else:
            self.AppTitleBar.Margin=Thickness(48,0,0,0)

class App(XamlApplication):
    def OnLaunched(self,args):
        self.Window=MainWindow()
        self.Window.ExtendsContentIntoTitleBar=True
        self.Window.SetTitleBar(self.Window.AppTitleBar)
        self.Window.AppWindow.TitleBar.PreferredHeightOption=TitleBarHeightOption.Tall
        self.DownloaderPage:DownloaderPage=DownloaderPage()
        self.SettingsPage:SettingsPage=SettingsPage()
        self.Window.Activate()
    
    @override
    def GetXamlTypeByFullName(self,fullName):
        if fullName=="Downloader":
            return XamlType("Downloader",TypeKind.Custom,activate_instance=lambda:self.DownloaderPage)
        elif fullName=="Settings":
            return XamlType("Settings",TypeKind.Custom,activate_instance=lambda:self.SettingsPage)
        return super().GetXamlTypeByFullName(fullName)

XamlApplication.Start(App)