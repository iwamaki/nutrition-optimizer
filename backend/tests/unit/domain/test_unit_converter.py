"""
UnitConverter のユニットテスト
"""
import pytest
from app.domain.services import UnitConverter


class TestUnitConverter:
    """UnitConverter のテスト"""

    @pytest.fixture
    def converter(self):
        return UnitConverter()

    def test_convert_to_display_unit_carrot(self, converter):
        """にんじんの単位変換テスト"""
        display, unit = converter.convert_to_display_unit("にんじん", 150)
        assert unit == "本"
        assert display == "1"

    def test_convert_to_display_unit_onion(self, converter):
        """玉ねぎの単位変換テスト"""
        display, unit = converter.convert_to_display_unit("玉ねぎ", 200)
        assert unit == "個"
        assert display == "1"

    def test_convert_to_display_unit_half_onion(self, converter):
        """玉ねぎ半分の単位変換テスト"""
        display, unit = converter.convert_to_display_unit("玉ねぎ", 100)
        assert unit == "個"
        assert display == "1/2"

    def test_convert_to_display_unit_egg(self, converter):
        """卵の単位変換テスト"""
        display, unit = converter.convert_to_display_unit("卵", 100)
        assert unit == "個"
        assert display == "2"

    def test_convert_to_display_unit_unknown(self, converter):
        """未知の食材はgで表示"""
        display, unit = converter.convert_to_display_unit("不明な食材", 150)
        assert unit == "g"
        assert display == "150"

    def test_convert_to_display_unit_large_amount(self, converter):
        """大量のグラム数はkgに変換"""
        display, unit = converter.convert_to_display_unit("不明な食材", 1500)
        assert unit == "kg"
        assert display == "1.5"

    def test_normalize_food_name_egg(self, converter):
        """鶏卵の正規化テスト"""
        result = converter.normalize_food_name("鶏卵　全卵　生")
        # 正規化結果を確認（実装に依存）
        assert "卵" in result or result == "鶏卵"

    def test_normalize_food_name_onion(self, converter):
        """玉ねぎの正規化テスト"""
        result = converter.normalize_food_name("＜野菜類＞たまねぎ　りん茎　生")
        assert result == "玉ねぎ"

    def test_normalize_food_name_carrot(self, converter):
        """にんじんの正規化テスト"""
        result = converter.normalize_food_name("＜野菜類＞にんじん　根　生")
        assert result == "にんじん"

    def test_normalize_food_name_chicken(self, converter):
        """鶏肉の正規化テスト"""
        result = converter.normalize_food_name("にわとり　もも　皮つき　生")
        # 正規化結果を確認（実装に依存）
        assert "鶏" in result or "もも" in result

    def test_normalize_food_name_salmon(self, converter):
        """鮭の正規化テスト"""
        result = converter.normalize_food_name("しろさけ　生")
        assert result == "鮭"

    def test_normalize_food_name_milk(self, converter):
        """牛乳の正規化テスト"""
        result = converter.normalize_food_name("普通牛乳")
        # 正規化結果を確認（実装に依存）
        assert "牛乳" in result

    def test_normalize_food_name_tofu(self, converter):
        """木綿豆腐の正規化テスト"""
        result = converter.normalize_food_name("木綿豆腐")
        assert result == "木綿豆腐"
