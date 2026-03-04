"""
战绩查询模块
"""
import requests
from datetime import datetime
from config import OPGG_API_URL, REQUEST_TIMEOUT


class MatchHistory:
    """战绩查询类"""

    @staticmethod
    def get_opgg_history(summoner_name, region="kr"):
        """
        从OP.GG获取战绩
        注意：需要代理或使用其他API源
        """
        try:
            url = f"{OPGG_API_URL}/summoners/{region}/{summoner_name}/matches"
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"OP.GG查询失败: {e}")
        return None

    @staticmethod
    def format_win_rate(wins, losses):
        """计算并格式化胜率"""
        total = wins + losses
        if total == 0:
            return "0%"
        return f"{int(wins / total * 100)}%"

    @staticmethod
    def format_kda(kills, deaths, assists):
        """计算并格式化KDA"""
        if deaths == 0:
            return "Perfect"
        return f"{(kills + assists) / deaths:.2f}"

    @staticmethod
    def format_duration(seconds):
        """格式化对局时长"""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}分{secs}秒"

    @staticmethod
    def get_champion_name(champion_id, champion_data=None):
        """
        根据ID获取英雄名称
        可以从英雄联盟Data Dragon获取英雄数据
        """
        # 简单的英雄ID映射（完整数据需要从Data Dragon获取）
        hero_map = {
            1: "安妮", 2: "奥拉夫", 3: "加里奥", 4: "特里斯塔娜", 5: "辛吉德",
            # 可以继续添加更多英雄
        }
        return hero_map.get(champion_id, f"未知英雄({champion_id})")
