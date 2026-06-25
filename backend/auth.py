"""认证与权限控制模块

提供 JWT Token 生成/验证、密码哈希、以及 Flask 装饰器：
- login_required: 校验请求头中的 JWT Token
- role_required: 校验用户角色是否有权限访问当前 API
"""

import os
import re
import functools
from datetime import datetime, timedelta, timezone
from flask import request, jsonify, g
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db


# ==================== 配置 ====================

SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(32).hex())
TOKEN_EXPIRE_HOURS = 8
ALGORITHM = "HS256"


# ==================== 角色权限映射 ====================

# 每个角色可访问的 API 路径前缀列表
# 'admin' 角色拥有全部权限（'/api/' 匹配所有）
ROLE_PERMISSIONS = {
    'receptionist': [
        '/api/applications',
        '/api/participants',
        '/api/groups',
        '/api/routes',
        '/api/activities',
        '/api/prices',
        '/api/calc-',
        '/api/stats',
    ],
    'collector': [
        '/api/balance',
        '/api/applications',      # 查看申请信息用于催款
        '/api/groups',
        '/api/routes',
        '/api/activities',
        '/api/stats',
    ],
    'routeAdmin': [
        '/api/routes',
        '/api/activities',
        '/api/groups',
        '/api/prices',
        '/api/stats',
    ],
    'accountant': [
        '/api/finance',
        '/api/stats',
    ],
    'admin': [
        '/api/',                  # 全部权限
    ],
}

# 前端菜单与角色的映射（用于返回给前端）
ROLE_MENUS = {
    'receptionist': ['home', 'query', 'apply', 'participant', 'change'],
    'collector':    ['home', 'query', 'balance', 'print'],
    'routeAdmin':   ['home', 'query', 'route', 'activity', 'price'],
    'accountant':   ['home', 'query', 'finance'],
    'admin':        ['home', 'query', 'apply', 'participant', 'balance',
                     'change', 'print', 'route', 'activity', 'price', 'finance'],
}


# ==================== 密码工具 ====================

def validate_password(password):
    """校验密码强度：至少6位，包含大小写字母和数字"""
    if len(password) < 6:
        return '密码长度不能少于6位'
    if not re.search(r'[a-z]', password):
        return '密码必须包含小写字母'
    if not re.search(r'[A-Z]', password):
        return '密码必须包含大写字母'
    if not re.search(r'\d', password):
        return '密码必须包含数字'
    return None


def hash_password(password):
    """生成密码哈希"""
    return generate_password_hash(password)


def check_password(password_hash, password):
    """验证密码"""
    return check_password_hash(password_hash, password)


# ==================== JWT 工具 ====================

def generate_token(user):
    """生成 JWT Token

    Args:
        user: dict，包含 user_id, username, real_name, role

    Returns:
        JWT token 字符串
    """
    payload = {
        'user_id': user['id'],
        'username': user['username'],
        'real_name': user['real_name'],
        'role': user['role'],
        'exp': datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS),
        'iat': datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token):
    """验证并解析 JWT Token

    Args:
        token: JWT token 字符串

    Returns:
        解析后的 payload dict，失败返回 None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ==================== 装饰器 ====================

def login_required(f):
    """登录校验装饰器

    从请求头 Authorization: Bearer <token> 中提取并验证 JWT Token。
    验证成功后将用户信息存入 flask.g.user。
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': '未登录，请先登录'}), 401

        token = auth_header[7:]  # 去掉 "Bearer " 前缀
        payload = verify_token(token)
        if payload is None:
            return jsonify({'error': '登录已过期，请重新登录'}), 401

        # 将用户信息存入 g，供后续路由使用
        g.user = {
            'user_id': payload['user_id'],
            'username': payload['username'],
            'real_name': payload['real_name'],
            'role': payload['role'],
        }
        return f(*args, **kwargs)

    return decorated


def role_required(*allowed_roles):
    """角色权限校验装饰器

    检查当前用户角色是否在允许列表中，或是否具有对应的 API 路径权限。

    Args:
        *allowed_roles: 允许的角色名称列表
    """
    def decorator(f):
        @functools.wraps(f)
        @login_required
        def decorated(*args, **kwargs):
            user_role = g.user['role']

            # admin 拥有全部权限
            if user_role == 'admin':
                return f(*args, **kwargs)

            # 检查角色是否在允许列表中
            if user_role in allowed_roles:
                return f(*args, **kwargs)

            # 检查角色权限映射中是否有当前路径的权限
            path = request.path
            perms = ROLE_PERMISSIONS.get(user_role, [])
            for prefix in perms:
                if path.startswith(prefix):
                    return f(*args, **kwargs)

            return jsonify({'error': '权限不足，无法访问此功能'}), 403

        return decorated
    return decorator
