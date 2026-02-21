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
import time

from Structure import *
from Core import (SongInfo as AbsSongInfo,FunctionType)


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

class SongInfo(AbsSongInfo):
    @property
    def Func(self)->FunctionType:
        return GetSongInfo
    

#UI
#1908182683
#2735521247

#这个import数量够恐怖吧()

from win32more.winui3 import XamlApplication,XamlClass,XamlType,xaml_typename
from win32more._winrt import unbox_value
from win32more.Windows.UI.Xaml.Interop import TypeKind
from win32more.Microsoft.UI.Xaml import Window,RoutedEventArgs,Thickness
from win32more.Windows.Foundation import IInspectable
from win32more.Microsoft.UI.Xaml.Controls import (
    NavigationView,NavigationViewSelectionChangedEventArgs,NavigationViewItem,Frame,
    Page,Grid,
    NavigationViewDisplayModeChangedEventArgs,NavigationViewBackRequestedEventArgs,NavigationViewDisplayMode
)
from win32more.Microsoft.UI.Windowing import (
    TitleBarHeightOption,
    OverlappedPresenter
)
try:
    from typing_extensions import override
except ModuleNotFoundError:
    from typing import override

from pathlib import Path

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
        return SETTINGS

class DownloaderPage(AbsDownliaderPage):
    @property
    def TemplateType(self)->type:
        return Template
    
    @property
    def Levels(self)->dict[str,Any]:
        return LEVELS

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
        self.Title="普普通通的音乐下载器" #不是WinUI Desktop!!我不叫WinUI Desktop!!
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

import QQ

class App(XamlApplication):
    def OnLaunched(self,args):
        self.Window=MainWindow()
        self.Window.ExtendsContentIntoTitleBar=True
        self.Window.SetTitleBar(self.Window.AppTitleBar)
        self.Window.AppWindow.TitleBar.PreferredHeightOption=TitleBarHeightOption.Tall
        self.NeteaseMusicDownloaderPage:DownloaderPage=DownloaderPage() #网易的因为是集成的，所以与其他的不同
        self.QQMusicDownloaderPage:QQ.DownloaderPage=QQ.DownloaderPage()
        self.SettingsPage:SettingsPage=SettingsPage()
        self.Window.Activate()
    
    @override
    def GetXamlTypeByFullName(self,fullName):
        if fullName=="NeteaseMusicDownloader":
            return XamlType("NeteaseMusicDownloader",TypeKind.Custom,activate_instance=lambda:self.NeteaseMusicDownloaderPage)
        elif fullName=="QQMusicDownloader":
            return XamlType("QQMusicDownloader",TypeKind.Custom,activate_instance=lambda:self.QQMusicDownloaderPage)
        elif fullName=="Settings":
            return XamlType("Settings",TypeKind.Custom,activate_instance=lambda:self.SettingsPage)
        return super().GetXamlTypeByFullName(fullName)

XamlApplication.Start(App)