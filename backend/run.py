"""一键启动脚本"""
import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=== 旅游业务管理系统后端启动 ===")
print()

# 安装依赖
print("正在检查依赖...")
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt', '-q'])

# 初始化数据库并启动
print("正在初始化数据库...")
from database import init_db, seed_data
init_db()
seed_data()

print("正在启动 Flask 服务...")
from app import app
app.run(debug=True, port=5000)
