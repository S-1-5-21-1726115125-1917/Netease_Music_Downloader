from win32more.winui3 import XamlClass
from win32more._winrt import unbox_value,box_value
from win32more.Microsoft.UI.Xaml import RoutedEventArgs,Visibility
from win32more.Windows.Foundation import IInspectable,Uri
from win32more.Microsoft.UI.Xaml.Controls import (
    Page,Grid,TextBox,ComboBoxItem,SelectionChangedEventArgs,ComboBox,StackPanel,Image,ProgressRing,MediaPlayerElement,
)
from win32more.Microsoft.UI.Xaml.Media.Imaging import BitmapImage
from win32more.Microsoft.UI.Xaml.Markup import XamlReader

from typing import Any

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
    @property
    def SongInfoType(self)->type: ...

    @property
    def Settings(self)->dict[str,Any]: ...

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
        self.Info=self.SongInfoType(int(self.ID) if self.ID.isdigit() else self.ID,Level=self._Level,Pack=self.Settings["Pack"],WriteMeta=self.Settings["WriteMeta"])
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
        self.Level.Text=str(self._Level)
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
    @property
    def TemplateType(self)->type: ...
    
    @property
    def Levels(self)->dict[Any,Any]: ...

    def __init__(self):
        super().__init__(own=True)
        self.InitializeComponent()
        self.InputBox:TextBox
        self.LevelSelect:ComboBox
        self.InfoContent:StackPanel
        self.SelectedLevel:str=""
        for Key in self.Levels.keys():
            self.LevelSelect.Items.Append(box_value(Key))
    
    def InitializeComponent(self)->None:
        self.LoadComponentFromFile(Path(__file__).with_name("Downloader.HomePage.xaml"))
    
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
            print("[WARN] ID必须为数字，如果这是网易云音乐会无法解析")
        _Loading=Loading("正在获取歌曲信息...")
        self.InfoContent.Children.Clear()
        self.InfoContent.Children.Append(_Loading)
        _Template=self.TemplateType(self.InputBox.Text,self.SelectedLevel)
        while not _Template.Initnialized:
            await asyncio.sleep(0.1)
        
        self.InfoContent.Children.Clear()
        self.InfoContent.Children.Append(_Template)
        args.Handled=True
    
    def LevelChanged(self,sender:IInspectable,args:SelectionChangedEventArgs)->None:
        _ComboBox:ComboBox=sender.as_(ComboBox)
        Text:ComboBoxItem=unbox_value(_ComboBox.SelectedValue)
        print(sender,args)
        if Text in self.Levels:
            print(f"[INFO] 选择了音质:{Text}({self.Levels[Text]})")
            self.SelectedLevel=self.Levels[Text]
        else:
            print(f"[WARN] 选择了未知音质:{Text}")
        args.Handled=True
