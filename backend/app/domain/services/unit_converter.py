"""Unit conversion service for ingredients."""

import re
from typing import Tuple


# 調味料の大さじ・小さじグラム数
# (大さじ1のg数, 小さじ1のg数)
SEASONING_MAPPINGS: dict[str, Tuple[float, float]] = {
    '醤油': (18, 6),
    'しょうゆ': (18, 6),
    'みりん': (18, 6),
    '砂糖': (9, 3),
    '塩': (18, 6),
    '酢': (15, 5),
    'サラダ油': (12, 4),
    'マヨネーズ': (12, 4),
    'ケチャップ': (15, 5),
    'ソース': (15, 5),
    '料理酒': (15, 5),
    'ごま油': (12, 4),
    'オリーブ油': (12, 4),
    'めんつゆ': (15, 5),
    '味噌': (18, 6),
    'バター': (12, 4),
    'ポン酢': (15, 5),
    'オイスターソース': (18, 6),
    '豆板醤': (18, 6),
    'コンソメ': (9, 3),
    'こしょう': (6, 2),
}

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
    '赤パプリカ': (150, '個'),
    '黄パプリカ': (150, '個'),
    '小松菜': (200, '束'),
    'ほうれん草': (200, '束'),
    'ニラ': (100, '束'),
    'にら': (100, '束'),
    'もやし': (200, '袋'),
    'ねぎ': (100, '本'),
    '長ねぎ': (100, '本'),
    '青ねぎ': (100, '束'),
    '大根': (900, '本'),
    'ブロッコリー': (250, '株'),
    'カリフラワー': (400, '株'),
    'かぼちゃ': (800, '個'),
    'オクラ': (10, '本'),
    'レタス': (600, '玉'),
    'きゅうり': (100, '本'),
    'ごぼう': (150, '本'),
    'れんこん': (150, '節'),
    '白菜': (1200, '株'),
    'セロリ': (100, '本'),
    'ズッキーニ': (150, '本'),
    'アスパラガス': (20, '本'),
    # きのこ類
    'しいたけ': (15, '個'),
    'えのき': (100, '袋'),
    'しめじ': (100, 'パック'),
    'まいたけ': (100, 'パック'),
    'エリンギ': (40, '本'),
    # 薬味
    '生姜': (15, 'かけ'),
    'しょうが': (15, 'かけ'),
    'にんにく': (5, '片'),
    '大葉': (1, '枚'),
    'みょうが': (15, '個'),
    '三つ葉': (50, '束'),
    # 卵・豆腐
    '卵': (50, '個'),
    '木綿豆腐': (350, '丁'),
    '絹ごし豆腐': (350, '丁'),
    '豆腐': (350, '丁'),
    '油揚げ': (30, '枚'),
    '厚揚げ': (150, '枚'),
    '納豆': (50, 'パック'),
    # 肉類
    '鶏肉': (250, '枚'),
    'もも肉': (250, '枚'),
    '鶏もも肉': (250, '枚'),
    '鶏むね肉': (250, '枚'),
    'ささみ': (50, '本'),
    '豚肉': (100, 'g'),
    '牛肉': (100, 'g'),
    'ベーコン': (18, '枚'),
    'ウインナー': (20, '本'),
    'ハム': (10, '枚'),
    # 魚介類
    '鮭': (80, '切れ'),
    'さば': (100, '切れ'),
    'サバ': (100, '切れ'),
    'あじ': (150, '尾'),
    'えび': (15, '尾'),
    'いか': (200, '杯'),
    'たこ': (100, 'g'),
    'あさり': (200, 'パック'),
    'しじみ': (200, 'パック'),
    'ホタテ': (30, '個'),
    'ツナ缶': (70, '缶'),
    'しらす': (30, 'パック'),
    # 主食
    '白米': (150, '合'),
    '米': (150, '合'),
    'パスタ': (100, 'g'),
    'うどん': (200, '玉'),
    'そば': (130, '束'),
    '食パン': (60, '枚'),
    # 乳製品
    '牛乳': (200, 'ml'),
    'チーズ': (20, '枚'),
    'ヨーグルト': (100, 'g'),
    '生クリーム': (200, 'ml'),
    # その他
    'コーン': (190, '缶'),
    '海苔': (3, '枚'),
    '焼き海苔': (3, '枚'),
    'わかめ': (5, 'g'),
    'ひじき': (10, 'g'),
    'アーモンド': (1, '粒'),
    'ごま': (3, 'g'),
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
        # 調味料の場合は大さじ・小さじに変換
        if food_name in SEASONING_MAPPINGS:
            return self._convert_seasoning(food_name, amount_g)

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

    def _convert_seasoning(
        self,
        name: str,
        amount_g: float,
    ) -> Tuple[str, str]:
        """
        調味料のグラム数を大さじ・小さじに変換

        Args:
            name: 調味料名
            amount_g: グラム数

        Returns:
            (display_amount, unit): 例 ("大さじ1", "") または ("小さじ2", "")
        """
        tbsp_g, tsp_g = SEASONING_MAPPINGS[name]

        # 大さじ数と小さじ数を計算
        tbsp_count = amount_g / tbsp_g
        tsp_count = amount_g / tsp_g

        # 少量（小さじ1未満）はgで表示
        if tsp_count < 0.8:
            return (str(round(amount_g)), "g")

        # 小さじで表現（小さじ3未満 = 大さじ1未満）
        if tbsp_count < 0.8:
            if tsp_count < 1.3:
                return ("小さじ1", "")
            elif tsp_count < 1.8:
                return ("小さじ1.5", "")
            elif tsp_count < 2.3:
                return ("小さじ2", "")
            else:
                return ("小さじ2.5", "")

        # 大さじで表現
        if tbsp_count < 1.3:
            return ("大さじ1", "")
        elif tbsp_count < 1.8:
            return ("大さじ1.5", "")
        elif tbsp_count < 2.3:
            return ("大さじ2", "")
        elif tbsp_count < 2.8:
            return ("大さじ2.5", "")
        elif tbsp_count < 3.3:
            return ("大さじ3", "")
        else:
            # 大さじ3以上は整数で表示
            return (f"大さじ{round(tbsp_count)}", "")

    def convert_with_db_unit(
        self,
        amount_g: float,
        unit_g: float | None,
        unit_name: str | None,
    ) -> Tuple[str, str]:
        """
        DBの単位情報を使ってグラム数を変換

        Args:
            amount_g: グラム数
            unit_g: 1単位あたりのグラム数（DBから）
            unit_name: 単位名（DBから）

        Returns:
            (display_amount, unit): 例 ("2", "本") または ("大さじ1", "")
        """
        # 単位情報がない場合はgのまま
        if not unit_g or not unit_name:
            if amount_g >= 1000:
                return (f"{amount_g / 1000:.1f}".rstrip('0').rstrip('.'), "kg")
            return (str(round(amount_g)), "g")

        # 調味料（大さじ）の場合
        if unit_name == "大さじ":
            tbsp_g = unit_g
            tsp_g = unit_g / 3  # 小さじは大さじの1/3

            tbsp_count = amount_g / tbsp_g
            tsp_count = amount_g / tsp_g

            # 少量は少々
            if tsp_count < 0.5:
                return ("少々", "")
            if tsp_count < 0.8:
                return ("小さじ1/2", "")

            # 小さじで表現
            if tbsp_count < 0.8:
                if tsp_count < 1.3:
                    return ("小さじ1", "")
                elif tsp_count < 1.8:
                    return ("小さじ1.5", "")
                elif tsp_count < 2.3:
                    return ("小さじ2", "")
                else:
                    return ("小さじ2.5", "")

            # 大さじで表現
            if tbsp_count < 1.3:
                return ("大さじ1", "")
            elif tbsp_count < 1.8:
                return ("大さじ1.5", "")
            elif tbsp_count < 2.3:
                return ("大さじ2", "")
            elif tbsp_count < 2.8:
                return ("大さじ2.5", "")
            elif tbsp_count < 3.3:
                return ("大さじ3", "")
            else:
                return (f"大さじ{round(tbsp_count)}", "")

        # g/mlの場合はそのまま
        if unit_name in ('g', 'ml'):
            if amount_g >= 1000:
                return (f"{amount_g / 1000:.1f}".rstrip('0').rstrip('.'), "kg" if unit_name == 'g' else 'L')
            return (str(round(amount_g)), unit_name)

        # 通常の単位
        unit_count = amount_g / unit_g

        # 大きい野菜（1個500g以上）は分数表示
        if unit_g >= 500:
            if unit_count < 0.2:
                return (str(round(amount_g)), "g")
            elif unit_count < 0.4:
                return ("1/4", unit_name)
            elif unit_count < 0.6:
                return ("1/2", unit_name)
            elif unit_count < 0.9:
                return ("3/4", unit_name)
            elif unit_count < 1.3:
                return ("1", unit_name)
            else:
                return (f"約{round(unit_count * 2) / 2}", unit_name)

        # 通常の食材の端数処理
        if unit_count < 0.3:
            return (str(round(amount_g)), "g")
        elif unit_count < 0.7:
            return ("1/2", unit_name)
        elif unit_count < 1.3:
            return ("1", unit_name)
        elif unit_count < 1.7:
            return ("1.5", unit_name)
        elif unit_count < 2.3:
            return ("2", unit_name)
        elif unit_count < 2.7:
            return ("2.5", unit_name)
        elif unit_count < 3.3:
            return ("3", unit_name)
        elif unit_count < 4:
            return ("3.5", unit_name)
        elif unit_count < 5:
            return ("4", unit_name)
        else:
            return (f"約{round(unit_count)}", unit_name)

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
