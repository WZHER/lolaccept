"""
英雄联盟LCU API封装
"""
import requests
import json
from pathlib import Path
import urllib3
import time
import psutil

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class LOLClient:
    """英雄联盟客户端API接口"""

    def __init__(self):
        self.base_url = None
        self.port = None
        self.auth_token = None
        # 配置session，禁用SSL验证
        self.session = requests.Session()
        self.session.verify = False
        self._connect()

    def _connect(self):
        """连接到LOL客户端"""
        import subprocess
        import re

        method1_error = None
        method2_error = None

        # 方法1: 使用psutil查找进程命令行（推荐方法）
        try:
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    if proc.info['name'] == 'LeagueClientUx.exe':
                        cmdline = proc.info['cmdline']
                        if cmdline and len(cmdline) > 0:
                            cmdline_str = ' '.join(cmdline)

                            # 使用正则提取token
                            token_match = re.search(r'--remoting-auth-token[= ]["\']?([a-zA-Z0-9_-]+)', cmdline_str)
                            if not token_match:
                                raise Exception("未找到认证令牌 (--remoting-auth-token)")

                            # 使用正则提取端口
                            port_match = re.search(r'--app-port[= ]["\']?([0-9]+)', cmdline_str)
                            if not port_match:
                                raise Exception("未找到应用程序端口 (--app-port)")

                            self.port = int(port_match.group(1))
                            self.auth_token = token_match.group(1)
                            # 使用带认证的URL格式
                            self.base_url = f"https://riot:{self.auth_token}@127.0.0.1:{self.port}"

                            return
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            raise Exception("未找到英雄联盟客户端进程 (LeagueClientUx.exe)")

        except Exception as e:
            method1_error = str(e)
            print(f"方法1失败: {e}")

        # 方法2: 尝试读取lockfile（备选方案）
        try:
            lockfile_paths = [
                Path.home() / "AppData" / "Roaming" / "League of Legends" / "lockfile",
                Path.home() / "AppData" / "Local" / "Riot Games" / "Riot Client" / "Config" / "lockfile",
            ]

            # 添加可能的国服路径
            for drive in ['C', 'D', 'E']:
                for path in [
                    f"{drive}:\\腾讯游戏\\英雄联盟",
                    f"{drive}:\\Program Files\\腾讯游戏\\英雄联盟",
                    f"{drive}:\\Riot Games\\League of Legends"
                ]:
                    lockfile_paths.append(Path(path) / "lockfile")

            found_lockfile = False
            for lockfile_path in lockfile_paths:
                if lockfile_path.exists():
                    found_lockfile = True
                    with open(lockfile_path, 'r') as f:
                        content = f.read().strip().split(':')

                    self.port = int(content[2])
                    self.auth_token = content[3]
                    self.base_url = f"https://127.0.0.1:{self.port}"
                    return

            if not found_lockfile:
                raise Exception("未找到lockfile文件")

        except Exception as e:
            method2_error = str(e)
            print(f"方法2失败: {e}")

        # 构建详细的错误信息
        error_msg = "无法连接到LOL客户端\n\n"
        error_msg += "失败详情：\n"
        if method1_error:
            error_msg += f"• 方法1（进程命令行）失败: {method1_error}\n"
        if method2_error:
            error_msg += f"• 方法2（lockfile读取）失败: {method2_error}\n"
        error_msg += "\n可能原因：\n"
        error_msg += "1. LOL客户端未启动\n"
        error_msg += "2. 客户端未登录账号\n"
        error_msg += "3. 客户端进程被管理员权限阻止\n"
        error_msg += "4. 客户端正在更新或重启中"

        raise Exception(error_msg)

    def _encode_auth(self, token):
        """编码认证信息（已不再使用）"""
        import base64
        return base64.b64encode(f"riot:{token}".encode()).decode()

    def _encode_auth(self, token):
        """编码认证信息"""
        import base64
        return base64.b64encode(f"riot:{token}".encode()).decode()

    def get_summoner_info(self):
        """获取召唤师信息"""
        try:
            response = self.session.get(f"{self.base_url}/lol-summoner/v1/current-summoner")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取召唤师信息失败: {e}")
            return None

    def accept_match(self):
        """自动接受对局"""
        try:
            response = self.session.post(f"{self.base_url}/lol-matchmaking/v1/ready-check/accept")
            # 200和204都是成功的状态码
            return response.status_code in [200, 204]
        except Exception as e:
            print(f"接受对局失败: {e}")
            return False

    def get_current_match(self):
        """获取当前对局信息"""
        try:
            response = self.session.get(f"{self.base_url}/lol-lobby/v2/lobby")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取对局信息失败: {e}")
            return None

    def get_champ_select_session(self):
        """获取英雄选择阶段信息"""
        try:
            response = self.session.get(f"{self.base_url}/lol-champ-select/v1/session")

            if response.status_code == 404:
                return None

            response.raise_for_status()
            data = response.json()

            return data
        except Exception as e:
            print(f"[DEBUG] 获取选人信息异常: {e}")
            return None

    def is_matchmaking_active(self):
        """检查是否正在匹配"""
        try:
            response = self.session.get(f"{self.base_url}/lol-matchmaking/v1/search")
            return response.status_code == 200
        except:
            return False

    def is_ready_check(self):
        """检查是否有准备对局"""
        try:
            response = self.session.get(f"{self.base_url}/lol-matchmaking/v1/ready-check")
            response.raise_for_status()
            data = response.json()
            return data.get('state') == 'InProgress'
        except:
            return False

    def get_summoner_by_name(self, summoner_name):
        """根据召唤师名称获取信息"""
        try:
            response = self.session.get(f"{self.base_url}/lol-summoner/v1/summoners-by-name/{summoner_name}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"查询召唤师失败: {e}")
            return None

    def get_ranked_stats(self):
        """获取排位信息 - 支持多种API路径"""
        # 尝试多种可能的API路径
        api_paths = [
            '/lol-ranked/v1/ranked-stats',
            '/lol-league/v1/ranked-stats',
            '/lol/league/v1/rankedstats',
            '/lol/league/v2/rankedstats'
        ]

        for path in api_paths:
            try:
                response = self.session.get(f"{self.base_url}{path}")
                if response.status_code == 200:
                    data = response.json()
                    ranked_info = self._parse_ranked_data(data)
                    if ranked_info:
                        return ranked_info
            except Exception as e:
                print(f"尝试路径 {path} 失败: {e}")
                continue

        # 如果以上都失败，尝试从召唤师接口获取
        try:
            summoner = self.get_summoner_info()
            if summoner:
                summoner_id = summoner.get('summonerId')
                if summoner_id:
                    return self._get_league_info(summoner_id)
        except Exception as e:
            print(f"从召唤师获取排位失败: {e}")

        return None

    def _parse_ranked_data(self, data):
        """解析排位数据"""
        ranked_info = {}

        # 尝试不同的数据结构
        queue_map = data.get('queueMap', {})
        if not queue_map:
            # 尝试直接的数据结构
            leagues = data.get('leagues', [])
            if leagues:
                for league in leagues:
                    queue_type = league.get('queueType', '')
                    self._add_ranked_info(ranked_info, queue_type, league)
                return ranked_info

        # 单双排
        solo = queue_map.get('RANKED_SOLO_5x5', {})
        if solo:
            self._add_ranked_info(ranked_info, 'solo', solo)

        # 灵活排位
        flex = queue_map.get('RANKED_FLEX_SR', {})
        if flex:
            self._add_ranked_info(ranked_info, 'flex', flex)

        # 云顶之弈
        tft = queue_map.get('RANKED_TFT', {})
        if not tft:
            tft = queue_map.get('RANKED_TFT_TURBO', {})
        if not tft:
            tft = queue_map.get('RANKED_TFT_DOUBLE_UP', {})
        if tft:
            self._add_ranked_info(ranked_info, 'tft', tft)

        return ranked_info if ranked_info else None

    def _add_ranked_info(self, ranked_info, key, data):
        """添加排位信息"""
        tier = data.get('tier', '')
        division = data.get('division', '')
        wins = data.get('wins', 0)
        losses = data.get('losses', 0)
        lp = data.get('leaguePoints', 0)

        ranked_info[key] = {
            'tier': tier,
            'division': division,
            'wins': wins,
            'losses': losses,
            'lp': lp,
            'total': wins + losses
        }

    def _get_league_info(self, summoner_id):
        """通过召唤师ID获取排位信息"""
        try:
            response = self.session.get(f"{self.base_url}/lol-league/v2/leagues/by-summoner/{summoner_id}")
            if response.status_code == 200:
                leagues = response.json()
                ranked_info = {}

                for league in leagues:
                    queue_type = league.get('queueType', '')
                    tier = league.get('tier', '')
                    rank = league.get('rank', '')
                    wins = league.get('wins', 0)
                    losses = league.get('losses', 0)
                    lp = league.get('leaguePoints', 0)

                    if queue_type == 'RANKED_SOLO_5x5':
                        ranked_info['solo'] = {
                            'tier': tier,
                            'division': rank,
                            'wins': wins,
                            'losses': losses,
                            'lp': lp,
                            'total': wins + losses
                        }
                    elif queue_type == 'RANKED_FLEX_SR':
                        ranked_info['flex'] = {
                            'tier': tier,
                            'division': rank,
                            'wins': wins,
                            'losses': losses,
                            'lp': lp,
                            'total': wins + losses
                        }

                return ranked_info if ranked_info else None
        except Exception as e:
            print(f"获取排位信息失败: {e}")

        return None

    def get_tft_ranked_stats(self, summoner_id=None):
        """获取云顶之弈排位信息"""
        try:
            if summoner_id is None:
                summoner = self.get_summoner_info()
                if not summoner:
                    return None
                summoner_id = summoner.get('summonerId')

            # 尝试多种TFT API路径
            tft_paths = [
                f'/lol-competitive/v0/highlander-guest/player/{summoner_id}/tft',
                f'/tft-ranked/v1/ranked-data/{summoner_id}',
                f'/lol-chat/v1/me',  # 从个人信息中获取
            ]

            for path in tft_paths:
                try:
                    response = self.session.get(f"{self.base_url}{path}")
                    if response.status_code == 200:
                        data = response.json()

                        # 尝试从不同数据结构中提取TFT信息
                        tft_data = self._extract_tft_data(data)
                        if tft_data:
                            return tft_data
                except:
                    continue

            return None

        except Exception as e:
            print(f"获取云顶排位失败: {e}")
            return None

    def _extract_tft_data(self, data):
        """从数据中提取云顶之弈信息"""
        # 尝试从当前召唤师信息中获取
        if isinstance(data, dict):
            # 检查是否有summonerId和相关的rank信息
            ranked_data = data.get('rankedData', {})
            if ranked_data:
                return self._parse_tft_ranked(ranked_data)

        return None

    def _parse_tft_ranked(self, data):
        """解析TFT排位数据"""
        tier = data.get('tier', '')
        rank = data.get('rank', '')
        wins = data.get('wins', 0)
        losses = data.get('losses', 0)
        lp = data.get('leaguePoints', 0)

        if not tier or tier == 'UNRANKED':
            return None

        return {
            'tier': tier,
            'division': rank,
            'wins': wins,
            'losses': losses,
            'lp': lp,
            'total': wins + losses
        }

    def get_match_history(self, puuid, count=10):
        """获取对局历史"""
        try:
            response = self.session.get(
                f"{self.base_url}/lol-match-history/v1/products/lol/{puuid}/matches",
                params={'begIndex': 0, 'endIndex': count}
            )

            response.raise_for_status()
            data = response.json()

            return data
        except Exception as e:
            return None

    def get_match_detail(self, game_id):
        """通过游戏ID获取对局详情"""
        try:
            # 尝试多种可能的对局详情API路径
            paths = [
                f"/lol-match-history/v1/games/{game_id}",
                f"/lol-spectator/v1/spectator/ended-game/{game_id}",
            ]

            for path in paths:
                try:
                    response = self.session.get(f"{self.base_url}{path}")

                    if response.status_code == 200:
                        data = response.json()
                        return data
                except Exception as e:
                    continue

            return None

        except Exception as e:
            return None

    def search_summoner(self, name):
        """搜索召唤师（支持模糊搜索）"""
        # 尝试多种API路径
        api_paths = [
            ('/lol-summoner/v2/summoners/names', 'POST'),
            ('/lol-summoner/v1/summoners-by-name/' + name, 'GET'),
            ('/lol-summoner/v4/summoners/by-name/' + name, 'GET'),
        ]

        for endpoint, method in api_paths:
            try:
                url = f"{self.base_url}{endpoint}"

                if method == 'POST':
                    response = self.session.post(url, json=[name])
                else:
                    response = self.session.get(url)

                if response.status_code == 200:
                    if method == 'POST':
                        summoners = response.json()
                        if summoners and len(summoners) > 0:
                            return summoners[0]
                    else:
                        summoner = response.json()
                        if summoner:
                            return summoner

            except Exception as e:
                continue

        return None
