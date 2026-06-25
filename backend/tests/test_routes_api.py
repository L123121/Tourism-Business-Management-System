"""路线与活动管理 API 集成测试

对应 PDF 第 19-21 页：属性测试和方法测试。
使用 Flask test_client 模拟 HTTP 请求，验证路由 CRUD 和活动管理功能。
"""

from tests import TourismTestCase


# ========================================================================
# 路线管理 API 测试
# ========================================================================

class TestRoutesAPI(TourismTestCase):
    """旅游路线 CRUD 相关 API"""

    def setUp(self):
        super().setUp()
        self.token = self.admin_token()

    # -------- 读取 --------

    def test_get_routes_list(self):
        """GET /api/routes —— 返回路线列表"""
        status, data = self.json_get('/api/routes', token=self.token)
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_get_routes_returns_all_fields(self):
        """返回的路线应包含关键字段"""
        _, data = self.json_get('/api/routes', token=self.token)
        route = data[0]
        self.assertIn('route_code', route)
        self.assertIn('route_name', route)
        self.assertIn('status', route)

    def test_get_route_by_code(self):
        """GET /api/routes/<code> —— 按编号获取路线"""
        status, data = self.json_get('/api/routes/R-001', token=self.token)
        self.assertEqual(status, 200)
        self.assertEqual(data['route_code'], 'R-001')
        self.assertIn('activities', data)
        self.assertIn('change_logs', data)

    def test_get_route_not_found(self):
        """不存在的路线应返回 404"""
        status, data = self.json_get('/api/routes/NONEXIST', token=self.token)
        self.assertEqual(status, 404)
        self.assertIn('error', data)

    # -------- 创建 --------

    def test_create_route_success(self):
        """POST /api/routes —— 创建新路线"""
        status, data = self.json_post('/api/routes', {
            'route_code': 'R-NEW-001',
            'route_name': '新路线',
            'description': '测试创建'
        }, token=self.token)
        self.assertEqual(status, 201)

        # 验证已持久化
        _, route = self.json_get('/api/routes/R-NEW-001', token=self.token)
        self.assertEqual(route['route_name'], '新路线')

    def test_create_route_missing_name(self):
        """缺少 route_name 时返回 400"""
        status, data = self.json_post('/api/routes', {
            'route_code': 'R-ERR-001'
        }, token=self.token)
        self.assertEqual(status, 400)

    def test_create_route_adds_change_log(self):
        """创建路线时应自动写入变更日志"""
        self.json_post('/api/routes', {
            'route_code': 'R-LOG-001',
            'route_name': '日志测试',
            'operator': '测试员'
        }, token=self.token)
        _, route = self.json_get('/api/routes/R-LOG-001', token=self.token)
        logs = route['change_logs']
        self.assertTrue(any('路线创建' in log['content'] for log in logs))

    # -------- 更新 --------

    def test_update_route(self):
        """PUT /api/routes/<code> —— 更新路线"""
        status, data = self.json_put('/api/routes/R-001', {
            'route_name': '云南更新版',
            'description': '更新后的描述'
        }, token=self.token)
        self.assertEqual(status, 200)

        _, route = self.json_get('/api/routes/R-001', token=self.token)
        self.assertEqual(route['route_name'], '云南更新版')

    def test_update_route_not_found(self):
        """更新不存在的路线返回 404"""
        status, data = self.json_put('/api/routes/NONEXIST', {
            'route_name': '不存在'
        }, token=self.token)
        self.assertEqual(status, 404)

    # -------- 取消 --------

    def test_cancel_route(self):
        """POST /api/routes/<code>/cancel —— 取消路线"""
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        resp = self.client.post('/api/routes/R-001/cancel',
                                json={'operator': '测试员'}, headers=headers)
        self.assertEqual(resp.status_code, 200)

        _, route = self.json_get('/api/routes/R-001', token=self.token)
        self.assertEqual(route['status'], '已取消')

    def test_cancel_route_adds_log(self):
        """取消路线时应写入变更日志"""
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        self.client.post('/api/routes/R-001/cancel', json={}, headers=headers)
        _, route = self.json_get('/api/routes/R-001', token=self.token)
        self.assertTrue(any('路线取消' in log['content']
                            for log in route['change_logs']))


# ========================================================================
# 旅游活动管理 API 测试
# ========================================================================

class TestActivitiesAPI(TourismTestCase):
    """旅游活动 CRUD 相关 API"""

    def setUp(self):
        super().setUp()
        self.token = self.admin_token()

    def test_get_activities_all(self):
        """GET /api/activities —— 返回活动列表"""
        status, data = self.json_get('/api/activities', token=self.token)
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_get_activities_by_route(self):
        """GET /api/activities?route_code=xxx —— 按路线筛选"""
        status, data = self.json_get('/api/activities?route_code=R-001', token=self.token)
        self.assertEqual(status, 200)
        for act in data:
            self.assertEqual(act['route_code'], 'R-001')

    def test_get_activities_empty_route(self):
        """筛选不存在路线的活动应返回空列表"""
        status, data = self.json_get('/api/activities?route_code=R-NONEXIST', token=self.token)
        self.assertEqual(status, 200)
        self.assertEqual(len(data), 0)

    def test_create_activity_success(self):
        """POST /api/activities —— 创建活动"""
        status, data = self.json_post('/api/activities', {
            'activity_code': 'A-TEST-001',
            'activity_name': '测试活动',
            'route_code': 'R-001',
            'description': '测试描述'
        }, token=self.token)
        self.assertEqual(status, 201)

    def test_create_activity_no_route(self):
        """为不存在的路线创建活动应失败"""
        status, data = self.json_post('/api/activities', {
            'activity_code': 'A-ERR-001',
            'activity_name': '无效',
            'route_code': 'R-NONEXIST'
        }, token=self.token)
        self.assertEqual(status, 400)

    def test_update_activity(self):
        """PUT /api/activities/<code> —— 更新活动"""
        status, data = self.json_put('/api/activities/A-001', {
            'activity_name': '更新后活动',
            'description': '新描述'
        }, token=self.token)
        self.assertEqual(status, 200)
