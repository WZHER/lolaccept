"""安全启动脚本，捕获所有异常"""
import sys
import traceback
from datetime import datetime

def main():
    try:
        # 导入主模块
        from main_window import main
        print(f"[{datetime.now()}] 启动程序...")
        main()
    except Exception as e:
        error_log = f"[{datetime.now()}] 程序崩溃!\n"
        error_log += f"错误类型: {type(e).__name__}\n"
        error_log += f"错误信息: {str(e)}\n"
        error_log += "\n=== 堆栈跟踪 ===\n"
        error_log += traceback.format_exc()

        # 打印到控制台
        print(error_log)

        # 保存到文件
        with open("crash_log.txt", "a", encoding="utf-8") as f:
            f.write(error_log + "\n" + "="*80 + "\n\n")

        # 显示错误对话框
        try:
            from PyQt5.QtWidgets import QApplication, QMessageBox
            app = QApplication(sys.argv) if QApplication.instance() is None else QApplication.instance()
            QMessageBox.critical(None, "程序崩溃",
                f"程序发生错误！\n\n错误信息已保存到 crash_log.txt\n\n{type(e).__name__}: {str(e)}")
        except:
            input("按回车键退出...")

if __name__ == '__main__':
    main()
