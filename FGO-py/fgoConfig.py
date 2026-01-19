from __future__ import annotations
import json,os
from typing import Any,Iterable,Optional,Union
from fgoConst import CONFIG
from fgoLogging import getLogger
logger=getLogger('Config')

class ConfigItemList(list):
    def __init__(self,iterable:Iterable[Any])->None:super().__init__(ConfigItem(i)for i in iterable)
    def __setitem__(self,key:int,value:Any)->None:super().__setitem__(key,ConfigItem(value))
    def __add__(self,other:Iterable[Any])->ConfigItemList:return ConfigItemList(self).extend(other)
    def __radd__(self,other:Iterable[Any])->ConfigItemList:return ConfigItemList(other).extend(self)
    def __iadd__(self,other:Iterable[Any])->ConfigItemList:return self.extend(other)
    def __repr__(self)->str:return f'{type(self).__name__}({", ".join(repr(i)for i in self)})'
    def copy(self)->ConfigItemList:return ConfigItemList(self)
    def append(self,obj:Any)->ConfigItemList:
        super().append(ConfigItem(obj))
        return self
    def extend(self,iterable:Iterable[Any])->ConfigItemList:
        super().extend(ConfigItemList(iterable))
        return self
    def insert(self,idx:int,obj:Any)->ConfigItemList:
        super().insert(idx,ConfigItem(obj))
        return self

class ConfigItem(dict):
    def __new__(cls,data:Optional[Union[dict,list,Any]]=None)->Union[ConfigItem,ConfigItemList,Any]:
        if isinstance(data,list):return ConfigItemList(data)
        if not isinstance(data,dict):return data
        return super().__new__(cls)
    def __init__(self,data:Optional[dict[str,Any]]=None)->None:
        if data is None:data={}
        super().__init__((k,ConfigItem(v))for k,v in data.items())
    def __getitem__(self,key):
        if not isinstance(key,str)or not key:
            raise KeyError(f'Invalid config key: {key!r}')
        result=self
        try:
            for k in key.split('.'):
                if isinstance(result,dict):
                    result=dict.__getitem__(result,k)
                elif isinstance(result,list):
                    idx=int(k)
                    if idx<0 or idx>=len(result):
                        raise IndexError(f'Index {idx} out of range for list of length {len(result)}')
                    result=result[idx]
                else:
                    raise KeyError(f'Cannot index into {type(result).__name__}')
        except ValueError:
            raise KeyError(f'Invalid index in key path: {k!r}')
        return result
    def __setitem__(self,key,value):
        if not isinstance(key,str)or not key:
            raise KeyError(f'Invalid config key: {key!r}')
        target=self
        keys=key.split('.')
        try:
            for k in keys[:-1]:
                if isinstance(target,dict):
                    target=dict.__getitem__(target,k)
                elif isinstance(target,list):
                    idx=int(k)
                    if idx<0 or idx>=len(target):
                        raise IndexError(f'Index {idx} out of range')
                    target=target[idx]
                else:
                    raise KeyError(f'Cannot traverse into {type(target).__name__}')
        except ValueError:
            raise KeyError(f'Invalid index in key path: {k!r}')
        if isinstance(target,dict):target.__setattr__(keys[-1],value)
        else:
            idx=int(keys[-1])
            if idx<0 or idx>=len(target):
                raise IndexError(f'Index {idx} out of range')
            target[idx]=value
    def __getattr__(self,name):
        try:
            return super().__getitem__(name)
        except KeyError:
            logger.warning(f'Config key not found: {name}')
            return None
    def __setattr__(self,name,attr):
        try:
            origin=super().__getitem__(name)
            t1,t2=type(origin),type(attr)
            if t1 is t2 or any(issubclass(t1,i)and issubclass(t2,i)for i in(list,dict)):
                super().__setitem__(name,ConfigItem(attr))
            else:logger.error(f'[{name}] Type Mismatch: ({t1.__name__}){origin} -> ({t2.__name__}){attr}')
        except KeyError:
            # 新键，直接设置
            super().__setitem__(name,ConfigItem(attr))
    def __or__(self,other):return ConfigItem(self).update(other)
    def __ror__(self,other):return ConfigItem(other).update(self)
    def __ior__(self,other):return self.update(other)
    def __contains__(self,key):
        try:self[key]
        except(KeyError,IndexError):return False
        return True
    def __repr__(self):return f'{type(self).__name__}({", ".join(f"{k}={v!r}"for k,v in self.items())})'
    def update(self,other:dict[str,Any])->ConfigItem:
        for k,v in self.items():
            if(v2:=other.get(k))is None:continue
            if isinstance(v2,dict)and isinstance(v,dict):
                v.update(v2)
                continue
            self.__setattr__(k,v2)
        return self
    def copy(self)->ConfigItem:return ConfigItem(self)
    def todict(self)->Union[dict[str,Any],list[Any],Any]:
        if isinstance(self,dict):return{k:ConfigItem.todict(v)for k,v in self.items()}
        if isinstance(self,list):return[ConfigItem.todict(i)for i in self]
        return self
    def flatten(self)->dict[tuple[Any,...],Any]:
        if isinstance(self,dict):return{(k,*k2):v2 for k,v in self.items()for k2,v2 in ConfigItem.flatten(v).items()}
        if isinstance(self,list):return{(k,*k2):v2 for k,v in enumerate(self)for k2,v2 in ConfigItem.flatten(v).items()}
        return{():self}


class Config(ConfigItem):
    def __new__(cls,*args:Any,**kwargs:Any)->Config:return super().__new__(cls,CONFIG)
    def __init__(self,file:str='fgoConfig.json')->None:
        super().__init__(CONFIG)
        self.__dict__['file']=file
        if os.path.isfile(file):
            try:
                with open(file,encoding='utf-8')as f:self.update(json.load(f))
            except json.JSONDecodeError as e:
                logger.error(f'Config file parse error: {e}')
            except (OSError,PermissionError) as e:
                logger.error(f'Config file read error: {e}')
    def save(self,file:Optional[str]=None)->None:
        logger.info('Save Config')
        try:
            with open(self.file if file is None else file,'w',encoding='utf-8')as f:json.dump(self,f,ensure_ascii=False,indent=4)
        except (OSError,PermissionError) as e:
            logger.error(f'Config file save error: {e}')
