"""登录与权限控制 API 测试

测试覆盖：
- 登录成功/失败
- JWT Token 验证
- 角色权限控制
- 注册功能（仅管理员）
- 修改密码
"""

from tests import TourismTestCase


# ========================================================================
# 登录 API 测试
# ========================================================================

class TestLoginAPI(TourismTestCase):
    """POST /api/login 登录接口测试"""

    def test_login_success(self):
        """正确用户名密码应返回 200 和 token"""
        status, data = self.json_post('/api/login', {
            'username': 'zhangmin',
            'password': 'Travel@2026'
        })
        self.assertEqual(status, 200)
        self.assertIn('token', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['username'], 'zhangmin')
        self.assertEqual(data['user']['real_name'], '张敏')
        self.assertEqual(data['user']['role'], 'receptionist')
        self.assertIn('menus', data['user'])

    def test_login_wrong_password(self):
        """错误密码应返回 401"""
        status, data = self.json_post('/api/login', {
            'username': 'zhangmin',
            'password': 'wrong'
        })
        self.assertEqual(status, 401)
        self.assertIn('error', data)

    def test_login_nonexistent_user(self):
        """不存在的用户名应返回 401"""
        status, data = self.json_post('/api/login', {
            'username': 'nobody',
            'password': 'Travel@2026'
        })
        self.assertEqual(status, 401)

    def test_login_missing_fields(self):
        """缺少字段应返回 400"""
        status, data = self.json_post('/api/login', {'username': 'zhangmin'})
        self.assertEqual(status, 400)

        status, data = self.json_post('/api/login', {'password': 'Travel@2026'})
        self.assertEqual(status, 400)

    def test_login_empty_body(self):
        """空请求体应返回 400"""
        status, data = self.json_post('/api/login', {})
        self.assertEqual(status, 400)

    def test_login_returns_correct_menus(self):
        """不同角色登录应返回对应的菜单列表"""
        # 前台员工
        _, data = self.json_post('/api/login', {'username': 'zhangmin', 'password': 'Travel@2026'})
        self.assertIn('apply', data['user']['menus'])
        self.assertNotIn('finance', data['user']['menus'])

        # 会计人员
        _, data = self.json_post('/api/login', {'username': 'zhaofang', 'password': 'Travel@2026'})
        self.assertIn('finance', data['user']['menus'])
        self.assertNotIn('apply', data['user']['menus'])

        # 管理员
        _, data = self.json_post('/api/login', {'username': 'admin', 'password': 'Travel@2026'})
        self.assertIn('apply', data['user']['menus'])
        self.assertIn('finance', data['user']['menus'])
        self.assertIn('route', data['user']['menus'])


# ========================================================================
# Token 认证测试
# ========================================================================

class TestTokenAuth(TourismTestCase):
    """JWT Token 认证保护测试"""

    def test_no_token_returns_401(self):
        """无 token 访问受保护 API 应返回 401"""
        status, data = self.json_get('/api/routes')
        self.assertEqual(status, 401)
        self.assertIn('error', data)

    def test_invalid_token_returns_401(self):
        """无效 token 应返回 401"""
        status, data = self.json_get('/api/routes', token='invalid.token.here')
        self.assertEqual(status, 401)

    def test_valid_token_returns_200(self):
        """有效 token 应能正常访问"""
        token = self.admin_token()
        status, data = self.json_get('/api/routes', token=token)
        self.assertEqual(status, 200)

    def test_user_info_with_token(self):
        """GET /api/user/info 应返回当前用户信息"""
        token = self.receptionist_token()
        status, data = self.json_get('/api/user/info', token=token)
        self.assertEqual(status, 200)
        self.assertEqual(data['user']['username'], 'zhangmin')
        self.assertEqual(data['user']['role'], 'receptionist')

    def test_user_info_without_token(self):
        """无 token 访问 /api/user/info 应返回 401"""
        status, data = self.json_get('/api/user/info')
        self.assertEqual(status, 401)


# ========================================================================
# 角色权限测试
# ========================================================================

class TestRolePermissions(TourismTestCase):
    """角色权限控制测试"""

    def test_admin_can_access_all(self):
        """管理员应能访问所有 API"""
        token = self.admin_token()
        # 路线管理
        status, _ = self.json_get('/api/routes', token=token)
        self.assertEqual(status, 200)
        # 财务导出
        status, _ = self.json_get('/api/finance/export', token=token)
        self.assertEqual(status, 200)
        # 余款管理
        status, _ = self.json_get('/api/balance/pending', token=token)
        self.assertEqual(status, 200)

    def test_receptionist_cannot_access_finance(self):
        """前台员工不能访问财务导出"""
        token = self.receptionist_token()
        status, data = self.json_get('/api/finance/export', token=token)
        self.assertEqual(status, 403)

    def test_receptionist_cannot_access_balance(self):
        """前台员工不能访问余款管理"""
        token = self.receptionist_token()
        status, data = self.json_get('/api/balance/pending', token=token)
        self.assertEqual(status, 403)

    def test_collector_can_access_balance(self):
        """催款员工可以访问余款管理"""
        token = self.collector_token()
        status, _ = self.json_get('/api/balance/pending', token=token)
        self.assertEqual(status, 200)

    def test_collector_cannot_access_finance(self):
        """催款员工不能访问财务导出"""
        token = self.collector_token()
        status, data = self.json_get('/api/finance/export', token=token)
        self.assertEqual(status, 403)

    def test_route_admin_can_manage_routes(self):
        """路线管理员可以管理路线"""
        token = self.route_admin_token()
        status, _ = self.json_get('/api/routes', token=token)
        self.assertEqual(status, 200)

    def test_route_admin_cannot_access_finance(self):
        """路线管理员不能访问财务导出"""
        token = self.route_admin_token()
        status, data = self.json_get('/api/finance/export', token=token)
        self.assertEqual(status, 403)

    def test_accountant_can_access_finance(self):
        """会计人员可以访问财务导出"""
        token = self.accountant_token()
        status, _ = self.json_get('/api/finance/export', token=token)
        self.assertEqual(status, 200)

    def test_accountant_cannot_manage_routes(self):
        """会计人员不能创建路线"""
        token = self.accountant_token()
        status, data = self.json_post('/api/routes', {
            'route_code': 'R-TEST', 'route_name': '测试路线'
        }, token=token)
        self.assertEqual(status, 403)

    def test_accountant_can_access_applications(self):
        """会计人员可以查看申请列表（只读）"""
        token = self.accountant_token()
        status, data = self.json_get('/api/applications', token=token)
        self.assertEqual(status, 200)


# ========================================================================
# 注册 API 测试
# ========================================================================

class TestRegisterAPI(TourismTestCase):
    """POST /api/register 注册接口测试"""

    def test_admin_can_register(self):
        """管理员可以注册新用户"""
        token = self.admin_token()
        status, data = self.json_post('/api/register', {
            'username': 'newuser',
            'password': 'Travel@2026',
            'real_name': '新用户',
            'role': 'receptionist'
        }, token=token)
        self.assertEqual(status, 201)

    def test_non_admin_cannot_register(self):
        """非管理员不能注册新用户"""
        token = self.receptionist_token()
        status, data = self.json_post('/api/register', {
            'username': 'newuser',
            'password': 'Travel@2026',
            'real_name': '新用户',
            'role': 'receptionist'
        }, token=token)
        self.assertEqual(status, 403)

    def test_register_duplicate_username(self):
        """重复用户名应返回 400"""
        token = self.admin_token()
        status, data = self.json_post('/api/register', {
            'username': 'zhangmin',
            'password': 'Travel@2026',
            'real_name': '重复用户',
            'role': 'receptionist'
        }, token=token)
        self.assertEqual(status, 400)

    def test_register_invalid_role(self):
        """无效角色应返回 400"""
        token = self.admin_token()
        status, data = self.json_post('/api/register', {
            'username': 'newuser',
            'password': 'Travel@2026',
            'real_name': '新用户',
            'role': 'invalid_role'
        }, token=token)
        self.assertEqual(status, 400)

    def test_register_missing_fields(self):
        """缺少必填字段应返回 400"""
        token = self.admin_token()
        status, data = self.json_post('/api/register', {
            'username': 'newuser'
        }, token=token)
        self.assertEqual(status, 400)


# ========================================================================
# 修改密码测试
# ========================================================================

class TestChangePassword(TourismTestCase):
    """PUT /api/user/password 修改密码测试"""

    def test_change_password_success(self):
        """正确原密码应能修改成功"""
        token = self.receptionist_token()
        status, data = self.json_put('/api/user/password', {
            'old_password': 'Travel@2026',
            'new_password': 'Newpass123'
        }, token=token)
        self.assertEqual(status, 200)

        # 用新密码登录
        status, data = self.json_post('/api/login', {
            'username': 'zhangmin',
            'password': 'Newpass123'
        })
        self.assertEqual(status, 200)

    def test_change_password_wrong_old(self):
        """错误原密码应返回 400"""
        token = self.receptionist_token()
        status, data = self.json_put('/api/user/password', {
            'old_password': 'wrong',
            'new_password': 'newpass123'
        }, token=token)
        self.assertEqual(status, 400)

    def test_change_password_too_short(self):
        """新密码太短应返回 400"""
        token = self.receptionist_token()
        status, data = self.json_put('/api/user/password', {
            'old_password': 'Travel@2026',
            'new_password': '123'
        }, token=token)
        self.assertEqual(status, 400)


# ========================================================================
# 用户列表测试（仅管理员）
# ========================================================================

class TestUserListAPI(TourismTestCase):
    """GET /api/users 用户列表测试"""

    def test_admin_can_list_users(self):
        """管理员可以查看用户列表"""
        token = self.admin_token()
        status, data = self.json_get('/api/users', token=token)
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 5)  # 5 个种子用户

    def test_non_admin_cannot_list_users(self):
        """非管理员不能查看用户列表"""
        token = self.receptionist_token()
        status, data = self.json_get('/api/users', token=token)
        self.assertEqual(status, 403)
