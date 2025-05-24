from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.public import MenuType

class MenuBase(BaseModel):
    """菜单基础模型"""
    name: str = Field(..., description="菜单名称")
    title: str = Field(..., description="菜单标题")
    menu_type: MenuType = Field(..., description="菜单类型")
    path: str = Field(..., description="菜单路径")
    component: str = Field(..., description="组件路径")
    icon: Optional[str] = Field(None, description="图标")
    order: int = Field(0, description="排序")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    is_hidden: bool = Field(False, description="是否隐藏")
    keepalive: bool = Field(False, description="是否缓存")
    redirect: Optional[str] = Field(None, description="重定向")
    is_enabled: bool = Field(True, description="是否启用")

class MenuCreate(MenuBase):
    """创建菜单模型"""
    parent_id: Optional[int] = None

class MenuUpdate(MenuBase):
    """更新菜单模型"""
    name: Optional[str] = None
    menu_type: Optional[MenuType] = None
    path: Optional[str] = None
    component: Optional[str] = None
    order: Optional[int] = None
    is_hidden: Optional[bool] = None
    keepalive: Optional[bool] = None
    redirect: Optional[str] = None
    is_enabled: Optional[bool] = None

class MenuInDBBase(MenuBase):
    """数据库中的菜单模型"""
    id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False

    class Config:
        from_attributes = True

class MenuResponse(MenuBase):
    """菜单响应模型"""
    id: int
    parent_id: Optional[int] = None
    children: List['MenuResponse'] = []

    class Config:
        from_attributes = True

MenuResponse.model_rebuild() 