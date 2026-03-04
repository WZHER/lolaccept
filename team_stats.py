"""
队友战绩展示模块
"""
import json
import os
import sys
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QTableWidgetItem


def load_champions_data():
    """加载英雄数据"""
    try:
        # 获取运行时资源所在目录
        # 支持开发环境和 PyInstaller 打包后的 exe 环境
        if hasattr(sys, "_MEIPASS"):
            base_dir = sys._MEIPASS  # PyInstaller 解压目录
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        champions_file = os.path.join(base_dir, 'champions.json')

        if os.path.exists(champions_file):
            with open(champions_file, 'r', encoding='utf-8') as f:
                champions = json.load(f)
                # 创建 heroId -> title 的映射字典
                champion_map = {}
                for hero in champions:
                    hero_id = hero.get('heroId')
                    title = hero.get('title')
                    if hero_id and title:
                        champion_map[hero_id] = title
                return champion_map
    except Exception as e:
        print(f"[DEBUG] 加载英雄数据失败: {e}")
    return {}


# 全局加载英雄数据
CHAMPION_MAP = load_champions_data()
print(f"[DEBUG] 成功加载 {len(CHAMPION_MAP)} 个英雄数据")


class TeamStatsWorker(QObject):
    """队友战绩获取工作线程"""

    # 信号定义
    stats_ready = pyqtSignal(list)  # 队友数据列表
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, lol_client):
        super().__init__()
        self.lol_client = lol_client
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_game_phase)
        self.checking = False
        self.last_team_data_hash = None  # 用于避免重复更新

    def start_monitoring(self):
        """开始监测选人阶段（自动运行，匹配一次刷新一次）"""
        self.checking = True
        self.timer.start(2000)  # 每2秒检查一次
        # 立即检查一次
        self._check_game_phase()

    def stop_monitoring(self):
        """停止监测"""
        self.checking = False
        self.timer.stop()

    def _check_game_phase(self):
        """检查游戏阶段（选人阶段或游戏内）"""
        if not self.checking:
            return

        try:
            # 1. 先检查是否在选人阶段
            session = self.lol_client.get_champ_select_session()

            if session is not None:
                print(f"[DEBUG] 选人阶段，获取队友")
                # 选人阶段：仅获取队友信息
                team_data = self._extract_team_data(session)

                # 计算数据哈希，避免重复更新
                team_hash = hash(str(team_data))
                if team_hash != self.last_team_data_hash:
                    self.last_team_data_hash = team_hash
                    if team_data:
                        self.stats_ready.emit(team_data)

        except Exception as e:
            print(f"[DEBUG] 检查游戏阶段异常: {e}")
            import traceback
            traceback.print_exc()

    def _extract_team_data(self, session):
        """提取队友数据"""
        team_data = []

        # 获取己方队伍
        my_team = session.get('myTeam', [])

        # 获取当前登录玩家的PUUID用于判断是否是自己
        my_puuid = None
        try:
            current_summoner = self.lol_client.get_summoner_info()
            my_puuid = current_summoner.get('puuid') if current_summoner else None
        except Exception as e:
            pass

        for i, player in enumerate(my_team):
            puuid = player.get('puuid')
            summoner_id = player.get('summonerId')
            game_name = player.get('gameName')
            tag_line = player.get('tagLine')

            # 构造显示名称：只显示游戏名，去掉 # 和后面的数字
            if game_name:
                summoner_name = game_name
            else:
                summoner_name = "未知"

            # 判断是否是自己
            is_me = (puuid == my_puuid) if puuid and my_puuid else False

            # 跳过无PUUID的玩家（但仍保留自己的数据）
            if not puuid:
                continue

            # 使用PUUID获取战绩
            try:
                history = self.lol_client.get_match_history(puuid, count=20)
            except Exception as e:
                history = None

            # 计算近期战绩统计
            stats = self._calculate_stats(history)

            # 提取最近 10 场战绩详细信息
            recent_matches = []
            if history and history.get('games'):
                games_data = history.get('games', {})
                games = games_data.get('games', [])
                for game in games[:10]:  # 只取最近 10 场
                    if game.get('participants'):
                        participant = game['participants'][0]
                        stats_data = participant.get('stats', {})

                        kills = stats_data.get('kills', 0)
                        deaths = stats_data.get('deaths', 0)
                        assists = stats_data.get('assists', 0)
                        kda_str = f"{kills}/{deaths}/{assists}"
                        result = "胜利" if stats_data.get('win', False) else "失败"

                        # 获取英雄名
                        champion_id = participant.get('championId', 0)
                        champion_name = CHAMPION_MAP.get(str(champion_id), f"英雄{champion_id}")

                        recent_matches.append({
                            'hero': champion_name,
                            'kda': kda_str,
                            'result': result
                        })

            team_data.append({
                'name': summoner_name,
                'kda': stats.get('avg_kda', 'N/A'),
                'win_rate': stats.get('win_rate', 'N/A'),
                'games': stats.get('total_games', 0),
                'wins': stats.get('wins', 0),
                'losses': stats.get('losses', 0),
                'score': stats.get('score', 0),
                'level': stats.get('level', '无数据'),
                'level_color': stats.get('level_color', '#999999'),
                'recent_matches': recent_matches
            })

        return team_data

    # 下面开始是统计和评分相关逻辑，仅用于队友数据

    def _calculate_stats(self, history):
        """计算战绩统计和评分"""
        if not history or not history.get('games'):
            return {'avg_kda': 'N/A', 'win_rate': 'N/A', 'total_games': 0, 'score': 0, 'level': '无数据', 'level_color': '#999999'}

        # 数据结构是 history['games']['games']
        games_data = history.get('games', {})
        games = games_data.get('games', [])

        if not games:
            return {'avg_kda': 'N/A', 'win_rate': 'N/A', 'total_games': 0, 'score': 0, 'level': '无数据', 'level_color': '#999999'}

        total_games = len(games)

        wins = 0
        total_kda = 0
        total_score = 0
        is_aram = False  # 标记是否为大乱斗模式

        for game in games:
            if game.get('participants'):
                # 检查游戏模式
                game_mode = game.get('gameMode', '')
                is_aram = (game_mode == 'ARAM')

                participant = game['participants'][0]
                stats = participant.get('stats', {})

                if stats.get('win'):
                    wins += 1

                kills = stats.get('kills', 0)
                deaths = stats.get('deaths', 0)
                assists = stats.get('assists', 0)

                if deaths == 0:
                    kda = kills + assists
                else:
                    kda = (kills + assists) / deaths

                total_kda += kda


                # 计算单场评分（根据游戏模式调整）
                game_duration = game.get('gameDuration', 0)  # 游戏时长（秒）
                game_score = self._calculate_game_score(kills, deaths, assists, stats.get('win', False),
                                                       stats.get('totalDamageDealtToChampions', 0),
                                                       stats.get('minionsKilled', 0) + stats.get('neutralMinionsKilled', 0),
                                                       stats.get('visionScore', 0),
                                                       game_duration,
                                                       is_aram)
                total_score += game_score

        losses = total_games - wins
        avg_kda = total_kda / total_games if total_games > 0 else 0
        win_rate = f"{int(wins / total_games * 100)}%" if total_games > 0 else "0%"
        avg_score = total_score / total_games if total_games > 0 else 0

        # 获取等级和颜色
        level, level_color = self._get_level_info(avg_score)

        return {
            'total_games': total_games,
            'wins': wins,
            'losses': losses,
            'avg_kda': f"{avg_kda:.2f}",
            'win_rate': win_rate,
            'score': avg_score,
            'level': level,
            'level_color': level_color
        }

    def _calculate_game_score(self, kills, deaths, assists, win, damage, cs, vision, game_duration, is_aram=False):
        """计算单场评分（根据游戏时长动态调整）"""
        score = 100.0

        # 计算游戏时长（分钟）
        duration_minutes = game_duration / 60 if game_duration > 0 else 30  # 默认30分钟

        # 计算时长调整系数：游戏越长，需要的数据越高才能获得同样的评分
        # 30分钟为基准，每多1分钟，系数增加0.5%，最大增加50%
        time_factor = 1.0
        if duration_minutes > 30:
            extra_minutes = min(duration_minutes - 30, 100)  # 最多加100分钟
            time_factor = 1.0 + (extra_minutes * 0.005)
        elif duration_minutes < 20:
            # 游戏太短（可能是翻盘或投降），适当降低评分标准
            time_factor = 0.9

        # KDA 加分（降低权重，并受时长系数影响）
        if deaths == 0:
            kda = kills + assists
        else:
            kda = (kills + assists) / deaths

        if kda >= 6:
            score += int(15 / time_factor)
        elif kda >= 5:
            score += int(12 / time_factor)
        elif kda >= 4:
            score += int(8 / time_factor)
        elif kda >= 3:
            score += int(5 / time_factor)
        elif kda >= 2:
            score += int(3 / time_factor)

        # 击杀加分（大幅降低，受时长系数影响）
        if is_aram:
            # 大乱斗标准（击杀更频繁）
            if kills >= 20:
                score += int(10 / time_factor)
            elif kills >= 15:
                score += int(8 / time_factor)
            elif kills >= 12:
                score += int(6 / time_factor)
            elif kills >= 10:
                score += int(4 / time_factor)
            elif kills >= 8:
                score += int(3 / time_factor)
        else:
            # 排位/匹配标准
            if kills >= 15:
                score += int(10 / time_factor)
            elif kills >= 12:
                score += int(8 / time_factor)
            elif kills >= 10:
                score += int(6 / time_factor)
            elif kills >= 8:
                score += int(4 / time_factor)
            elif kills >= 6:
                score += int(3 / time_factor)
            elif kills >= 4:
                score += int(2 / time_factor)

        # 助攻加分（降低，受时长系数影响）
        if is_aram:
            if assists >= 30:
                score += int(6 / time_factor)
            elif assists >= 25:
                score += int(5 / time_factor)
            elif assists >= 20:
                score += int(4 / time_factor)
            elif assists >= 15:
                score += int(3 / time_factor)
        else:
            if assists >= 20:
                score += int(6 / time_factor)
            elif assists >= 15:
                score += int(5 / time_factor)
            elif assists >= 12:
                score += int(4 / time_factor)
            elif assists >= 10:
                score += int(3 / time_factor)

        # 胜利加分（小幅加分）
        if win:
            score += 5
        else:
            score -= 2

        # 死亡扣分（加重扣分，受时长系数影响）
        if is_aram:
            # 大乱斗标准
            if deaths >= 18:
                score -= int(25 * time_factor)
            elif deaths >= 15:
                score -= int(20 * time_factor)
            elif deaths >= 12:
                score -= int(15 * time_factor)
            elif deaths >= 10:
                score -= int(10 * time_factor)
            elif deaths >= 8:
                score -= int(6 * time_factor)
            elif deaths >= 6:
                score -= int(3 * time_factor)
        else:
            # 排位/匹配标准（更严格）
            if deaths >= 10:
                score -= int(30 * time_factor)
            elif deaths >= 8:
                score -= int(25 * time_factor)
            elif deaths >= 6:
                score -= int(20 * time_factor)
            elif deaths >= 5:
                score -= int(15 * time_factor)
            elif deaths >= 4:
                score -= int(10 * time_factor)
            elif deaths >= 3:
                score -= int(5 * time_factor)
            elif deaths >= 2:
                score -= int(2 * time_factor)

        # 参与度加分（降低权重，受时长系数影响）
        participation = kills + assists
        if is_aram:
            # 大乱斗标准
            if participation >= 50:
                score += int(8 / time_factor)
            elif participation >= 40:
                score += int(6 / time_factor)
            elif participation >= 35:
                score += int(5 / time_factor)
            elif participation >= 30:
                score += int(4 / time_factor)
            elif participation >= 25:
                score += int(3 / time_factor)
        else:
            if participation >= 30:
                score += int(8 / time_factor)
            elif participation >= 25:
                score += int(6 / time_factor)
            elif participation >= 20:
                score += int(4 / time_factor)
            elif participation >= 15:
                score += int(3 / time_factor)
            elif participation >= 12:
                score += int(2 / time_factor)

        # 补刀加分（大乱斗没有补刀，跳过此项）
        if not is_aram:
            # 补刀标准需要根据时长动态调整
            cs_per_minute = cs / duration_minutes if duration_minutes > 0 else 0
            if cs >= 250:
                score += int(8 / time_factor)
            elif cs >= 200:
                score += int(6 / time_factor)
            elif cs >= 150:
                score += int(4 / time_factor)
            elif cs >= 100:
                score += 2

        # 伤害加分（大乱斗伤害更高，标准调整）- 提高权重
        if is_aram:
            # 大乱斗标准
            if damage >= 60000:
                score += 20
            elif damage >= 50000:
                score += 15
            elif damage >= 40000:
                score += 12
            elif damage >= 30000:
                score += 8
            elif damage >= 25000:
                score += 5
            elif damage >= 20000:
                score += 3
        else:
            # 排位/匹配标准
            if damage >= 50000:
                score += 20
            elif damage >= 40000:
                score += 15
            elif damage >= 30000:
                score += 10
            elif damage >= 25000:
                score += 8
            elif damage >= 20000:
                score += 5
            elif damage >= 15000:
                score += 3
            elif damage >= 10000:
                score += 1

        # 视野加分（大乱斗没有视野，跳过此项）
        if not is_aram:
            if vision >= 50:
                score += 5
            elif vision >= 40:
                score += 3
            elif vision >= 30:
                score += 2

        return score

    def _get_level_info(self, score):
        """获取等级和颜色（提高门槛，避免躺赢被误判）"""
        if score < 85:
            return "牛马", "#9E9E9E"  # 灰色
        elif score < 95:
            return "下等马", "#FF5722"  # 橙红色
        elif score < 110:
            return "中等马", "#FF9800"  # 橙色
        elif score < 125:
            return "上等马", "#2196F3"  # 蓝色
        elif score < 150:
            return "小代", "#9C27B0"  # 紫色
        else:
            return "通天带", "#F44336"  # 红色

    def get_summoner_stats(self, summoner_name):
        """手动查询召唤师战绩"""
        try:
            summoner = self.lol_client.get_summoner_by_name(summoner_name)
            if not summoner:
                raise Exception("未找到该召唤师")

            summoner_id = summoner.get('summonerId')
            history = self.lol_client.get_match_history(summoner_id, count=20)
            stats = self._calculate_stats(history)

            return stats

        except Exception as e:
            self.error_occurred.emit(f"查询失败: {str(e)}")
            return None
