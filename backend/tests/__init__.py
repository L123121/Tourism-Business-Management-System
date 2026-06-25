"""测试基类

对应 PDF 第 18 页：setUp/tearDown 创建和销毁测试 fixture。
每个测试方法使用独立的临时数据库，确保测试隔离性。
"""

import os
import tempfile
import unittest
import database
from app import app


class TourismTestCase(unittest.TestCase):
    """旅游业务管理系统测试基类

    每个测试类使用一个临时 SQLite 数据库文件，测试类之间互不干扰。
    用法：继承此类，在子类中编写 test_ 开头的测试方法。
    """

    @classmethod
    def setUpClass(cls):
        """在所有测试方法前创建临时数据库文件"""
        cls.db_fd, cls.db_path = tempfile.mkstemp(suffix='_travel_test.db')
        database.DB_PATH = cls.db_path

    @classmethod
    def tearDownClass(cls):
        """在所有测试方法后清理临时数据库文件"""
        os.close(cls.db_fd)
        try:
            os.unlink(cls.db_path)
        except OSError:
            pass

    def setUp(self):
        """每个测试方法前重建数据库并注入种子数据
        注意：init_db() 使用 IF NOT EXISTS，seed_data() 检测到数据存在会跳过，
        因此必须手动清空所有表，确保每个测试用例从一致的初始状态开始。
        """
        database.init_db()  # 建表（如果已存在则为空操作）

        conn = database.get_db()
        # 按外键依赖逆序删除所有表数据
        for table in ['payment', 'participant', 'application', 'price',
                      'tour_group', 'activity', 'route_change_log', 'route', 'user']:
            conn.execute(f"DELETE FROM {table}")
        # 重置自增 ID 计数器，确保 seed_data 从已知 ID 开始
        conn.execute("DELETE FROM sqlite_sequence")
        conn.commit()
        conn.close()

        database.seed_data()
        self.client = app.test_client()

    # ---- 便捷 HTTP 请求方法 ----

    def json_get(self, url, token=None):
        """发送 GET 请求并返回 (状态码, JSON数据)"""
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = self.client.get(url, headers=headers)
        return resp.status_code, resp.get_json()

    def json_post(self, url, data, token=None):
        """发送 POST JSON 请求并返回 (状态码, JSON数据)"""
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = self.client.post(url, json=data, headers=headers)
        return resp.status_code, resp.get_json()

    def json_put(self, url, data, token=None):
        """发送 PUT JSON 请求并返回 (状态码, JSON数据)"""
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = self.client.put(url, json=data, headers=headers)
        return resp.status_code, resp.get_json()

    # ---- 认证辅助方法 ----

    def login(self, username='admin', password='Travel@2026'):
        """登录并返回 JWT Token"""
        resp = self.client.post('/api/login', json={
            'username': username,
            'password': password
        }, content_type='application/json')
        data = resp.get_json()
        return data.get('token')

    def admin_token(self):
        """获取管理员 token"""
        return self.login('admin', 'Travel@2026')

    def receptionist_token(self):
        """获取前台员工 token"""
        return self.login('zhangmin', 'Travel@2026')

    def collector_token(self):
        """获取催款员工 token"""
        return self.login('lihua', 'Travel@2026')

    def route_admin_token(self):
        """获取路线管理员 token"""
        return self.login('wanglei', 'Travel@2026')

    def accountant_token(self):
        """获取会计人员 token"""
        return self.login('zhaofang', 'Travel@2026')
