# LOL辅助工具

一个基于Python + PyQt5开发的英雄联盟辅助工具，支持自动接受对局、战绩查询和队友战绩展示功能。

## 功能特性

- ✅ 自动接受对局
- ✅ 查询召唤师战绩
- ✅ 选人阶段展示队友近期战绩
- ✅ 美观的图形化界面
- ✅ 轻量级，打包后体积约30-50MB

## 安装步骤

### 1. 安装Python

确保已安装Python 3.8或更高版本：
```bash
python --version
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行程序

```bash
python main_window.py
```

## 使用说明

### 自动接受对局
1. 确保LOL客户端正在运行并已登录
2. 启动本程序
3. 点击"启动自动接受"按钮
4. 进入排位赛大厅，程序会自动检测并接受对局

### 查询战绩
1. 程序启动后会自动读取当前登录账号
2. 点击"查询战绩"按钮
3. 查看近期20场战绩统计

### 队友战绩
1. 进入英雄选择阶段
2. 点击"开始监测"按钮
3. 程序会自动获取并显示队友的近期战绩
4. 根据胜率显示不同颜色（绿色≥60%，橙色≥50%，红色<50%）

## 打包为EXE

使用PyInstaller打包：

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "LOL辅助工具" main_window.py
```

打包后的EXE文件位于`dist`目录。

## 注意事项

- 必须先启动LOL客户端并登录
- 本工具仅用于辅助，请遵守游戏规则
- 使用第三方API可能存在不稳定因素
- 建议仅用于排位赛，避免在匹配模式使用

## 项目结构

```
lol-symbol/
├── config.py           # 配置文件
├── lol_api.py          # LCU API封装
├── auto_accept.py      # 自动接受模块
├── team_stats.py       # 队友战绩模块
├── match_history.py    # 战绩查询模块
├── main_window.py      # 主窗口界面
├── requirements.txt    # 依赖列表
└── README.md          # 说明文档
```

## 技术说明

### LCU API

本工具通过LOL客户端的本地API（LCU API）实现功能：
- 读取lockfile文件获取认证信息
- 使用RESTful API与LOL客户端通信

### 原理

- **自动接受**：轮询检查ready-check状态，发现对局时调用accept接口
- **战绩查询**：通过match-history API获取历史对局数据
- **队友战绩**：champ-select阶段获取队友信息，然后查询其历史战绩

## 开发者

本项目使用Python + PyQt5开发，易于维护和扩展。

如有问题或建议，欢迎反馈。
