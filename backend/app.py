import os
import uuid
import time

from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from database import get_db, init_db, seed_data
from auth import (
    login_required, role_required, validate_password,
    hash_password, check_password,
    generate_token, ROLE_MENUS
)
from datetime import date, timedelta

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='')
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1MB 请求体上限

cors_origins = os.environ.get('CORS_ORIGINS', '').split(',')
CORS(app, origins=[o.strip() for o in cors_origins if o.strip()])




# ==================== 工具函数 ====================

def row_to_dict(row):
    return dict(row) if row else None


def rows_to_list(rows):
    return [dict(r) for r in rows]


def gen_apply_no():
    today = date.today().strftime('%Y%m%d')
    short_id = uuid.uuid4().hex[:6].upper()
    return f'AP-{today}-{short_id}'


def gen_payment_no():
    today = date.today().strftime('%Y%m%d')
    short_id = uuid.uuid4().hex[:6].upper()
    return f'PAY-{today}-{short_id}'


def get_paid_amount(db, apply_no):
    return db.execute(
        "SELECT COALESCE(SUM(amount),0) as total FROM payment WHERE apply_no=? AND pay_type IN ('订金','余款')",
        (apply_no,)
    ).fetchone()['total']


def sync_participant_counts(db, apply_no):
    """根据实际参加者列表重算申请表中的 adult_count / child_count"""
    counts = db.execute(
        "SELECT type, COUNT(*) as cnt FROM participant WHERE apply_no=? AND status='已录入' GROUP BY type",
        (apply_no,)
    ).fetchall()
    count_map = {r['type']: r['cnt'] for r in counts}
    adult = count_map.get('大人', 0)
    child = count_map.get('小孩', 0)
    db.execute(
        "UPDATE application SET adult_count=?, child_count=? WHERE apply_no=?",
        (adult, child, apply_no)
    )


def calc_deposit(departure_date, adult, child):
    """根据距出发天数计算订金"""
    days = (departure_date - date.today()).days
    if days >= 60:
        per_person = 300
    elif days >= 30:
        per_person = 600
    elif days >= 15:
        per_person = 1000
    else:
        per_person = 600  # 简化：14天内按全额，此处用600代替
    total = (adult + child) * per_person
    return {'days': days, 'per_person': per_person, 'total': total}


def calc_cancel_fee(departure_date, paid_amount):
    """根据距出发天数计算取消手续费"""
    days = (departure_date - date.today()).days
    if days >= 30:
        rate = 0.10
    elif days >= 15:
        rate = 0.30
    elif days >= 7:
        rate = 0.50
    else:
        rate = 1.0
    fee = paid_amount * rate
    refund = paid_amount - fee
    return {'days': days, 'rate': rate, 'fee': round(fee, 2), 'refund': round(refund, 2)}


# ==================== 登录与用户管理 ====================

@app.route('/api/login', methods=['POST'])
def login():
    """用户登录，返回 JWT Token"""
    data = request.json
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': '请输入用户名和密码'}), 400

    db = get_db()
    user = db.execute(
        "SELECT * FROM user WHERE username=?", (data['username'],)
    ).fetchone()
    db.close()

    if not user:
        return jsonify({'error': '用户名或密码错误'}), 401
    if not user['is_active']:
        return jsonify({'error': '该账号已被禁用'}), 403
    if not check_password(user['password_hash'], data['password']):
        return jsonify({'error': '用户名或密码错误'}), 401

    user_dict = dict(user)
    token = generate_token(user_dict)

    return jsonify({
        'message': '登录成功',
        'token': token,
        'user': {
            'id': user_dict['id'],
            'username': user_dict['username'],
            'real_name': user_dict['real_name'],
            'role': user_dict['role'],
            'menus': ROLE_MENUS.get(user_dict['role'], []),
        }
    })


@app.route('/api/register', methods=['POST'])
@login_required
@role_required('admin')
def register():
    """注册新用户（仅管理员可用）"""
    data = request.json
    required = ['username', 'password', 'real_name', 'role']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'缺少必填字段: {field}'}), 400

    valid_roles = ['receptionist', 'collector', 'routeAdmin', 'accountant', 'admin']
    if data['role'] not in valid_roles:
        return jsonify({'error': f'无效角色，可选: {", ".join(valid_roles)}'}), 400

    pw_error = validate_password(data['password'])
    if pw_error:
        return jsonify({'error': pw_error}), 400

    if len(data['username']) < 3 or len(data['username']) > 20:
        return jsonify({'error': '用户名长度需在3-20个字符之间'}), 400

    db = get_db()
    existing = db.execute("SELECT id FROM user WHERE username=?", (data['username'],)).fetchone()
    if existing:
        db.close()
        return jsonify({'error': '用户名已存在'}), 400

    try:
        db.execute(
            "INSERT INTO user (username, password_hash, real_name, role) VALUES (?,?,?,?)",
            (data['username'], hash_password(data['password']),
             data['real_name'], data['role'])
        )
        db.commit()
        return jsonify({'message': '用户注册成功'}), 201
    except Exception:
        db.rollback()
        return jsonify({'error': '注册失败，请稍后重试'}), 400
    finally:
        db.close()


@app.route('/api/user/info', methods=['GET'])
@login_required
def get_user_info():
    """获取当前登录用户信息"""
    return jsonify({
        'user': {
            'user_id': g.user['user_id'],
            'username': g.user['username'],
            'real_name': g.user['real_name'],
            'role': g.user['role'],
            'menus': ROLE_MENUS.get(g.user['role'], []),
        }
    })


@app.route('/api/user/password', methods=['PUT'])
@login_required
def change_password():
    """修改密码"""
    data = request.json
    if not data.get('old_password') or not data.get('new_password'):
        return jsonify({'error': '请输入原密码和新密码'}), 400

    db = get_db()
    user = db.execute("SELECT * FROM user WHERE id=?", (g.user['user_id'],)).fetchone()

    if not check_password(user['password_hash'], data['old_password']):
        db.close()
        return jsonify({'error': '原密码错误'}), 400

    pw_error = validate_password(data['new_password'])
    if pw_error:
        db.close()
        return jsonify({'error': pw_error}), 400

    db.execute(
        "UPDATE user SET password_hash=? WHERE id=?",
        (hash_password(data['new_password']), g.user['user_id'])
    )
    db.commit()
    db.close()
    return jsonify({'message': '密码修改成功'})


@app.route('/api/users', methods=['GET'])
@login_required
@role_required('admin')
def get_users():
    """获取用户列表（仅管理员）"""
    db = get_db()
    rows = db.execute(
        "SELECT id, username, real_name, role, is_active, created_date FROM user ORDER BY id"
    ).fetchall()
    db.close()
    return jsonify(rows_to_list(rows))


# ==================== 路线管理 ====================

@app.route('/api/routes', methods=['GET'])
@login_required
def get_routes():
    db = get_db()
    rows = db.execute("SELECT * FROM route ORDER BY created_date DESC").fetchall()
    db.close()
    return jsonify(rows_to_list(rows))


@app.route('/api/routes', methods=['POST'])
@login_required
@role_required('routeAdmin')
def create_route():
    data = request.json
    db = get_db()
    try:
        db.execute(
            "INSERT INTO route (route_code, route_name, description) VALUES (?,?,?)",
            (data['route_code'], data['route_name'], data.get('description', ''))
        )
        db.execute(
            "INSERT INTO route_change_log (route_code, content, operator) VALUES (?,?,?)",
            (data['route_code'], '路线创建', data.get('operator', '系统'))
        )
        db.commit()
        return jsonify({'message': '路线创建成功'}), 201
    except Exception:
        db.rollback()
        return jsonify({'error': '路线创建失败，请检查编号是否重复'}), 400
    finally:
        db.close()


@app.route('/api/routes/<route_code>', methods=['GET'])
@login_required
def get_route(route_code):
    db = get_db()
    route = db.execute("SELECT * FROM route WHERE route_code=?", (route_code,)).fetchone()
    if not route:
        db.close()
        return jsonify({'error': '路线不存在'}), 404

    activities = db.execute(
        "SELECT * FROM activity WHERE route_code=?", (route_code,)
    ).fetchall()
    logs = db.execute(
        "SELECT * FROM route_change_log WHERE route_code=? ORDER BY change_date DESC",
        (route_code,)
    ).fetchall()
    db.close()

    result = row_to_dict(route)
    result['activities'] = rows_to_list(activities)
    result['change_logs'] = rows_to_list(logs)
    return jsonify(result)


@app.route('/api/routes/<route_code>', methods=['PUT'])
@login_required
@role_required('routeAdmin')
def update_route(route_code):
    data = request.json
    db = get_db()
    route = db.execute("SELECT * FROM route WHERE route_code=?", (route_code,)).fetchone()
    if not route:
        db.close()
        return jsonify({'error': '路线不存在'}), 404

    db.execute(
        "UPDATE route SET route_name=?, description=? WHERE route_code=?",
        (data.get('route_name', route['route_name']),
         data.get('description', route['description']),
         route_code)
    )
    db.execute(
        "INSERT INTO route_change_log (route_code, content, operator) VALUES (?,?,?)",
        (route_code, f"路线信息更新", data.get('operator', '系统'))
    )
    db.commit()
    db.close()
    return jsonify({'message': '路线更新成功'})


@app.route('/api/routes/<route_code>/cancel', methods=['POST'])
@login_required
@role_required('routeAdmin')
def cancel_route(route_code):
    db = get_db()
    db.execute("UPDATE route SET status='已取消' WHERE route_code=?", (route_code,))
    db.execute(
        "INSERT INTO route_change_log (route_code, content, operator) VALUES (?,?,?)",
        (route_code, '路线取消', request.json.get('operator', '系统'))
    )
    db.commit()
    db.close()
    return jsonify({'message': '路线已取消'})


# ==================== 旅游活动管理 ====================

@app.route('/api/activities', methods=['GET'])
@login_required
def get_activities():
    route_code = request.args.get('route_code')
    db = get_db()
    if route_code:
        rows = db.execute(
            "SELECT a.*, r.route_name FROM activity a JOIN route r ON a.route_code=r.route_code WHERE a.route_code=?",
            (route_code,)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT a.*, r.route_name FROM activity a JOIN route r ON a.route_code=r.route_code"
        ).fetchall()
    db.close()
    return jsonify(rows_to_list(rows))


@app.route('/api/activities', methods=['POST'])
@login_required
@role_required('routeAdmin')
def create_activity():
    data = request.json
    db = get_db()
    try:
        db.execute(
            "INSERT INTO activity (activity_code, activity_name, description, route_code) VALUES (?,?,?,?)",
            (data['activity_code'], data['activity_name'],
             data.get('description', ''), data['route_code'])
        )
        db.commit()
        return jsonify({'message': '旅游活动创建成功'}), 201
    except Exception:
        db.rollback()
        return jsonify({'error': '活动创建失败，请检查编号是否重复'}), 400
    finally:
        db.close()


@app.route('/api/activities/<activity_code>', methods=['PUT'])
@login_required
@role_required('routeAdmin')
def update_activity(activity_code):
    data = request.json
    db = get_db()
    db.execute(
        "UPDATE activity SET activity_name=?, description=? WHERE activity_code=?",
        (data['activity_name'], data.get('description', ''), activity_code)
    )
    db.commit()
    db.close()
    return jsonify({'message': '旅游活动更新成功'})


# ==================== 旅游团管理 ====================

@app.route('/api/groups', methods=['GET'])
@login_required
def get_groups():
    status = request.args.get('status')
    db = get_db()
    sql = '''SELECT g.*, a.activity_name, r.route_name, p.adult_price, p.child_price, p.discount, p.is_published
             FROM tour_group g
             JOIN activity a ON g.activity_code=a.activity_code
             JOIN route r ON a.route_code=r.route_code
             LEFT JOIN price p ON g.group_code=p.group_code'''
    params = []
    if status:
        sql += ' WHERE g.status=?'
        params.append(status)
    sql += ' ORDER BY g.departure_date'
    rows = db.execute(sql, params).fetchall()
    db.close()
    return jsonify(rows_to_list(rows))


@app.route('/api/groups', methods=['POST'])
@login_required
@role_required('routeAdmin')
def create_group():
    data = request.json
    db = get_db()
    try:
        # 计算余款截止日期（默认出发前3天）
        departure = date.fromisoformat(data['departure_date'])
        balance_deadline = data.get('balance_deadline') or (departure - timedelta(days=3)).isoformat()

        db.execute(
            "INSERT INTO tour_group (group_code, activity_code, departure_date, deadline, balance_deadline, capacity) VALUES (?,?,?,?,?,?)",
            (data['group_code'], data['activity_code'],
             data['departure_date'], data['deadline'], balance_deadline, data['capacity'])
        )
        db.commit()
        return jsonify({'message': '旅游团创建成功'}), 201
    except Exception:
        db.rollback()
        return jsonify({'error': '旅游团创建失败，请检查编号是否重复'}), 400
    finally:
        db.close()


@app.route('/api/groups/<group_code>', methods=['GET'])
@login_required
def get_group(group_code):
    db = get_db()
    row = db.execute(
        '''SELECT g.*, a.activity_name, r.route_name, r.route_code
           FROM tour_group g
           JOIN activity a ON g.activity_code=a.activity_code
           JOIN route r ON a.route_code=r.route_code
           WHERE g.group_code=?''',
        (group_code,)
    ).fetchone()
    db.close()
    if not row:
        return jsonify({'error': '旅游团不存在'}), 404
    return jsonify(row_to_dict(row))


# ==================== 价格管理 ====================

@app.route('/api/prices', methods=['GET'])
@login_required
def get_prices():
    db = get_db()
    rows = db.execute(
        '''SELECT p.*, g.departure_date, a.activity_name, r.route_name
           FROM price p
           JOIN tour_group g ON p.group_code=g.group_code
           JOIN activity a ON g.activity_code=a.activity_code
           JOIN route r ON a.route_code=r.route_code'''
    ).fetchall()
    db.close()
    return jsonify(rows_to_list(rows))


@app.route('/api/prices/<group_code>', methods=['GET'])
@login_required
def get_price(group_code):
    db = get_db()
    row = db.execute("SELECT * FROM price WHERE group_code=?", (group_code,)).fetchone()
    db.close()
    if not row:
        return jsonify({'error': '价格未设定'}), 404
    return jsonify(row_to_dict(row))


@app.route('/api/prices/<group_code>', methods=['PUT'])
@login_required
@role_required('routeAdmin')
def update_price(group_code):
    data = request.json
    db = get_db()
    existing = db.execute("SELECT * FROM price WHERE group_code=?", (group_code,)).fetchone()
    if existing and existing['is_published']:
        db.close()
        return jsonify({'error': '价格已公开，不可修改'}), 400

    if existing:
        db.execute(
            "UPDATE price SET adult_price=?, child_price=?, discount=? WHERE group_code=?",
            (data['adult_price'], data['child_price'], data.get('discount', ''), group_code)
        )
    else:
        db.execute(
            "INSERT INTO price (group_code, adult_price, child_price, discount) VALUES (?,?,?,?)",
            (group_code, data['adult_price'], data['child_price'], data.get('discount', ''))
        )
    db.commit()
    db.close()
    return jsonify({'message': '价格已保存'})


@app.route('/api/prices/<group_code>/publish', methods=['POST'])
@login_required
@role_required('routeAdmin')
def publish_price(group_code):
    db = get_db()
    existing = db.execute("SELECT * FROM price WHERE group_code=?", (group_code,)).fetchone()
    if not existing:
        db.close()
        return jsonify({'error': '请先设定价格'}), 400
    if existing['is_published']:
        db.close()
        return jsonify({'error': '价格已公开'}), 400

    db.execute("UPDATE price SET is_published=1 WHERE group_code=?", (group_code,))
    db.commit()
    db.close()
    return jsonify({'message': '价格已公开'})


# ==================== 申请管理 ====================

@app.route('/api/applications', methods=['GET'])
@login_required
@role_required('receptionist', 'collector', 'accountant')
def get_applications():
    db = get_db()
    rows = db.execute(
        '''SELECT ap.*, g.departure_date, a.activity_name, r.route_name
           FROM application ap
           JOIN tour_group g ON ap.group_code=g.group_code
           JOIN activity a ON g.activity_code=a.activity_code
           JOIN route r ON a.route_code=r.route_code
           ORDER BY ap.apply_date DESC'''
    ).fetchall()
    db.close()
    return jsonify(rows_to_list(rows))


@app.route('/api/applications/<apply_no>', methods=['GET'])
@login_required
@role_required('receptionist', 'collector')
def get_application(apply_no):
    db = get_db()
    app_row = db.execute(
        '''SELECT ap.*, g.departure_date, g.deadline, a.activity_name, r.route_name
           FROM application ap
           JOIN tour_group g ON ap.group_code=g.group_code
           JOIN activity a ON g.activity_code=a.activity_code
           JOIN route r ON a.route_code=r.route_code
           WHERE ap.apply_no=?''',
        (apply_no,)
    ).fetchone()
    if not app_row:
        db.close()
        return jsonify({'error': '申请不存在'}), 404

    participants = db.execute(
        "SELECT * FROM participant WHERE apply_no=? AND status='已录入' ORDER BY id", (apply_no,)
    ).fetchall()
    payments = db.execute(
        "SELECT * FROM payment WHERE apply_no=? ORDER BY pay_date", (apply_no,)
    ).fetchall()
    db.close()

    result = row_to_dict(app_row)
    result['participants'] = rows_to_list(participants)
    result['payments'] = rows_to_list(payments)
    return jsonify(result)


@app.route('/api/applications', methods=['POST'])
@login_required
@role_required('receptionist')
def create_application():
    data = request.json
    db = get_db()

    # 检查旅游团是否可申请
    group = db.execute("SELECT * FROM tour_group WHERE group_code=?", (data['group_code'],)).fetchone()
    if not group:
        db.close()
        return jsonify({'error': '旅游团不存在'}), 400
    if group['status'] != '已开放':
        db.close()
        return jsonify({'error': '旅游团当前不可申请'}), 400
    if group['current_count'] + data['adult_count'] + data['child_count'] > group['capacity']:
        db.close()
        return jsonify({'error': '人数超出限额'}), 400

    # 计算订金
    departure = date.fromisoformat(group['departure_date'])
    deposit_info = calc_deposit(departure, data['adult_count'], data['child_count'])

    apply_no = gen_apply_no()
    try:
        db.execute(
            '''INSERT INTO application
               (apply_no, group_code, responsible_name, responsible_phone, responsible_idcard,
                adult_count, child_count, deposit, total_fee)
               VALUES (?,?,?,?,?,?,?,?,?)''',
            (apply_no, data['group_code'], data['responsible_name'],
             data['responsible_phone'], data.get('responsible_idcard', ''),
             data['adult_count'], data['child_count'],
             deposit_info['total'], data.get('total_fee', 0))
        )
        # 添加申请责任人为参加者
        db.execute(
            '''INSERT INTO participant (apply_no, name, gender, age, idcard, type, phone, is_responsible)
               VALUES (?,?,?,?,?,?,?,1)''',
            (apply_no, data['responsible_name'], data.get('gender', '男'),
             data.get('age', 0), data.get('responsible_idcard', ''),
             '大人', data['responsible_phone'])
        )
        # 更新旅游团人数
        db.execute(
            "UPDATE tour_group SET current_count=current_count+? WHERE group_code=?",
            (data['adult_count'] + data['child_count'], data['group_code'])
        )
        # 记录订金支付
        pay_no = gen_payment_no()
        db.execute(
            "INSERT INTO payment (payment_no, apply_no, amount, pay_type, pay_method) VALUES (?,?,?,?,?)",
            (pay_no, apply_no, deposit_info['total'], '订金', data.get('pay_method', '现金'))
        )
        db.commit()
        return jsonify({
            'message': '申请办理成功',
            'apply_no': apply_no,
            'deposit': deposit_info
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()


@app.route('/api/applications/<apply_no>/cancel', methods=['POST'])
@login_required
@role_required('receptionist')
def cancel_application(apply_no):
    db = get_db()
    app_row = db.execute("SELECT * FROM application WHERE apply_no=?", (apply_no,)).fetchone()
    if not app_row:
        db.close()
        return jsonify({'error': '申请不存在'}), 404
    if app_row['status'] == '已取消':
        db.close()
        return jsonify({'error': '申请已取消'}), 400
    if app_row['status'] == '已完成':
        db.close()
        return jsonify({'error': '申请已完成，无法取消'}), 400

    group = db.execute("SELECT * FROM tour_group WHERE group_code=?", (app_row['group_code'],)).fetchone()
    departure = date.fromisoformat(group['departure_date'])

    # 计算已付金额
    paid = get_paid_amount(db, apply_no)

    fee_info = calc_cancel_fee(departure, paid)

    try:
        db.execute("UPDATE application SET status='已取消' WHERE apply_no=?", (apply_no,))
        db.execute(
            "UPDATE participant SET status='已取消' WHERE apply_no=?", (apply_no,)
        )
        db.execute(
            "UPDATE tour_group SET current_count=current_count-? WHERE group_code=?",
            (app_row['adult_count'] + app_row['child_count'], app_row['group_code'])
        )
        # 记录退款
        if fee_info['refund'] > 0:
            refund_no = gen_payment_no()
            db.execute(
                "INSERT INTO payment (payment_no, apply_no, amount, pay_type, pay_method) VALUES (?,?,?,?,?)",
                (refund_no, apply_no, -fee_info['refund'], '退款', '银行转账')
            )
        db.commit()
        return jsonify({
            'message': '申请已取消',
            'fee_info': fee_info
        })
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()


# ==================== 参加者管理 ====================

@app.route('/api/applications/<apply_no>/participants', methods=['GET'])
@login_required
@role_required('receptionist', 'collector')
def get_participants(apply_no):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM participant WHERE apply_no=? AND status='已录入' ORDER BY id",
        (apply_no,)
    ).fetchall()
    db.close()
    return jsonify(rows_to_list(rows))


@app.route('/api/applications/<apply_no>/participants', methods=['POST'])
@login_required
@role_required('receptionist')
def add_participant(apply_no):
    data = request.json
    db = get_db()

    # 数据校验
    if not data.get('name', '').strip():
        db.close()
        return jsonify({'error': '姓名不能为空'}), 400
    if not data.get('gender') or data['gender'] not in ('男', '女'):
        db.close()
        return jsonify({'error': '性别必须为男或女'}), 400
    if not isinstance(data.get('age'), int) or data['age'] < 1:
        db.close()
        return jsonify({'error': '年龄必须为正整数'}), 400
    if data.get('type') not in ('大人', '小孩'):
        db.close()
        return jsonify({'error': '类型必须为大人或小孩'}), 400
    idcard = data.get('idcard', '')
    if idcard and (len(idcard) != 18 or not idcard.isdigit()):
        db.close()
        return jsonify({'error': '身份证号须为18位数字'}), 400
    phone = data.get('phone', '')
    if phone and (len(phone) != 11 or not phone.isdigit()):
        db.close()
        return jsonify({'error': '电话号码须为11位数字'}), 400

    # 校验人数是否超出申请限额
    app_row = db.execute("SELECT adult_count, child_count FROM application WHERE apply_no=?", (apply_no,)).fetchone()
    if not app_row:
        db.close()
        return jsonify({'error': '申请不存在'}), 404

    counts = db.execute(
        "SELECT type, COUNT(*) as cnt FROM participant WHERE apply_no=? AND status='已录入' GROUP BY type",
        (apply_no,)
    ).fetchall()
    count_map = {r['type']: r['cnt'] for r in counts}
    current_adult = count_map.get('大人', 0)
    current_child = count_map.get('小孩', 0)

    if data['type'] == '大人' and current_adult >= app_row['adult_count']:
        db.close()
        return jsonify({'error': f'大人人数已达上限（{app_row["adult_count"]}人），无法继续添加'}), 400
    if data['type'] == '小孩' and current_child >= app_row['child_count']:
        db.close()
        return jsonify({'error': f'小孩人数已达上限（{app_row["child_count"]}人），无法继续添加'}), 400

    try:
        db.execute(
            '''INSERT INTO participant (apply_no, name, gender, age, idcard, type, phone)
               VALUES (?,?,?,?,?,?,?)''',
            (apply_no, data['name'], data['gender'], data['age'],
             data.get('idcard', ''), data['type'], data.get('phone', ''))
        )
        db.commit()
        return jsonify({'message': '参加者添加成功'}), 201
    except Exception:
        db.rollback()
        return jsonify({'error': '参加者添加失败'}), 400
    finally:
        db.close()


@app.route('/api/participants/<int:pid>', methods=['PUT'])
@login_required
@role_required('receptionist')
def update_participant(pid):
    data = request.json
    db = get_db()

    # 数据校验
    if not data.get('name', '').strip():
        db.close()
        return jsonify({'error': '姓名不能为空'}), 400
    if not data.get('gender') or data['gender'] not in ('男', '女'):
        db.close()
        return jsonify({'error': '性别必须为男或女'}), 400
    if not isinstance(data.get('age'), int) or data['age'] < 1:
        db.close()
        return jsonify({'error': '年龄必须为正整数'}), 400
    if data.get('type') not in ('大人', '小孩'):
        db.close()
        return jsonify({'error': '类型必须为大人或小孩'}), 400
    idcard = data.get('idcard', '')
    if idcard and (len(idcard) != 18 or not idcard.isdigit()):
        db.close()
        return jsonify({'error': '身份证号须为18位数字'}), 400
    phone = data.get('phone', '')
    if phone and (len(phone) != 11 or not phone.isdigit()):
        db.close()
        return jsonify({'error': '电话号码须为11位数字'}), 400

    db.execute(
        "UPDATE participant SET name=?, gender=?, age=?, idcard=?, type=?, phone=? WHERE id=?",
        (data['name'], data['gender'], data['age'],
         data.get('idcard', ''), data['type'], data.get('phone', ''), pid)
    )
    db.commit()
    db.close()
    return jsonify({'message': '参加者信息已更新'})


@app.route('/api/participants/<int:pid>/cancel', methods=['POST'])
@login_required
@role_required('receptionist')
def cancel_participant(pid):
    db = get_db()
    p = db.execute("SELECT * FROM participant WHERE id=?", (pid,)).fetchone()
    if not p:
        db.close()
        return jsonify({'error': '参加者不存在'}), 404

    if p['is_responsible']:
        db.close()
        return jsonify({'error': '不能取消申请责任人，请先变更责任人'}), 400

    db.execute("UPDATE participant SET status='已取消' WHERE id=?", (pid,))
    db.commit()
    db.close()
    return jsonify({'message': '参加者已取消'})


@app.route('/api/applications/<apply_no>/change-responsible', methods=['POST'])
@login_required
@role_required('receptionist')
def change_responsible(apply_no):
    data = request.json
    new_resp_id = data['new_responsible_id']
    db = get_db()

    # 取消原责任人标记
    db.execute(
        "UPDATE participant SET is_responsible=0 WHERE apply_no=? AND is_responsible=1",
        (apply_no,)
    )
    # 设置新责任人
    db.execute(
        "UPDATE participant SET is_responsible=1 WHERE id=? AND apply_no=?",
        (new_resp_id, apply_no)
    )
    # 更新申请表
    new_resp = db.execute("SELECT * FROM participant WHERE id=?", (new_resp_id,)).fetchone()
    db.execute(
        "UPDATE application SET responsible_name=?, responsible_phone=? WHERE apply_no=?",
        (new_resp['name'], new_resp['phone'], apply_no)
    )
    db.commit()
    db.close()
    return jsonify({'message': '申请责任人已变更'})


# ==================== 余款支付 ====================

@app.route('/api/balance/pending', methods=['GET'])
@login_required
@role_required('collector')
def get_pending_balance():
    db = get_db()
    rows = db.execute(
        '''SELECT ap.*, g.departure_date, a.activity_name, r.route_name,
                  COALESCE(SUM(CASE WHEN p.pay_type IN ('订金','余款') THEN p.amount ELSE 0 END), 0) as paid_total
           FROM application ap
           JOIN tour_group g ON ap.group_code=g.group_code
           JOIN activity a ON g.activity_code=a.activity_code
           JOIN route r ON a.route_code=r.route_code
           LEFT JOIN payment p ON ap.apply_no=p.apply_no
           WHERE ap.status='进行中'
           GROUP BY ap.apply_no
           HAVING paid_total < ap.total_fee
           ORDER BY g.departure_date'''
    ).fetchall()
    db.close()
    return jsonify(rows_to_list(rows))


@app.route('/api/applications/<apply_no>/pay-balance', methods=['POST'])
@login_required
@role_required('collector')
def pay_balance(apply_no):
    data = request.json
    db = get_db()

    app_row = db.execute("SELECT * FROM application WHERE apply_no=?", (apply_no,)).fetchone()
    if not app_row:
        db.close()
        return jsonify({'error': '申请不存在'}), 404

    if app_row['status'] != '进行中':
        db.close()
        return jsonify({'error': '该申请已完结，无法支付余款'}), 400

    paid = get_paid_amount(db, apply_no)

    remaining = app_row['total_fee'] - paid
    amount = data.get('amount', remaining)

    if amount > remaining:
        db.close()
        return jsonify({'error': f'支付金额超出待付余额 ¥{remaining}'}), 400

    try:
        pay_no = gen_payment_no()
        db.execute(
            "INSERT INTO payment (payment_no, apply_no, amount, pay_type, pay_method) VALUES (?,?,?,?,?)",
            (pay_no, apply_no, amount, '余款', data.get('pay_method', '现金'))
        )
        # 如果全额付清，更新申请状态
        if paid + amount >= app_row['total_fee']:
            db.execute("UPDATE application SET status='已完成' WHERE apply_no=?", (apply_no,))
        db.commit()
        return jsonify({
            'message': '余款支付成功',
            'payment_no': pay_no,
            'paid_amount': amount,
            'fully_paid': paid + amount >= app_row['total_fee']
        })
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()


# ==================== 计算订金（供前端调用） ====================

@app.route('/api/calc-deposit', methods=['POST'])
@login_required
@role_required('receptionist')
def api_calc_deposit():
    data = request.json
    departure = date.fromisoformat(data['departure_date'])
    result = calc_deposit(departure, data['adult_count'], data['child_count'])
    return jsonify(result)


# ==================== 余款截止检查 ====================

def auto_cancel_overdue():
    """启动时自动取消余款逾期且未付清的申请（仅限未出发的）"""
    db = get_db()
    today = date.today().isoformat()

    rows = db.execute(
        '''SELECT ap.*, g.balance_deadline, g.departure_date
           FROM application ap
           JOIN tour_group g ON ap.group_code=g.group_code
           WHERE ap.status='进行中'
           AND g.balance_deadline IS NOT NULL
           AND g.balance_deadline < ?
           AND g.departure_date >= ?''',
        (today, today)
    ).fetchall()

    cancelled = []
    for row in rows:
        apply_no = row['apply_no']
        paid = get_paid_amount(db, apply_no)
        if paid < row['total_fee']:
            departure = date.fromisoformat(row['departure_date'])
            fee_info = calc_cancel_fee(departure, paid)

            try:
                db.execute("UPDATE application SET status='已取消' WHERE apply_no=?", (apply_no,))
                db.execute("UPDATE participant SET status='已取消' WHERE apply_no=?", (apply_no,))
                db.execute(
                    "UPDATE tour_group SET current_count=current_count-? WHERE group_code=?",
                    (row['adult_count'] + row['child_count'], row['group_code'])
                )
                if fee_info['refund'] > 0:
                    refund_no = gen_payment_no()
                    db.execute(
                        "INSERT INTO payment (payment_no, apply_no, amount, pay_type, pay_method) VALUES (?,?,?,?,?)",
                        (refund_no, apply_no, -fee_info['refund'], '退款', '银行转账')
                    )
                cancelled.append({
                    'apply_no': apply_no,
                    'responsible_name': row['responsible_name'],
                    'fee_info': fee_info
                })
            except Exception:
                continue

    db.commit()
    db.close()

    if cancelled:
        print(f"[auto_cancel] cancelled {len(cancelled)} overdue application(s)")
        for c in cancelled:
            print(f"  - {c['apply_no']} refund={c['fee_info']['refund']}")

    return cancelled


@app.route('/api/check-balance-deadline', methods=['POST'])
@login_required
@role_required('admin', 'collector')
def check_balance_deadline_api():
    """API 接口：手动触发余款逾期检查"""
    cancelled = auto_cancel_overdue()
    return jsonify({
        'message': f'已自动取消 {len(cancelled)} 个逾期申请',
        'cancelled': cancelled
    })


@app.route('/api/pending-balance', methods=['GET'])
@login_required
@role_required('collector', 'admin')
def get_pending_balance_list():
    """获取即将到期的未付清申请列表"""
    db = get_db()
    today = date.today().isoformat()

    rows = db.execute(
        '''SELECT ap.*, g.balance_deadline, g.departure_date, r.route_name,
                  COALESCE(SUM(CASE WHEN p.pay_type IN ('订金','余款') THEN p.amount ELSE 0 END), 0) as paid_total
           FROM application ap
           JOIN tour_group g ON ap.group_code=g.group_code
           JOIN activity a ON g.activity_code=a.activity_code
           JOIN route r ON a.route_code=r.route_code
           LEFT JOIN payment p ON ap.apply_no=p.apply_no
           WHERE ap.status='进行中'
           AND g.balance_deadline IS NOT NULL
           GROUP BY ap.apply_no
           HAVING paid_total < ap.total_fee
           ORDER BY g.balance_deadline''',
    ).fetchall()

    db.close()
    return jsonify(rows_to_list(rows))


@app.route('/api/calc-cancel-fee', methods=['POST'])
@login_required
@role_required('receptionist')
def api_calc_cancel_fee():
    data = request.json
    departure = date.fromisoformat(data['departure_date'])
    result = calc_cancel_fee(departure, data['paid_amount'])
    return jsonify(result)


# ==================== 财务数据导出 ====================

@app.route('/api/finance/export', methods=['GET'])
@login_required
@role_required('accountant')
def get_finance_export():
    start = request.args.get('start')
    end = request.args.get('end')
    pay_type = request.args.get('type')

    db = get_db()
    sql = '''SELECT p.*, ap.responsible_name, g.departure_date, a.activity_name, r.route_name
             FROM payment p
             JOIN application ap ON p.apply_no=ap.apply_no
             JOIN tour_group g ON ap.group_code=g.group_code
             JOIN activity a ON g.activity_code=a.activity_code
             JOIN route r ON a.route_code=r.route_code
             WHERE 1=1'''
    params = []
    if start:
        sql += ' AND p.pay_date>=?'
        params.append(start)
    if end:
        sql += ' AND p.pay_date<=?'
        params.append(end)
    if pay_type:
        sql += ' AND p.pay_type=?'
        params.append(pay_type)
    sql += ' ORDER BY p.pay_date DESC'

    rows = db.execute(sql, params).fetchall()
    db.close()
    return jsonify(rows_to_list(rows))


@app.route('/api/finance/export', methods=['POST'])
@login_required
@role_required('accountant')
def export_finance():
    data = request.json or {}
    db = get_db()
    sql = "UPDATE payment SET exported=1 WHERE exported=0"
    params = []
    if data.get('start'):
        sql += ' AND pay_date>=?'
        params.append(data['start'])
    if data.get('end'):
        sql += ' AND pay_date<=?'
        params.append(data['end'])
    if data.get('type'):
        sql += ' AND pay_type=?'
        params.append(data['type'])
    db.execute(sql, params)
    count = db.execute("SELECT changes()").fetchone()[0]
    db.commit()
    db.close()
    return jsonify({'message': f'已导出 {count} 条记录到财务系统'})


# ==================== 统计数据 ====================

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    db = get_db()
    today = date.today().isoformat()
    month_start = date.today().replace(day=1).isoformat()

    monthly_apps = db.execute(
        "SELECT COUNT(*) FROM application WHERE apply_date>=?", (month_start,)
    ).fetchone()[0]

    today_apps = db.execute(
        "SELECT COUNT(*) FROM application WHERE apply_date=?", (today,)
    ).fetchone()[0]

    pending_balance = db.execute(
        '''SELECT COUNT(*) FROM application ap
           WHERE ap.status='进行中' AND ap.deposit < ap.total_fee'''
    ).fetchone()[0]

    upcoming_groups = db.execute(
        "SELECT COUNT(*) FROM tour_group WHERE departure_date>=? AND status='已开放'",
        (today,)
    ).fetchone()[0]

    db.close()
    return jsonify({
        'monthly_applications': monthly_apps,
        'today_applications': today_apps,
        'pending_balance': pending_balance,
        'upcoming_groups': upcoming_groups
    })


# ==================== 前端页面 ====================

@app.route('/')
@app.route('/<path:path>')
def serve_frontend(path=''):
    """Vue 前端入口：静态文件直接返回，其余返回 index.html"""
    if path and os.path.exists(os.path.join(STATIC_DIR, path)):
        return send_from_directory(STATIC_DIR, path)
    return send_from_directory(STATIC_DIR, 'index.html')


# ==================== 启动 ====================

if __name__ == '__main__':
    init_db()
    seed_data()
    auto_cancel_overdue()
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    print("旅游业务管理系统已启动")
    print("访问地址: http://localhost:5000")
    app.run(debug=debug_mode, port=5000)
