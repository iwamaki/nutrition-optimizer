"""Unit conversion service for ingredients."""

import re
from typing import Tuple


# 食材名 -> (1単位あたりのグラム数, 単位名)
UNIT_MAPPINGS: dict[str, Tuple[float, str]] = {
    # 野菜類
    'にんじん': (150, '本'),
    '玉ねぎ': (200, '個'),
    'じゃがいも': (150, '個'),
    'さつまいも': (200, '本'),
    'キャベツ': (1000, '玉'),
    'なす': (80, '本'),
    'トマト': (150, '個'),
    'ピーマン': (35, '個'),
    '小松菜': (200, '束'),
    'ほうれん草': (200, '束'),
    'ニラ': (100, '束'),
    'もやし': (200, '袋'),
    'ねぎ': (100, '本'),
    '青ねぎ': (100, '束'),
    '大根': (900, '本'),
    'ブロッコリー': (250, '株'),
    'かぼちゃ': (800, '個'),
    'オクラ': (10, '本'),
    'レタス': (600, '玉'),
    'きゅうり': (100, '本'),
    'ごぼう': (150, '本'),
    'れんこん': (150, '節'),
    '白菜': (1200, '株'),
    'セロリ': (100, '本'),
    # 薬味
    '生姜': (15, 'かけ'),
    'にんにく': (5, '片'),
    # 卵・豆腐
    '卵': (50, '個'),
    '木綿豆腐': (350, '丁'),
    '絹ごし豆腐': (350, '丁'),
    '油揚げ': (30, '枚'),
    '厚揚げ': (150, '枚'),
    # 肉類
    '鶏肉': (250, '枚'),
    'もも肉': (250, '枚'),
    '豚肉': (100, 'g'),
    '牛肉': (100, 'g'),
    'ベーコン': (18, '枚'),
    'ウインナー': (20, '本'),
    # 魚介類
    '鮭': (80, '切れ'),
    'さば': (100, '切れ'),
    'あじ': (150, '尾'),
    'えび': (15, '尾'),
    # 主食
    '白米': (150, '合'),
    'パスタ': (100, 'g'),
    'うどん': (200, '玉'),
    'そば': (130, '束'),
    '食パン': (60, '枚'),
    # その他
    '牛乳': (200, 'ml'),
    'コーン': (190, '缶'),
    '海苔': (3, '枚'),
    '焼き海苔': (3, '枚'),
    'わかめ': (5, 'g'),
}

# 食品成分表の名称を正規化するためのマッピング
FOOD_NAME_MAPPINGS = {
    '木綿豆腐': '木綿豆腐',
    '絹ごし豆腐': '絹ごし豆腐',
    '油揚げ': '油揚げ',
    '厚揚げ': '厚揚げ',
    '納豆': '納豆',
    'こめ': '白米',
    'こむぎ': '小麦',
    'こまつな': '小松菜',
    'だいず': '大豆',
    'あまのり': '海苔',
    'わかめ': 'わかめ',
    'たまねぎ': '玉ねぎ',
    'にんじん': 'にんじん',
    'キャベツ': 'キャベツ',
    'ピーマン': 'ピーマン',
    'もやし': 'もやし',
    'ねぎ': 'ねぎ',
    'だいこん': '大根',
    'はくさい': '白菜',
    'レタス': 'レタス',
    'きゅうり': 'きゅうり',
    'ごぼう': 'ごぼう',
    'れんこん': 'れんこん',
    'ブロッコリー': 'ブロッコリー',
    'かぼちゃ': 'かぼちゃ',
    'ほうれんそう': 'ほうれん草',
    'なす': 'なす',
    'トマト': 'トマト',
    'じゃがいも': 'じゃがいも',
    'さつまいも': 'さつまいも',
    'しょうが': '生姜',
    'にんにく': 'にんにく',
    'ぶたにく': '豚肉',
    '豚肉': '豚肉',
    'ぎゅうにく': '牛肉',
    '牛肉': '牛肉',
    'とりにく': '鶏肉',
    '鶏肉': '鶏肉',
    'さけ': '鮭',
    'さば': 'さば',
    'あじ': 'あじ',
    'えび': 'えび',
}


class UnitConverter:
    """単位変換サービス"""

    def convert_to_display_unit(
        self,
        food_name: str,
        amount_g: float,
    ) -> Tuple[str, str]:
        """
        グラム数を実用的な単位に変換

        Args:
            food_name: 食材名
            amount_g: グラム数

        Returns:
            (display_amount, unit): 例 ("2", "本") または ("約1.5", "束")
        """
        if food_name not in UNIT_MAPPINGS:
            # マッピングがない場合はgのまま
            if amount_g >= 1000:
                return (f"{amount_g / 1000:.1f}".rstrip('0').rstrip('.'), "kg")
            return (str(round(amount_g)), "g")

        grams_per_unit, unit = UNIT_MAPPINGS[food_name]

        # 特殊ケース: 単位がgやmlの場合はそのまま
        if unit in ('g', 'ml'):
            if amount_g >= 1000:
                return (f"{amount_g / 1000:.1f}".rstrip('0').rstrip('.'), "kg" if unit == 'g' else 'L')
            return (str(round(amount_g)), unit)

        # 単位数を計算
        unit_count = amount_g / grams_per_unit

        # 大きい野菜（玉・株・個で1個が大きいもの）は分数表示
        if grams_per_unit >= 500:
            if unit_count < 0.2:
                return (str(round(amount_g)), "g")
            elif unit_count < 0.4:
                display = "1/4"
            elif unit_count < 0.6:
                display = "1/2"
            elif unit_count < 0.9:
                display = "3/4"
            elif unit_count < 1.3:
                display = "1"
            else:
                display = f"約{round(unit_count * 2) / 2}"
            return (display, unit)

        # 通常の食材の端数処理（0.5単位で丸める）
        if unit_count < 0.3:
            return (str(round(amount_g)), "g")
        elif unit_count < 0.7:
            display = "1/2"
        elif unit_count < 1.3:
            display = "1"
        elif unit_count < 1.7:
            display = "1.5"
        elif unit_count < 2.3:
            display = "2"
        elif unit_count < 2.7:
            display = "2.5"
        elif unit_count < 3.3:
            display = "3"
        elif unit_count < 4:
            display = "3.5"
        elif unit_count < 5:
            display = "4"
        else:
            display = f"約{round(unit_count)}"

        return (display, unit)

    def normalize_food_name(self, raw_name: str) -> str:
        """
        食品成分表の名称を購入リスト用の簡潔な名前に変換

        Args:
            raw_name: 食品成分表の元の名前

        Returns:
            正規化された食材名
        """
        name = raw_name

        # 1. カテゴリ接頭辞を除去
        name = re.sub(r'＜[^＞]+＞', '', name)
        name = re.sub(r'（[^）]+類）', '', name)
        name = re.sub(r'［[^］]+］', '', name)

        # 2. 部位・状態を除去
        remove_words = [
            '全卵', 'りん茎', '塊茎', '塊根', '結球葉', '根茎',
            '果実', '根', '葉', '茎', '皮つき', '皮なし', '皮むき',
            '未熟種子', 'カーネル', '養殖', '主品目',
        ]
        for word in remove_words:
            name = name.replace(word, '')

        # 3. 調理法を除去
        cooking_methods = [
            '生', 'ゆで', '茹で', '焼き', '油いため', '蒸し',
            'フライ', '天ぷら', 'いり', '炒り', '素干し', '水戻し',
            '冷凍', '乾燥',
        ]
        for method in cooking_methods:
            name = re.sub(rf'\s*{method}\s*$', '', name)
            name = re.sub(rf'\s+{method}(?=\s|$)', '', name)

        # 4. 特定食材の読みやすい名前へのマッピング
        for key, value in FOOD_NAME_MAPPINGS.items():
            if key in name:
                return value

        # 5. 括弧内の補足情報を除去
        name = re.sub(r'（[^）]*）', '', name)
        name = re.sub(r'\([^)]*\)', '', name)

        # 6. 余分な空白を除去
        name = re.sub(r'\s+', ' ', name).strip()

        return name if name else raw_name
