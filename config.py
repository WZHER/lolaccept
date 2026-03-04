"""
配置文件
"""
import os

# LOL客户端默认安装路径
DEFAULT_LOL_PATHS = [
    r"C:\Riot Games\League of Legends",
    r"D:\Riot Games\League of Legends",
]

# API配置
OPGG_API_URL = "https://api.op.gg"
REQUEST_TIMEOUT = 10

# UI配置
WINDOW_TITLE = "LOL辅助工具"
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 700
WINDOW_MIN_WIDTH = 400
WINDOW_MIN_HEIGHT = 600

# 缓存配置
CACHE_EXPIRE_HOURS = 1

# 英雄头像API
ICON_BASE_URL = "https://ddragon.leagueoflegends.com/cdn/14.1.1/img/profileicon/"
