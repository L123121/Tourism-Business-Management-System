"""申请管理及相关 API 集成测试

对应 PDF 第 21-30 页：方法测试（set/get/操作验证）。
覆盖最复杂的业务流：旅游团管理、价格发布约束、申请创建/取消、
参加者管理、余款支付。
"""

from tests import TourismTestCase


# ========================================================================
# 旅游团管理 API 测试
# ========================================================================

class TestGroupsAPI(TourismTestCase):
    """旅游团 CRUD 相关 API"""

    def setUp(self):
        super().setUp()
        self.token = self.admin_token()

    def test_get_groups_list(self):
        """GET /api/groups —— 返回旅游团列表"""
        status, data = self.json_get('/api/groups', token=self.token)
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_get_groups_by_status(self):
        """GET /api/groups?status=已开放 —— 按状态筛选"""
        status, data = self.json_get('/api/groups?status=已开放', token=self.token)
        self.assertEqual(status, 200)
        for g in data:
            self.assertEqual(g['status'], '已开放')

    def test_get_groups_by_status_empty(self):
        """筛选不存在状态的旅游团"""
        status, data = self.json_get('/api/groups?status=已完成', token=self.token)
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)

    def test_get_group_by_code(self):
        """GET /api/groups/<code> —— 获取单个旅游团"""
        status, data = self.json_get('/api/groups/YN-20260615', token=self.token)
        self.assertEqual(status, 200)
        self.assertEqual(data['group_code'], 'YN-20260615')
        self.assertIn('activity_name', data)
        self.assertIn('route_name', data)

    def test_get_group_not_found(self):
        """不存在的旅游团返回 404"""
        status, data = self.json_get('/api/groups/NONEXIST', token=self.token)
        self.assertEqual(status, 404)
        self.assertIn('error', data)

    def test_create_group_success(self):
        """POST /api/groups —— 创建旅游团"""
        status, data = self.json_post('/api/groups', {
            'group_code': 'G-TEST-001',
            'activity_code': 'A-001',
            'departure_date': '2026-08-01',
            'deadline': '2026-07-15',
            'capacity': 30
        }, token=self.token)
        self.assertEqual(status, 201)


# ========================================================================
# 价格管理 API 测试 —— 核心业务规则
# ========================================================================

class TestPricesAPI(TourismTestCase):
    """价格设定、发布、修改约束 API"""

    def setUp(self):
        super().setUp()
        self.token = self.admin_token()

    def test_get_prices_list(self):
        """GET /api/prices —— 返回价格列表"""
        status, data = self.json_get('/api/prices', token=self.token)
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)

    def test_get_price_by_group(self):
        """GET /api/prices/<group_code> —— 获取指定团价格"""
        status, data = self.json_get('/api/prices/YN-20260615', token=self.token)
        self.assertEqual(status, 200)
        self.assertEqual(data['group_code'], 'YN-20260615')
        self.assertIn('adult_price', data)
        self.assertIn('is_published', data)

    def test_get_price_not_set(self):
        """未设定价格的旅游团返回 404"""
        status, data = self.json_get('/api/prices/YN-20260510', token=self.token)
        self.assertEqual(status, 404)
        self.assertIn('error', data)

    def test_set_price_new(self):
        """为未设定价格的旅游团设置价格"""
        status, data = self.json_put('/api/prices/YN-20260510', {
            'adult_price': 3000,
            'child_price': 2000,
            'discount': '早鸟优惠'
        }, token=self.token)
        self.assertEqual(status, 200)

    def test_publish_price_success(self):
        """POST /api/prices/<code>/publish —— 发布价格"""
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        resp = self.client.post('/api/prices/HN-20260720/publish', headers=headers)
        self.assertEqual(resp.status_code, 200)

    def test_publish_unset_price_fails(self):
        """发布未设定的价格应失败"""
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        resp = self.client.post('/api/prices/YN-20260510/publish', headers=headers)
        self.assertEqual(resp.status_code, 400)
        self.assertIn('请先设定价格', resp.get_json()['error'])

    def test_double_publish_fails(self):
        """重复发布价格应失败"""
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        self.client.post('/api/prices/YN-20260615/publish', headers=headers)
        resp = self.client.post('/api/prices/YN-20260615/publish', headers=headers)
        self.assertEqual(resp.status_code, 400)

    # ---- 核心业务规则：价格发布后不可修改 ----

    def test_modify_after_publish_forbidden(self):
        """价格已公开，修改应拒绝（核心约束）"""
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        self.client.post('/api/prices/YN-20260615/publish', headers=headers)
        status, data = self.json_put('/api/prices/YN-20260615', {
            'adult_price': 9999,
            'child_price': 8888
        }, token=self.token)
        self.assertEqual(status, 400)
        self.assertIn('不可修改', data['error'])

    def test_modify_before_publish_allowed(self):
        """发布前可以修改价格"""
        status, data = self.json_put('/api/prices/HN-20260720', {
            'adult_price': 3600,
            'child_price': 2700,
            'discount': '限时优惠'
        }, token=self.token)
        self.assertEqual(status, 200)

        # 验证已更新
        _, price = self.json_get('/api/prices/HN-20260720', token=self.token)
        self.assertEqual(price['adult_price'], 3600)


# ========================================================================
# 申请管理 API 测试 —— 最复杂的业务流
# ========================================================================

class TestApplicationsAPI(TourismTestCase):
    """申请办理、查询、取消等业务流程"""

    def setUp(self):
        super().setUp()
        self.token = self.receptionist_token()
        self.admin = self.admin_token()

    # -------- 查询 --------

    def test_get_applications_list(self):
        """GET /api/applications —— 返回申请列表"""
        status, data = self.json_get('/api/applications', token=self.token)
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_get_application_detail(self):
        """GET /api/applications/<no> —— 返回申请详情含参加者和支付记录"""
        status, data = self.json_get('/api/applications/AP-20260501-001', token=self.token)
        self.assertEqual(status, 200)
        self.assertEqual(data['apply_no'], 'AP-20260501-001')
        self.assertIn('participants', data)
        self.assertIn('payments', data)

    def test_get_application_not_found(self):
        """不存在的申请返回 404"""
        status, data = self.json_get('/api/applications/NONEXIST', token=self.token)
        self.assertEqual(status, 404)
        self.assertIn('error', data)

    # -------- 创建申请 --------

    def test_create_application_success(self):
        """POST /api/applications —— 创建申请"""
        status, data = self.json_post('/api/applications', {
            'group_code': 'YN-20260701',
            'responsible_name': '测试人',
            'responsible_phone': '13900000001',
            'adult_count': 2,
            'child_count': 1,
            'total_fee': 8000
        }, token=self.token)
        self.assertEqual(status, 201)
        self.assertIn('apply_no', data)
        self.assertIn('deposit', data)

    def test_create_application_group_not_exist(self):
        """申请不存在的旅游团应失败"""
        status, data = self.json_post('/api/applications', {
            'group_code': 'NONEXIST',
            'responsible_name': '不存在',
            'responsible_phone': '13900000004',
            'adult_count': 1,
            'child_count': 0,
            'total_fee': 1000
        }, token=self.token)
        self.assertEqual(status, 400)

    def test_create_application_group_not_open(self):
        """申请状态非 '已开放' 的旅游团应失败"""
        status, data = self.json_post('/api/applications', {
            'group_code': 'YN-20260510',  # 已截止
            'responsible_name': '状态测试',
            'responsible_phone': '13900000003',
            'adult_count': 1,
            'child_count': 0,
            'total_fee': 3000
        }, token=self.token)
        self.assertEqual(status, 400)
        self.assertIn('不可申请', data['error'])

    def test_create_application_over_capacity(self):
        """超出旅游团容量限制应失败"""
        status, data = self.json_post('/api/applications', {
            'group_code': 'YN-20260620',
            'responsible_name': '超额测试',
            'responsible_phone': '13900000002',
            'adult_count': 3,
            'child_count': 0,
            'total_fee': 5000
        }, token=self.token)
        self.assertEqual(status, 400)
        self.assertIn('超出限额', data['error'])

    def test_create_application_increases_count(self):
        """创建申请后，旅游团已有人数应增加"""
        _, group_before = self.json_get('/api/groups/YN-20260701', token=self.admin)
        before = group_before['current_count']

        self.json_post('/api/applications', {
            'group_code': 'YN-20260701',
            'responsible_name': '人数测试',
            'responsible_phone': '13900000005',
            'adult_count': 2,
            'child_count': 1,
            'total_fee': 8000
        }, token=self.token)

        _, group_after = self.json_get('/api/groups/YN-20260701', token=self.admin)
        self.assertEqual(group_after['current_count'], before + 3)

    def test_create_application_adds_responsible_participant(self):
        """创建申请后，责任人自动成为参加者"""
        _, created = self.json_post('/api/applications', {
            'group_code': 'YN-20260701',
            'responsible_name': '责任人测试',
            'responsible_phone': '13900000006',
            'adult_count': 1,
            'child_count': 0,
            'total_fee': 3000
        }, token=self.token)
        _, detail = self.json_get(f"/api/applications/{created['apply_no']}", token=self.token)
        names = [p['name'] for p in detail['participants']]
        self.assertIn('责任人测试', names)

    # -------- 取消申请 --------

    def test_cancel_application(self):
        """POST /api/applications/<no>/cancel —— 取消申请"""
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        resp = self.client.post('/api/applications/AP-20260501-001/cancel', headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('fee_info', resp.get_json())

    def test_cancel_application_changes_status(self):
        """取消后申请状态变为 '已取消'"""
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        self.client.post('/api/applications/AP-20260501-001/cancel', headers=headers)
        _, app_data = self.json_get('/api/applications/AP-20260501-001', token=self.token)
        self.assertEqual(app_data['status'], '已取消')

    def test_cancel_application_cancels_participants(self):
        """取消申请后，所有参加者状态也变为 '已取消'"""
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        self.client.post('/api/applications/AP-20260501-001/cancel', headers=headers)
        _, app_data = self.json_get('/api/applications/AP-20260501-001', token=self.token)
        for p in app_data['participants']:
            self.assertEqual(p['status'], '已取消')

    def test_cancel_already_cancelled_fails(self):
        """重复取消已取消的申请应失败"""
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        self.client.post('/api/applications/AP-20260501-001/cancel', headers=headers)
        resp = self.client.post('/api/applications/AP-20260501-001/cancel', headers=headers)
        self.assertEqual(resp.status_code, 400)

    def test_cancel_application_not_found(self):
        """取消不存在的申请返回 404"""
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        resp = self.client.post('/api/applications/NONEXIST/cancel', headers=headers)
        self.assertEqual(resp.status_code, 404)

    def test_cancel_application_decreases_count(self):
        """取消申请后，旅游团人数应减少"""
        _, group_before = self.json_get('/api/groups/YN-20260615', token=self.admin)
        before = group_before['current_count']

        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        self.client.post('/api/applications/AP-20260501-001/cancel', headers=headers)

        _, group_after = self.json_get('/api/groups/YN-20260615', token=self.admin)
        self.assertEqual(group_after['current_count'],
                         before - 6)  # AP-20260501-001: adult=5, child=1


# ========================================================================
# 参加者管理 API 测试
# ========================================================================

class TestParticipantsAPI(TourismTestCase):
    """参加者录入、修改、取消等 API"""

    def setUp(self):
        super().setUp()
        self.token = self.receptionist_token()

    def test_get_participants(self):
        """GET /api/applications/<no>/participants —— 参加者列表"""
        status, data = self.json_get(
            '/api/applications/AP-20260501-001/participants', token=self.token)
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_add_participant(self):
        """POST —— 添加参加者"""
        status, data = self.json_post(
            '/api/applications/AP-20260501-001/participants', {
                'name': '新参加者',
                'gender': '女',
                'age': 25,
                'type': '大人',
                'phone': '13800000001'
            }, token=self.token)
        self.assertEqual(status, 201)

    def test_update_participant(self):
        """PUT /api/participants/<id> —— 更新参加者"""
        status, data = self.json_put('/api/participants/1', {
            'name': '新名字',
            'gender': '男',
            'age': 40,
            'type': '大人',
            'phone': '13900000000'
        }, token=self.token)
        self.assertEqual(status, 200)

    def test_cancel_non_responsible_participant(self):
        """取消非责任人参加者 —— 成功"""
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        resp = self.client.post('/api/participants/2/cancel', headers=headers)  # id=2 非责任人
        self.assertEqual(resp.status_code, 200)

    def test_cancel_responsible_participant_forbidden(self):
        """取消责任人参加者 —— 拒绝（需先变更责任人）"""
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        resp = self.client.post('/api/participants/1/cancel', headers=headers)  # id=1 是责任人
        self.assertEqual(resp.status_code, 400)
        self.assertIn('不能取消', resp.get_json()['error'])

    def test_cancel_participant_not_found(self):
        """取消不存在的参加者返回 404"""
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        resp = self.client.post('/api/participants/99999/cancel', headers=headers)
        self.assertEqual(resp.status_code, 404)

    def test_change_responsible(self):
        """POST .../change-responsible —— 变更责任人"""
        # 先添加一个新参加者
        self.json_post('/api/applications/AP-20260501-001/participants', {
            'name': '新责任人', 'gender': '女', 'age': 30,
            'type': '大人', 'phone': '13800000002'
        }, token=self.token)
        _, parts = self.json_get(
            '/api/applications/AP-20260501-001/participants', token=self.token)
        new_id = max(p['id'] for p in parts)

        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        resp = self.client.post(
            '/api/applications/AP-20260501-001/change-responsible',
            json={'new_responsible_id': new_id}, headers=headers)
        self.assertEqual(resp.status_code, 200)

        # 验证新责任人的标记
        _, parts = self.json_get(
            '/api/applications/AP-20260501-001/participants', token=self.token)
        new_resp = next(p for p in parts if p['id'] == new_id)
        self.assertEqual(new_resp['is_responsible'], 1)


# ========================================================================
# 余款支付 API 测试
# ========================================================================

class TestPaymentsAPI(TourismTestCase):
    """余额支付相关 API"""

    def setUp(self):
        super().setUp()
        self.token = self.collector_token()
        self.admin = self.admin_token()

    def test_get_pending_balance(self):
        """GET /api/balance/pending —— 待付余额列表"""
        status, data = self.json_get('/api/balance/pending', token=self.token)
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)

    def test_pay_balance_partial(self):
        """POST .../pay-balance —— 部分支付"""
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        resp = self.client.post(
            '/api/applications/AP-20260501-001/pay-balance',
            json={'amount': 1000, 'pay_method': '微信支付'}, headers=headers)
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body['paid_amount'], 1000)
        self.assertFalse(body['fully_paid'])

    def test_pay_balance_full(self):
        """全额付清后申请状态变为 '已完成'"""
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        resp = self.client.post(
            '/api/applications/AP-20260501-001/pay-balance',
            json={'amount': 9600, 'pay_method': '银行转账'}, headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()['fully_paid'])

        _, app_data = self.json_get('/api/applications/AP-20260501-001', token=self.admin)
        self.assertEqual(app_data['status'], '已完成')

    def test_pay_balance_exceed_remaining(self):
        """支付金额超出待付余额应拒绝"""
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        resp = self.client.post(
            '/api/applications/AP-20260501-001/pay-balance',
            json={'amount': 99999}, headers=headers)
        self.assertEqual(resp.status_code, 400)

    def test_pay_balance_not_found(self):
        """为不存在的申请支付返回 404"""
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token}'}
        resp = self.client.post(
            '/api/applications/NONEXIST/pay-balance',
            json={'amount': 1000}, headers=headers)
        self.assertEqual(resp.status_code, 404)


# ========================================================================
# 统计数据 API 测试
# ========================================================================

class TestStatsAPI(TourismTestCase):
    """仪表盘统计数据 API"""

    def setUp(self):
        super().setUp()
        self.token = self.admin_token()

    def test_get_stats_success(self):
        """GET /api/stats —— 返回统计数据"""
        status, data = self.json_get('/api/stats', token=self.token)
        self.assertEqual(status, 200)
        self.assertIn('monthly_applications', data)
        self.assertIn('today_applications', data)
        self.assertIn('pending_balance', data)
        self.assertIn('upcoming_groups', data)

    def test_stats_types(self):
        """统计值应为整数类型"""
        _, data = self.json_get('/api/stats', token=self.token)
        self.assertIsInstance(data['monthly_applications'], int)
        self.assertIsInstance(data['today_applications'], int)
        self.assertIsInstance(data['pending_balance'], int)
        self.assertIsInstance(data['upcoming_groups'], int)
