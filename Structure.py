from ctypes import Structure as _Structure,windll,byref,FormatError,GetLastError,sizeof,c_void_p,create_unicode_buffer,cast,c_wchar_p
from ctypes.wintypes import *

from typing import Any

PyCStructType=type(_Structure)

ctypesMapping:dict[str,str]={
    "c_wchar":"wchar_t",
    "c_wchar_p":"wchar_t*",
    "c_char":"char",
    "c_byte":"char",
    "c_ubyte":"unsigned char",
    "c_short":"short",
    "c_ushort":"unsigned short",
    "c_int":"int",
    "c_uint":"unsigned int",
    "c_long":"long",
    "c_ulong":"unsigned long",
    "c_longlong":"long long",
    "c_ulonglong":"unsigned long long",
    "c_void_p":"void*",
}

def ToCName(Type:Any)->str:
    """
    将ctypes的类型名称转为C/C++的基本类型名称
    LP_开头的是动态生成的
    """
    Name:str=Type.__name__
    PointerLevel:str=""
    
    #通常由POINTER生成，都是LP_开头的
    while Name.startswith("LP_"):
        PointerLevel+="*"
        Name=Name[3:]

    if Name in ctypesMapping:
        return ctypesMapping[Name]+PointerLevel
    elif Name.startswith("c_"):
        return Name[2:]+PointerLevel
    
    return "auto"

# 类定义
#Structure的元类
class _Structure_Meta_(PyCStructType):
    def __new__(cls,name:str,bases:tuple[Any],attrs:dict[str,Any])->PyCStructType: #type:ignore[reportInvalidTypeForm]
        _fields_=list(attrs.get("__annotations__", {}).items())
        attrs["_fields_"]=_fields_
        return PyCStructType.__new__(cls,name,bases,attrs)
    
    def __repr__(self)->str:
        # C/C++:?
        if self._fields_==[]:
            return "struct "+self.__name__+" {};"
        String:str="struct "+self.__name__+"\n{"
        for Name,Type in self._fields_:
            String+="\n    "+ToCName(Type)+" "+Name+";"
        String+="\n};"
        return String

# Structure类
class Structure(_Structure,metaclass=_Structure_Meta_):
    def __repr__(self)->str:
        return self.__class__.__name__+" v1="+"{"+",".join([str(getattr(self,Attr,"NULL")) for Attr,Type in self._fields_])+"}"+";"
