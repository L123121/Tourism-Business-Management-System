import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'travel.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.executescript('''
    CREATE TABLE IF NOT EXISTS route (
        route_code TEXT PRIMARY KEY,
        route_name TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT '活跃' CHECK(status IN ('活跃','已取消')),
        created_date TEXT DEFAULT (date('now'))
    );

    CREATE TABLE IF NOT EXISTS route_change_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        route_code TEXT NOT NULL,
        change_date TEXT DEFAULT (date('now')),
        content TEXT NOT NULL,
        operator TEXT,
        FOREIGN KEY (route_code) REFERENCES route(route_code)
    );

    CREATE TABLE IF NOT EXISTS activity (
        activity_code TEXT PRIMARY KEY,
        activity_name TEXT NOT NULL,
        description TEXT,
        route_code TEXT NOT NULL,
        FOREIGN KEY (route_code) REFERENCES route(route_code)
    );

    CREATE TABLE IF NOT EXISTS tour_group (
        group_code TEXT PRIMARY KEY,
        activity_code TEXT NOT NULL,
        departure_date TEXT NOT NULL,
        deadline TEXT NOT NULL,
        capacity INTEGER NOT NULL,
        current_count INTEGER DEFAULT 0,
        status TEXT DEFAULT '未开放' CHECK(status IN ('未开放','已开放','已截止','已完成')),
        FOREIGN KEY (activity_code) REFERENCES activity(activity_code)
    );

    CREATE TABLE IF NOT EXISTS price (
        group_code TEXT PRIMARY KEY,
        adult_price REAL,
        child_price REAL,
        discount TEXT,
        is_published INTEGER DEFAULT 0,
        FOREIGN KEY (group_code) REFERENCES tour_group(group_code)
    );

    CREATE TABLE IF NOT EXISTS application (
        apply_no TEXT PRIMARY KEY,
        group_code TEXT NOT NULL,
        apply_date TEXT DEFAULT (date('now')),
        responsible_name TEXT NOT NULL,
        responsible_phone TEXT NOT NULL,
        responsible_idcard TEXT,
        adult_count INTEGER NOT NULL,
        child_count INTEGER NOT NULL,
        deposit REAL NOT NULL,
        total_fee REAL,
        status TEXT DEFAULT '进行中' CHECK(status IN ('进行中','已完成','已取消')),
        FOREIGN KEY (group_code) REFERENCES tour_group(group_code)
    );

    CREATE TABLE IF NOT EXISTS participant (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        apply_no TEXT NOT NULL,
        name TEXT NOT NULL,
        gender TEXT CHECK(gender IN ('男','女')),
        age INTEGER,
        idcard TEXT,
        type TEXT CHECK(type IN ('大人','小孩')),
        phone TEXT,
        is_responsible INTEGER DEFAULT 0,
        status TEXT DEFAULT '已录入' CHECK(status IN ('已录入','已取消')),
        FOREIGN KEY (apply_no) REFERENCES application(apply_no)
    );

    CREATE TABLE IF NOT EXISTS payment (
        payment_no TEXT PRIMARY KEY,
        apply_no TEXT NOT NULL,
        amount REAL NOT NULL,
        pay_date TEXT DEFAULT (date('now')),
        pay_type TEXT CHECK(pay_type IN ('订金','余款','退款')),
        pay_method TEXT,
        exported INTEGER DEFAULT 0,
        FOREIGN KEY (apply_no) REFERENCES application(apply_no)
    );
    ''')

    conn.commit()
    conn.close()


def seed_data():
    conn = get_db()
    cur = conn.cursor()

    # 检查是否已有数据
    count = cur.execute("SELECT COUNT(*) FROM route").fetchone()[0]
    if count > 0:
        conn.close()
        return

    # 旅游路线
    routes = [
        ('R-001', '云南昆明-大理-丽江6日游', '游览昆明石林、大理古城、丽江古城、玉龙雪山'),
        ('R-002', '北京5日游', '游览故宫、长城、颐和园、天坛'),
        ('R-003', '海南三亚4日游', '游览亚龙湾、天涯海角、南山寺'),
        ('R-004', '四川成都-九寨沟5日游', '游览成都武侯祠、九寨沟、黄龙'),
        ('R-005', '桂林3日游', '游览漓江、阳朔、象鼻山'),
        ('R-006', '西安-华山4日游', '游览兵马俑、华山、大雁塔'),
    ]
    cur.executemany("INSERT INTO route VALUES (?,?,?,?,?)",
                    [(r[0], r[1], r[2], '活跃' if r[0] != 'R-006' else '已取消', '2026-01-15' if r[0] == 'R-001' else '2026-02-01') for r in routes])

    # 路线变更历史
    logs = [
        ('R-001', '2026-03-10', '新增旅游活动：丽江古城夜游', '王磊'),
        ('R-002', '2026-02-20', '新增旅游活动：故宫深度游', '王磊'),
        ('R-006', '2025-12-15', '路线取消（缺乏吸引力）', '王磊'),
        ('R-004', '2026-04-01', '新增旅游活动：黄龙景区', '王磊'),
    ]
    cur.executemany("INSERT INTO route_change_log (route_code, change_date, content, operator) VALUES (?,?,?,?)", logs)

    # 旅游活动
    activities = [
        ('A-001', '昆明石林游览', '游览世界自然遗产石林风景区', 'R-001'),
        ('A-002', '大理古城-洱海', '游览大理古城、环洱海骑行', 'R-001'),
        ('A-003', '丽江古城-玉龙雪山', '游览丽江古城、玉龙雪山', 'R-001'),
        ('A-004', '故宫-天坛', '游览故宫博物院、天坛公园', 'R-002'),
        ('A-005', '长城游览', '游览八达岭长城', 'R-002'),
        ('A-006', '亚龙湾-天涯海角', '游览亚龙湾海滩、天涯海角景区', 'R-003'),
        ('A-007', '九寨沟-黄龙', '游览九寨沟、黄龙景区', 'R-004'),
        ('A-008', '漓江-阳朔', '游览漓江风光、阳朔西街', 'R-005'),
    ]
    cur.executemany("INSERT INTO activity VALUES (?,?,?,?)", activities)

    # 旅游团
    groups = [
        ('YN-20260615', 'A-003', '2026-06-15', '2026-06-08', 30, 22, '已开放'),
        ('YN-20260701', 'A-003', '2026-07-01', '2026-06-24', 25, 10, '已开放'),
        ('YN-20260620', 'A-002', '2026-06-20', '2026-06-13', 20, 18, '已开放'),
        ('YN-20260510', 'A-001', '2026-05-10', '2026-05-03', 30, 28, '已截止'),
        ('BJ-20260701', 'A-004', '2026-07-01', '2026-06-24', 40, 15, '已开放'),
        ('HN-20260720', 'A-006', '2026-07-20', '2026-07-13', 35, 8, '已开放'),
        ('SC-20260801', 'A-007', '2026-08-01', '2026-07-25', 25, 5, '已开放'),
    ]
    cur.executemany("INSERT INTO tour_group VALUES (?,?,?,?,?,?,?)", groups)

    # 价格
    prices = [
        ('YN-20260615', 3200, 2400, '满4人减200元', 1),
        ('YN-20260701', 2800, 2100, '满3人减150元', 1),
        ('BJ-20260701', 4000, 3000, '无', 1),
        ('HN-20260720', 3500, 2600, '早鸟优惠减300元', 0),
    ]
    cur.executemany("INSERT INTO price VALUES (?,?,?,?,?)", prices)

    # 申请
    applications = [
        ('AP-20260501-001', 'YN-20260615', '2026-05-01', '张三', '13800138001', '420106199001011234', 3, 1, 2400, 12000, '进行中'),
        ('AP-20260502-003', 'BJ-20260701', '2026-05-02', '李四', '13800138002', '420106199002021234', 2, 0, 1600, 8000, '进行中'),
        ('AP-20260428-005', 'HN-20260720', '2026-04-28', '王五', '13800138003', '420106199003031234', 4, 2, 3600, 18000, '已完成'),
        ('AP-20260430-002', 'SC-20260801', '2026-04-30', '赵六', '13800138004', '420106199004041234', 2, 1, 1800, 9000, '已完成'),
        ('AP-20260503-001', 'YN-20260615', '2026-05-03', '孙七', '13800138005', '420106199005051234', 5, 0, 3000, 15000, '进行中'),
    ]
    cur.executemany("INSERT INTO application VALUES (?,?,?,?,?,?,?,?,?,?,?)", applications)

    # 参加者
    participants = [
        ('AP-20260501-001', '张三', '男', 35, '420106199001011234', '大人', '13800138001', 1, '已录入'),
        ('AP-20260501-001', '李芳', '女', 33, '420106199001021234', '大人', '13800138006', 0, '已录入'),
        ('AP-20260501-001', '王强', '男', 36, '420106199001031234', '大人', '13800138007', 0, '已录入'),
        ('AP-20260501-001', '张小明', '男', 8, '420106199001041234', '小孩', None, 0, '已录入'),
        ('AP-20260502-003', '李四', '男', 40, '420106199002021234', '大人', '13800138002', 1, '已录入'),
        ('AP-20260502-003', '李四妻子', '女', 38, '420106199002051234', '大人', None, 0, '已录入'),
    ]
    cur.executemany("INSERT INTO participant (apply_no,name,gender,age,idcard,type,phone,is_responsible,status) VALUES (?,?,?,?,?,?,?,?,?)", participants)

    # 支付记录
    payments = [
        ('PAY-20260501-001', 'AP-20260501-001', 2400, '2026-05-01', '订金', '现金', 1),
        ('PAY-20260502-001', 'AP-20260502-003', 1600, '2026-05-02', '订金', '微信支付', 1),
        ('PAY-20260428-001', 'AP-20260428-005', 3600, '2026-04-28', '订金', '银行转账', 1),
        ('PAY-20260428-002', 'AP-20260428-005', 14400, '2026-04-30', '余款', '银行转账', 1),
        ('PAY-20260430-001', 'AP-20260430-002', 1800, '2026-04-30', '订金', '支付宝', 1),
        ('PAY-20260430-002', 'AP-20260430-002', 7200, '2026-05-05', '余款', '支付宝', 1),
        ('PAY-20260503-001', 'AP-20260503-001', 3000, '2026-05-03', '订金', '现金', 1),
    ]
    cur.executemany("INSERT INTO payment VALUES (?,?,?,?,?,?,?)", payments)

    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
    seed_data()
    print("数据库初始化完成")
