from flask import Flask, request, jsonify
from flask_cors import CORS
from database import get_db, init_db, seed_data
from datetime import date, timedelta

app = Flask(__name__)
CORS(app)


# ==================== 工具函数 ====================

def row_to_dict(row):
    return dict(row) if row else None


def rows_to_list(rows):
    return [dict(r) for r in rows]


def gen_apply_no(db=None):
    today = date.today().strftime('%Y%m%d')
    own_db = db is None
    if own_db:
        db = get_db()
    count = db.execute(
        "SELECT COUNT(*) FROM application WHERE apply_no LIKE ?",
        (f'AP-{today}-%',)
    ).fetchone()[0]
    if own_db:
        db.close()
    return f'AP-{today}-{count + 1:03d}'


def gen_payment_no(db=None):
    today = date.today().strftime('%Y%m%d')
    own_db = db is None
    if own_db:
        db = get_db()
    count = db.execute(
        "SELECT COUNT(*) FROM payment WHERE payment_no LIKE ?",
        (f'PAY-{today}-%',)
    ).fetchone()[0]
    if own_db:
        db.close()
    return f'PAY-{today}-{count + 1:03d}'


def get_paid_amount(db, apply_no):
    return db.execute(
        "SELECT COALESCE(SUM(amount),0) as total FROM payment WHERE apply_no=? AND pay_type IN ('订金','余款')",
        (apply_no,)
    ).fetchone()['total']


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


# ==================== 路线管理 ====================

@app.route('/api/routes', methods=['GET'])
def get_routes():
    db = get_db()
    rows = db.execute("SELECT * FROM route ORDER BY created_date DESC").fetchall()
    db.close()
    return jsonify(rows_to_list(rows))


@app.route('/api/routes', methods=['POST'])
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
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()


@app.route('/api/routes/<route_code>', methods=['GET'])
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
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()


@app.route('/api/activities/<activity_code>', methods=['PUT'])
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
def create_group():
    data = request.json
    db = get_db()
    try:
        db.execute(
            "INSERT INTO tour_group (group_code, activity_code, departure_date, deadline, capacity) VALUES (?,?,?,?,?)",
            (data['group_code'], data['activity_code'],
             data['departure_date'], data['deadline'], data['capacity'])
        )
        db.commit()
        return jsonify({'message': '旅游团创建成功'}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()


@app.route('/api/groups/<group_code>', methods=['GET'])
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
def get_price(group_code):
    db = get_db()
    row = db.execute("SELECT * FROM price WHERE group_code=?", (group_code,)).fetchone()
    db.close()
    if not row:
        return jsonify({'error': '价格未设定'}), 404
    return jsonify(row_to_dict(row))


@app.route('/api/prices/<group_code>', methods=['PUT'])
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
        "SELECT * FROM participant WHERE apply_no=? ORDER BY id", (apply_no,)
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

    apply_no = gen_apply_no(db)
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
        pay_no = gen_payment_no(db)
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
def cancel_application(apply_no):
    db = get_db()
    app_row = db.execute("SELECT * FROM application WHERE apply_no=?", (apply_no,)).fetchone()
    if not app_row:
        db.close()
        return jsonify({'error': '申请不存在'}), 404
    if app_row['status'] == '已取消':
        db.close()
        return jsonify({'error': '申请已取消'}), 400

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
            refund_no = gen_payment_no(db)
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
def get_participants(apply_no):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM participant WHERE apply_no=? AND status='已录入' ORDER BY id",
        (apply_no,)
    ).fetchall()
    db.close()
    return jsonify(rows_to_list(rows))


@app.route('/api/applications/<apply_no>/participants', methods=['POST'])
def add_participant(apply_no):
    data = request.json
    db = get_db()
    try:
        db.execute(
            '''INSERT INTO participant (apply_no, name, gender, age, idcard, type, phone)
               VALUES (?,?,?,?,?,?,?)''',
            (apply_no, data['name'], data['gender'], data['age'],
             data.get('idcard', ''), data['type'], data.get('phone', ''))
        )
        db.commit()
        return jsonify({'message': '参加者添加成功'}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()


@app.route('/api/participants/<int:pid>', methods=['PUT'])
def update_participant(pid):
    data = request.json
    db = get_db()
    db.execute(
        "UPDATE participant SET name=?, gender=?, age=?, idcard=?, type=?, phone=? WHERE id=?",
        (data['name'], data['gender'], data['age'],
         data.get('idcard', ''), data['type'], data.get('phone', ''), pid)
    )
    db.commit()
    db.close()
    return jsonify({'message': '参加者信息已更新'})


@app.route('/api/participants/<int:pid>/cancel', methods=['POST'])
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
def pay_balance(apply_no):
    data = request.json
    db = get_db()

    app_row = db.execute("SELECT * FROM application WHERE apply_no=?", (apply_no,)).fetchone()
    if not app_row:
        db.close()
        return jsonify({'error': '申请不存在'}), 404

    paid = get_paid_amount(db, apply_no)

    remaining = app_row['total_fee'] - paid
    amount = data.get('amount', remaining)

    if amount > remaining:
        db.close()
        return jsonify({'error': f'支付金额超出待付余额 ¥{remaining}'}), 400

    try:
        pay_no = gen_payment_no(db)
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
def api_calc_deposit():
    data = request.json
    departure = date.fromisoformat(data['departure_date'])
    result = calc_deposit(departure, data['adult_count'], data['child_count'])
    return jsonify(result)


@app.route('/api/calc-cancel-fee', methods=['POST'])
def api_calc_cancel_fee():
    data = request.json
    departure = date.fromisoformat(data['departure_date'])
    result = calc_cancel_fee(departure, data['paid_amount'])
    return jsonify(result)


# ==================== 财务数据导出 ====================

@app.route('/api/finance/export', methods=['GET'])
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
def export_finance():
    db = get_db()
    db.execute("UPDATE payment SET exported=1 WHERE exported=0")
    count = db.execute("SELECT changes()").fetchone()[0]
    db.commit()
    db.close()
    return jsonify({'message': f'已导出 {count} 条记录到财务系统'})


# ==================== 统计数据 ====================

@app.route('/api/stats', methods=['GET'])
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


# ==================== 启动 ====================

if __name__ == '__main__':
    init_db()
    seed_data()
    print("旅游业务管理系统后端已启动")
    print("API 地址: http://localhost:5000")
    app.run(debug=True, port=5000)
