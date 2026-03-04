"""
自动接受对局模块
"""
import time
import threading
from PyQt5.QtCore import QObject, pyqtSignal


class AutoAcceptWorker(QObject):
    """自动接受对局工作线程"""

    # 信号定义
    status_changed = pyqtSignal(str)
    match_found = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, lol_client):
        super().__init__()
        self.lol_client = lol_client
        self.running = False
        self.thread = None

    def start_auto_accept(self):
        """启动自动接受"""
        if self.running:
            self.status_changed.emit("自动接受已在运行中")
            return

        self.running = True
        self.status_changed.emit("自动接受已启动，等待对局...")
        self.thread = threading.Thread(target=self._auto_accept_loop, daemon=True)
        self.thread.start()

    def stop_auto_accept(self):
        """停止自动接受"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        self.status_changed.emit("自动接受已停止")

    def _auto_accept_loop(self):
        """自动接受循环"""
        while self.running:
            try:
                # 检查是否有准备对局
                if self.lol_client.is_ready_check():
                    self.match_found.emit()
                    self.status_changed.emit("检测到对局，正在接受...")

                    # 自动接受
                    success = self.lol_client.accept_match()
                    if success:
                        self.status_changed.emit("✓ 对局已接受！")
                    else:
                        self.status_changed.emit("✗ 接受失败，请手动接受")

                    # 等待一段时间避免重复接受
                    time.sleep(5)

                time.sleep(0.5)  # 检查间隔

            except Exception as e:
                if self.running:
                    self.error_occurred.emit(f"错误: {str(e)}")
                time.sleep(2)

    def is_running(self):
        """检查是否正在运行"""
        return self.running
