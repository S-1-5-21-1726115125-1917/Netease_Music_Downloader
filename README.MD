## 运行需求

Python环境

Windows App Runtime

### 环境安装方式

1. **安装Python**
- [在这里下载](https://registry.npmmirror.com/-/binary/python/3.10.10/python-3.10.10-amd64.exe)Python
- 在安装程序打开后的第一个界面的下面选择`Add Python 3.xx to path`，然后如果不是特殊情况点击`Install now`即可

2. **安装Windows App Runtime**
- [在这里下载](https://aka.ms/windowsappsdk/1.7/1.7.250909003/windowsappruntimeinstall-x64.exe)Windows App Runtime
- 直接打开下载下来的exe，等待弹出的控制台窗口自动关闭时就安装好了

## 运行前需求

运行`Initinalize.cmd`，这会安装好所有的依赖（当然你也可以手动打开`requirements.txt`查看依赖）

## 主程序

主程序是`Downloader.py`，双击即可启动（Python环境在安装时会自动关联.py文件）

## 问题

- `Windows App Runtime`可能安装失败

- 安装依赖时可能因为权限不够安装失败，请以管理员身份运行`Initinalize.cmd`

- 极不稳定，因为我几乎没写异常捕获，并且我还是古希腊掌管内存泄漏的神，哪里都能漏，比如你在解析一首并立刻解析第二首就会 余 声 绕 梁 ，并且内存占用也是飙升
