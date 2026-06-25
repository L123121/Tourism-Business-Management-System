"""业务规则纯单元测试 —— 不依赖数据库

对应 PDF:
  - 第 3 页：assertEqual 判断结果与预期值是否相符
  - 第 6 页：mock 对象控制依赖行为（mock date.today()）
  - 第 22-27 页：方法测试中使用 mock 保持测试独立性

被测函数：calc_deposit(), calc_cancel_fee()
它们都是纯计算函数，唯一的外部依赖是 date.today()。
"""

import unittest
from unittest.mock import patch
from datetime import date
from app import calc_deposit, calc_cancel_fee


# ========================================================================
# 订金计算测试
# 规则：days>=60 -> 300/人；30<=days<60 -> 600/人；
#       15<=days<30 -> 1000/人；days<15 -> 600/人（简化）
# ========================================================================

class TestCalcDeposit(unittest.TestCase):
    """calc_deposit 单元测试 —— 覆盖所有阶梯及边界"""

    # -------- 正常阶梯测试 --------

    @patch('app.date')
    def test_60_days_above_300_per_person(self, mock_date):
        """出发前 >=60 天：每人 300 元"""
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_deposit(departure_date=date(2026, 3, 2), adult=2, child=0)
        self.assertEqual(result['per_person'], 300)
        self.assertEqual(result['total'], 600)

    @patch('app.date')
    def test_60_days_above_with_children(self, mock_date):
        """出发前 >=60 天，儿童同样计费"""
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_deposit(departure_date=date(2026, 3, 3), adult=2, child=1)
        self.assertEqual(result['per_person'], 300)
        self.assertEqual(result['total'], 900)   # 300 × 3

    @patch('app.date')
    def test_30_to_59_days_600_per_person(self, mock_date):
        """30 <= 出发前 < 60 天：每人 600 元"""
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_deposit(departure_date=date(2026, 1, 31), adult=3, child=0)
        self.assertEqual(result['per_person'], 600)
        self.assertEqual(result['total'], 1800)

    @patch('app.date')
    def test_15_to_29_days_1000_per_person(self, mock_date):
        """15 <= 出发前 < 30 天：每人 1000 元"""
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_deposit(departure_date=date(2026, 1, 20), adult=1, child=1)
        self.assertEqual(result['per_person'], 1000)
        self.assertEqual(result['total'], 2000)

    @patch('app.date')
    def test_less_than_15_days_fallback(self, mock_date):
        """出发前 < 15 天：简化规则 600 元/人"""
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_deposit(departure_date=date(2026, 1, 10), adult=1, child=0)
        self.assertEqual(result['per_person'], 600)
        self.assertEqual(result['days'], 9)

    # -------- 边界测试 --------

    @patch('app.date')
    def test_boundary_exactly_60_days(self, mock_date):
        """边界：刚好 60 天 -> 300 元/人"""
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_deposit(departure_date=date(2026, 3, 2), adult=1, child=0)
        self.assertEqual(result['per_person'], 300)

    @patch('app.date')
    def test_boundary_59_days(self, mock_date):
        """边界：59 天 -> 600 元/人"""
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_deposit(departure_date=date(2026, 3, 1), adult=1, child=0)
        self.assertEqual(result['per_person'], 600)

    @patch('app.date')
    def test_boundary_exactly_30_days(self, mock_date):
        """边界：刚好 30 天 -> 600 元/人"""
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_deposit(departure_date=date(2026, 1, 31), adult=1, child=0)
        self.assertEqual(result['per_person'], 600)

    @patch('app.date')
    def test_boundary_29_days(self, mock_date):
        """边界：29 天 -> 1000 元/人"""
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_deposit(departure_date=date(2026, 1, 30), adult=1, child=0)
        self.assertEqual(result['per_person'], 1000)

    @patch('app.date')
    def test_boundary_exactly_15_days(self, mock_date):
        """边界：刚好 15 天 -> 1000 元/人"""
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_deposit(departure_date=date(2026, 1, 16), adult=1, child=0)
        self.assertEqual(result['per_person'], 1000)

    @patch('app.date')
    def test_boundary_14_days(self, mock_date):
        """边界：14 天 -> 600 元/人 (fallback)"""
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_deposit(departure_date=date(2026, 1, 15), adult=1, child=0)
        self.assertEqual(result['per_person'], 600)

    # -------- 特殊值 --------

    @patch('app.date')
    def test_zero_participants(self, mock_date):
        """人数为 0 时总订金为 0"""
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_deposit(departure_date=date(2026, 6, 1), adult=0, child=0)
        self.assertEqual(result['total'], 0)

    @patch('app.date')
    def test_large_group(self, mock_date):
        """大团（50人）也能正确计算
        距出发120天 >= 60，所以 per_person=300"""
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_deposit(departure_date=date(2026, 5, 1), adult=50, child=0)
        self.assertEqual(result['per_person'], 300)
        self.assertEqual(result['total'], 50 * 300)   # 15000


# ========================================================================
# 取消手续费测试
# 规则：days>=30 -> 10%；15<=days<30 -> 30%；
#       7<=days<15 -> 50%；days<7 -> 100%
# ========================================================================

class TestCalcCancelFee(unittest.TestCase):
    """calc_cancel_fee 单元测试 —— 覆盖所有阶梯及边界"""

    @patch('app.date')
    def test_30_days_above_10_percent(self, mock_date):
        """出发前 >=30 天：扣 10%"""
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_cancel_fee(departure_date=date(2026, 2, 1), paid_amount=1000)
        self.assertEqual(result['rate'], 0.10)
        self.assertEqual(result['fee'], 100)
        self.assertEqual(result['refund'], 900)

    @patch('app.date')
    def test_15_to_29_days_30_percent(self, mock_date):
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_cancel_fee(departure_date=date(2026, 1, 20), paid_amount=2000)
        self.assertEqual(result['rate'], 0.30)
        self.assertEqual(result['fee'], 600)
        self.assertEqual(result['refund'], 1400)

    @patch('app.date')
    def test_7_to_14_days_50_percent(self, mock_date):
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_cancel_fee(departure_date=date(2026, 1, 12), paid_amount=2000)
        self.assertEqual(result['rate'], 0.50)
        self.assertEqual(result['fee'], 1000)
        self.assertEqual(result['refund'], 1000)

    @patch('app.date')
    def test_less_than_7_days_100_percent(self, mock_date):
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_cancel_fee(departure_date=date(2026, 1, 5), paid_amount=3000)
        self.assertEqual(result['rate'], 1.0)
        self.assertEqual(result['fee'], 3000)
        self.assertEqual(result['refund'], 0)

    # -------- 边界测试 --------

    @patch('app.date')
    def test_boundary_exactly_30_days(self, mock_date):
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_cancel_fee(departure_date=date(2026, 1, 31), paid_amount=1000)
        self.assertEqual(result['rate'], 0.10)

    @patch('app.date')
    def test_boundary_29_days(self, mock_date):
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_cancel_fee(departure_date=date(2026, 1, 30), paid_amount=1000)
        self.assertEqual(result['rate'], 0.30)

    @patch('app.date')
    def test_boundary_exactly_15_days(self, mock_date):
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_cancel_fee(departure_date=date(2026, 1, 16), paid_amount=1000)
        self.assertEqual(result['rate'], 0.30)

    @patch('app.date')
    def test_boundary_14_days(self, mock_date):
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_cancel_fee(departure_date=date(2026, 1, 15), paid_amount=1000)
        self.assertEqual(result['rate'], 0.50)

    @patch('app.date')
    def test_boundary_exactly_7_days(self, mock_date):
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_cancel_fee(departure_date=date(2026, 1, 8), paid_amount=1000)
        self.assertEqual(result['rate'], 0.50)

    @patch('app.date')
    def test_boundary_6_days(self, mock_date):
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_cancel_fee(departure_date=date(2026, 1, 7), paid_amount=1000)
        self.assertEqual(result['rate'], 1.0)

    # -------- 特殊值 --------

    @patch('app.date')
    def test_zero_paid_amount(self, mock_date):
        """未付任何费用时取消，手续费和退款均为 0"""
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_cancel_fee(departure_date=date(2026, 2, 1), paid_amount=0)
        self.assertEqual(result['fee'], 0)
        self.assertEqual(result['refund'], 0)

    @patch('app.date')
    def test_fee_rounding(self, mock_date):
        """验证小数点保留两位"""
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        result = calc_cancel_fee(departure_date=date(2026, 2, 1), paid_amount=333)
        self.assertEqual(result['fee'], 33.3)
        self.assertEqual(result['refund'], 299.7)


if __name__ == '__main__':
    unittest.main(verbosity=2)
