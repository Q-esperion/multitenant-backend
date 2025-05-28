from typing import List, Dict, Any
from fastapi import APIRouter
from app.models.public import Menu, Api

def generate_menu_from_router(router: APIRouter) -> List[Dict[str, Any]]:
    """
    从FastAPI路由生成菜单结构
    """
    menus = []
    
    def process_route(route, prefix=""):
        # 处理子路由
        if isinstance(route, APIRouter):
            for r in route.routes:
                process_route(r, prefix + route.prefix)
            return
        
        # 获取路由的tags和summary
        tags = route.tags[0] if route.tags else "未分类"
        summary = route.summary or route.name
        
        # 构建菜单路径
        path = prefix + route.path
        if path.startswith("/"):
            path = path[1:]
        
        # 构建菜单项
        menu = {
            "name": summary,
            "menu_type": "menu",
            "path": f"/{path}",
            "component": path.replace("/", "/"),
            "icon": "menu",
            "order": 1,
            "is_hidden": False,
            "keepalive": True
        }
        
        menus.append(menu)
    
    # 处理所有路由
    for route in router.routes:
        process_route(route)
    
    return menus

def generate_api_from_router(router: APIRouter) -> List[Dict[str, Any]]:
    """
    从FastAPI路由生成API权限结构
    """
    apis = []
    
    def process_route(route, prefix=""):
        # 处理子路由
        if isinstance(route, APIRouter):
            for r in route.routes:
                process_route(r, prefix + route.prefix)
            return
        
        # 获取路由的tags和summary
        tags = route.tags[0] if route.tags else "未分类"
        summary = route.summary or route.name
        
        # 构建API路径
        path = prefix + route.path
        if path.startswith("/"):
            path = path[1:]
        
        # 获取HTTP方法
        methods = route.methods or {"GET"}
        method = next(iter(methods))  # 获取第一个方法
        
        # 构建API项
        api = {
            "path": f"/api/v1/{path}",
            "method": method,
            "summary": summary,
            "tags": tags
        }
        
        apis.append(api)
    
    # 处理所有路由
    for route in router.routes:
        process_route(route)
    
    return apis

def get_all_routes(router: APIRouter) -> List[Dict[str, Any]]:
    """
    获取所有路由信息
    """
    routes = []
    
    def process_route(route, prefix=""):
        # 处理子路由
        if isinstance(route, APIRouter):
            for r in route.routes:
                process_route(r, prefix + route.prefix)
            return
        
        # 获取路由信息
        route_info = {
            "path": prefix + route.path,
            "methods": list(route.methods) if route.methods else ["GET"],
            "tags": route.tags,
            "summary": route.summary,
            "name": route.name
        }
        routes.append(route_info)
    
    # 处理所有路由
    for route in router.routes:
        process_route(route)
    
    return routes 