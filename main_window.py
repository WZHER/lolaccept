"""
主窗口界面 - 重构版
"""
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QGroupBox, QMessageBox, QHeaderView, QScrollArea, QGridLayout, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QFont, QColor, QPixmap
import config

from lol_api import LOLClient
from auto_accept import AutoAcceptWorker
from team_stats import TeamStatsWorker


def get_resource_path(relative_path):
    """
    获取资源文件的绝对路径
    支持开发环境和打包后的exe环境
    """
    try:
        # PyInstaller打包后的临时目录
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class SwitchButton(QWidget):
    """自定义开关按钮 - 饿了么风格"""
    stateChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(56, 28)
        self._checked = False
        self.setCursor(Qt.PointingHandCursor)
        self._init_ui()
        self._update_style()

    def _init_ui(self):
        self._indicator = QLabel(self)
        self._indicator.setFixedSize(24, 24)
        self._update_indicator_pos()
        self._update_face()

    def _update_face(self):
        """更新表情"""
        if self._checked:
            # 开启状态：笑脸
            self._indicator.setText("😊")
            self._indicator.setAlignment(Qt.AlignCenter)
            self._indicator.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    background-color: transparent;
                    border: none;
                }
            """)
        else:
            # 关闭状态：哭脸
            self._indicator.setText("😢")
            self._indicator.setAlignment(Qt.AlignCenter)
            self._indicator.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    background-color: transparent;
                    border: none;
                }
            """)

    def _update_style(self):
        """更新开关样式"""
        # 先更新表情
        self._update_face()

        # 再设置整体样式
        if self._checked:
            # 激活状态 - 饿了么橙色
            self.setStyleSheet("""
                SwitchButton {
                    background-color: #FF6B00;
                    border-radius: 14px;
                    border: 2px solid #FF6B00;
                }
            """)
        else:
            # 关闭状态 - 浅灰色背景
            self.setStyleSheet("""
                SwitchButton {
                    background-color: #E0E0E0;
                    border-radius: 14px;
                    border: 2px solid #E0E0E0;
                }
            """)

    def _update_indicator_pos(self):
        if self._checked:
            self._indicator.move(28, 2)
        else:
            self._indicator.move(2, 2)

    def mousePressEvent(self, event):
        self.setChecked(not self._checked)
        self.stateChanged.emit(self._checked)

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self._update_indicator_pos()
            self._update_style()


class PlayerCard(QFrame):
    """玩家卡片组件 - 纵向布局"""
    def __init__(self, name, level, kda, win_rate, games, recent_matches=None):
        super().__init__()
        # 稍微加宽，保证信息展示更完整
        self.setFixedWidth(210)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 10px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        # 玩家名字和评级在同一行
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        # 玩家名字
        name_label = QLabel(name)
        name_label.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        name_label.setStyleSheet("color: #333;")
        header_row.addWidget(name_label)

        header_row.addStretch()

        # 总体评级
        level_color = self._get_level_color(level)
        level_label = QLabel(level)
        level_label.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        level_label.setStyleSheet(f"color: {level_color};")
        header_row.addWidget(level_label)

        layout.addLayout(header_row)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #e0e0e0;")
        layout.addWidget(line)

        # 最近战绩列表（去掉标题）
        matches_container = QWidget()
        matches_layout = QVBoxLayout(matches_container)
        matches_layout.setSpacing(4)
        matches_layout.setContentsMargins(0, 0, 0, 0)

        if recent_matches:
            # 默认展示最近 10 场战绩（如果有这么多）
            for match in recent_matches[:10]:
                match_row = QHBoxLayout()
                match_row.setSpacing(8)
                match_row.setContentsMargins(0, 0, 0, 0)

                # 创建带边框的容器
                match_frame = QFrame()
                match_frame.setStyleSheet("""
                    QFrame {
                        border: 1px solid #e0e0e0;
                        border-radius: 4px;
                        padding: 4px;
                        background-color: #fafafa;
                    }
                """)
                match_layout = QHBoxLayout(match_frame)
                match_layout.setSpacing(8)
                match_layout.setContentsMargins(6, 4, 6, 4)

                # 英雄名字
                hero_label = QLabel(match.get('hero', '未知'))
                hero_label.setStyleSheet("color: #666; font-size: 10px;")
                match_layout.addWidget(hero_label)

                # KDA
                kda_label = QLabel(match.get('kda', '0/0/0'))
                kda_label.setStyleSheet("color: #666; font-size: 10px;")
                match_layout.addWidget(kda_label)

                # 胜负
                result = match.get('result', '未知')
                result_color = "#4CAF50" if result == '胜利' else "#f44336" if result == '失败' else "#999"
                result_label = QLabel(result)
                result_label.setStyleSheet(f"color: {result_color}; font-size: 10px; font-weight: bold;")
                match_layout.addWidget(result_label)

                match_layout.addStretch()

                match_row.addWidget(match_frame)
                matches_layout.addLayout(match_row)
        else:
            no_match_label = QLabel("暂无战绩")
            no_match_label.setStyleSheet("color: #999; font-size: 9px;")
            no_match_label.setAlignment(Qt.AlignCenter)
            matches_layout.addWidget(no_match_label)

        matches_container.setLayout(matches_layout)
        layout.addWidget(matches_container)
        layout.addStretch()

    def _get_level_color(self, level):
        color_map = {
            "牛马": "#9E9E9E",
            "下等马": "#FF5722",
            "中等马": "#FF9800",
            "上等马": "#2196F3",
            "小代": "#9C27B0",
            "通天带": "#F44336"
        }
        return color_map.get(level, "#999999")


class MainWindow(QMainWindow):
    """主窗口 - 重构版"""

    match_detail_loaded = pyqtSignal(object, object)

    def __init__(self):
        super().__init__()
        self.lol_client = None
        self.auto_accept_worker = None
        self.team_stats_worker = None
        self.summoner_info = None

        self.match_detail_loaded.connect(self.update_game_detail)

        self.init_ui()
        self.connect_to_lol()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(config.WINDOW_TITLE)
        # 使用固定窗口大小，避免被拉伸，默认能展示 5 个队友卡片
        self.setFixedSize(1400, 720)
        print(f"[DEBUG] Window fixed size: {self.width()}x{self.height()}")

        # 初始化网络管理器
        from PyQt5.QtNetwork import QNetworkAccessManager
        self.nam = QNetworkAccessManager()

        # 整体样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f7fa;
            }
            QWidget {
                font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
            }
        """)

        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局：水平分割
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ==================== 左侧 B 区域 ====================
        # 小侧边栏，显示头像+ID+开关
        left_panel = self._create_left_panel()
        main_layout.addWidget(left_panel)

        # ==================== 右侧 C 区域 ====================
        # 主内容区域，上下分割
        right_panel = self._create_right_panel()
        main_layout.addWidget(right_panel)

    def _create_left_panel(self):
        """创建左侧面板 (B区域)"""
        panel = QWidget()
        panel.setFixedWidth(220)
        panel.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-right: 1px solid #e6f4ff;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 30, 20, 30)
        layout.setAlignment(Qt.AlignTop)

        # 头像
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(110, 110)
        self.avatar_label.setStyleSheet("""
            QLabel {
                border: 3px solid #e0e0e0;
                border-radius: 55px;
                background-color: #f5f5f5;
            }
        """)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.avatar_label, 0, Qt.AlignCenter)

        # 名字
        self.name_label = QLabel("加载中...")
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setFont(QFont("Microsoft YaHei", 15, QFont.Bold))
        self.name_label.setStyleSheet("color: #333; margin-top: 5px;")
        layout.addWidget(self.name_label)

        # 等级标签 - 移除"召唤师等级"标签，只显示数字
        self.level_value_label = QLabel("--")
        self.level_value_label.setAlignment(Qt.AlignCenter)
        self.level_value_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        self.level_value_label.setStyleSheet("color: #FF6B00; margin-top: 5px;")
        layout.addWidget(self.level_value_label, 0, Qt.AlignCenter)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #e0e0e0; max-width: 120px;")
        layout.addWidget(line, 0, Qt.AlignCenter)

        # 自动接受开关 - 饿了么风格
        aa_label = QLabel("自动接受")
        aa_label.setAlignment(Qt.AlignCenter)
        aa_label.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        aa_label.setStyleSheet("color: #333; margin-bottom: 8px;")
        layout.addWidget(aa_label)

        self.aa_switch = SwitchButton()
        self.aa_switch.stateChanged.connect(self._on_aa_switch_changed)
        layout.addWidget(self.aa_switch, 0, Qt.AlignCenter)

        # 状态指示
        self.aa_status_label = QLabel("未启动")
        self.aa_status_label.setAlignment(Qt.AlignCenter)
        self.aa_status_label.setStyleSheet("color: #999; font-size: 11px; margin-top: 8px;")
        layout.addWidget(self.aa_status_label)

        layout.addStretch()

        return panel

    def _create_right_panel(self):
        """创建右侧面板 (C区域)"""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: #f5f7fa;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # ==================== D区域：队友信息 ====================
        d_group = self._create_team_section("队友信息", "#2196F3")
        layout.addWidget(d_group, 1)

        return panel

    def _create_team_section(self, title, color):
        """创建队友战绩区域 (D区域)"""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 13px;
                color: {color};
                border: none;
                margin-top: 6px;
                padding-top: 18px;  /* 给标题留出空间，避免内容遮挡文字 */
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 4px 12px;
                border-radius: 14px;
                background-color: #e6f4ff;
            }}
        """)

        outer_layout = QVBoxLayout(group)
        outer_layout.setSpacing(8)

        # 内层卡片容器，做成饿了么风格的白色卡片区域
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
            }
        """)
        layout = QVBoxLayout(container)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        # 使用滚动区域和水平布局显示5个玩家卡片
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        team_widget = QWidget()
        team_layout = QHBoxLayout(team_widget)
        team_layout.setSpacing(12)
        team_layout.setContentsMargins(4, 4, 4, 4)

        # 创建5个占位卡片
        self.team_cards = []
        for i in range(5):
            card = PlayerCard(f"召唤师{i+1}", "N/A", "0/0/0", "0%", 0)
            team_layout.addWidget(card)
            self.team_cards.append(card)

        team_layout.addStretch()
        scroll.setWidget(team_widget)
        layout.addWidget(scroll)

        outer_layout.addWidget(container)

        return group


    def connect_to_lol(self):
        """连接到LOL客户端"""
        try:
            self.lol_client = LOLClient()
            summoner = self.lol_client.get_summoner_info()

            if summoner:
                self.update_summoner_card(summoner)
            else:
                self.name_label.setText("连接失败")

            # 初始化工作线程
            self.auto_accept_worker = AutoAcceptWorker(self.lol_client)
            self.auto_accept_worker.status_changed.connect(self._on_aa_status)
            self.auto_accept_worker.error_occurred.connect(self.show_error)

            self.team_stats_worker = TeamStatsWorker(self.lol_client)
            self.team_stats_worker.stats_ready.connect(self._on_team_stats_ready)
            self.team_stats_worker.status_changed.connect(self._on_team_status)
            self.team_stats_worker.error_occurred.connect(self.show_error)

            # 启动队友监测
            self.team_stats_worker.start_monitoring()

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()

            self.name_label.setText("连接失败")
            self.name_label.setStyleSheet("color: #f44336;")

            error_msg = f"无法连接到LOL客户端\n\n"
            error_msg += f"错误详情: {str(e)}\n\n"
            error_msg += f"请检查：\n"
            error_msg += f"1. LOL客户端是否已启动\n"
            error_msg += f"2. 是否已登录游戏账号\n"
            error_msg += f"3. 客户端是否完全加载完成\n\n"
            error_msg += f"技术信息：\n{error_detail}"

            QMessageBox.critical(self, "连接失败", error_msg)

    def update_summoner_card(self, summoner):
        """更新召唤师卡片信息"""
        if not summoner:
            return

        self.summoner_info = summoner

        # 更新名字 - 只使用 gameName
        name = summoner.get('gameName', '未知')
        
        self.name_label.setText(name)
        self.name_label.setStyleSheet("color: #333;")

        # 更新等级
        level = summoner.get('summonerLevel', 0)
        self.level_value_label.setText(f"LV.{level}")

        # 加载头像
        icon_id = summoner.get('profileIconId', 0)
        if icon_id > 0:
            self.load_avatar(icon_id)

    def load_avatar(self, icon_id):
        """加载召唤师头像"""
        try:
            from PyQt5.QtNetwork import QNetworkRequest
            from PyQt5.QtCore import QUrl

            url = QUrl(f"{config.ICON_BASE_URL}{icon_id}.png")
            reply = self.nam.get(QNetworkRequest(url))
            reply.finished.connect(lambda r=reply: self._on_avatar_loaded(r))
        except Exception as e:
            print(f"加载头像失败: {e}")

    def _on_avatar_loaded(self, reply):
        """头像加载完成"""
        try:
            if reply and reply.error() == 0:
                data = reply.readAll()
                pixmap = QPixmap()
                if pixmap.loadFromData(data):
                    scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.avatar_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"头像显示失败: {e}")
        finally:
            if reply:
                reply.deleteLater()

    def _on_aa_switch_changed(self, checked):
        """自动接受开关切换"""
        if checked:
            if self.auto_accept_worker:
                self.auto_accept_worker.start_auto_accept()
                self.aa_status_label.setText("已启动")
                self.aa_status_label.setStyleSheet("color: #4CAF50; font-size: 11px; margin-top: 5px;")
        else:
            if self.auto_accept_worker:
                self.auto_accept_worker.stop_auto_accept()
                self.aa_status_label.setText("已停止")
                self.aa_status_label.setStyleSheet("color: #999; font-size: 11px; margin-top: 5px;")

    def _on_aa_status(self, msg):
        """自动接受状态更新"""
        print(f"[AA] {msg}")

    def _on_team_status(self, msg):
        """队伍状态更新"""
        pass

    def _on_team_stats_ready(self, team_data):
        """队友战绩数据就绪"""
        if not team_data:
            return

        # 更新D区域的队友卡片
        for i, data in enumerate(team_data):
            if i >= 5 or i >= len(self.team_cards):
                break

            # 获取旧卡片的父容器
            old_card = self.team_cards[i]
            parent_widget = old_card.parentWidget()

            if parent_widget:
                parent_layout = parent_widget.layout()
                if parent_layout:
                    # 移除旧卡片但不删除（避免多次更新时问题）
                    parent_layout.removeWidget(old_card)
                    old_card.setParent(None)
                    old_card.deleteLater()

            # 创建新卡片
            new_card = PlayerCard(
                data['name'],
                data.get('level', 'N/A'),
                data['kda'],
                data['win_rate'],
                data['games'],
                data.get('recent_matches', [])
            )

            # 重新添加到布局
            if parent_widget:
                parent_layout = parent_widget.layout()
                if parent_layout:
                    parent_layout.insertWidget(i, new_card)

            self.team_cards[i] = new_card

    def show_error(self, error_msg):
        """显示错误信息"""
        QMessageBox.warning(self, "错误", error_msg)

    def update_game_detail(self, game_data, full_detail):
        """更新对局详情（保留兼容）"""
        pass


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
