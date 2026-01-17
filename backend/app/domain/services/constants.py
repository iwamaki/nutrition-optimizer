"""Domain constants for nutrition optimization."""

# コア栄養素（常に計算、8種類）
CORE_NUTRIENTS = [
    "calories", "protein", "fat", "carbohydrate", "fiber",
    "iron", "calcium", "vitamin_d"
]

# オプション栄養素（ユーザー選択可能、16種類）
OPTIONAL_NUTRIENTS = [
    # ミネラル
    "sodium", "potassium", "magnesium", "zinc",
    # ビタミン
    "vitamin_a", "vitamin_e", "vitamin_k",
    "vitamin_b1", "vitamin_b2", "vitamin_b6", "vitamin_b12",
    "niacin", "pantothenic_acid", "biotin",
    "folate", "vitamin_c"
]

# 全栄養素リスト（後方互換性のため維持）
ALL_NUTRIENTS = CORE_NUTRIENTS + [n for n in OPTIONAL_NUTRIENTS if n not in CORE_NUTRIENTS]
# 重複を除いた正しい順序
ALL_NUTRIENTS = [
    "calories", "protein", "fat", "carbohydrate", "fiber",
    # ミネラル
    "sodium", "potassium", "calcium", "magnesium", "iron", "zinc",
    # ビタミン
    "vitamin_a", "vitamin_d", "vitamin_e", "vitamin_k",
    "vitamin_b1", "vitamin_b2", "vitamin_b6", "vitamin_b12",
    "niacin", "pantothenic_acid", "biotin",
    "folate", "vitamin_c"
]


def get_enabled_nutrients(enabled_optional: list[str] | None = None) -> list[str]:
    """有効な栄養素リストを取得

    Args:
        enabled_optional: 有効にするオプション栄養素リスト（Noneの場合は全て有効）

    Returns:
        有効な栄養素名のリスト
    """
    if enabled_optional is None:
        return ALL_NUTRIENTS

    # コア栄養素は常に含める
    enabled = list(CORE_NUTRIENTS)

    # 指定されたオプション栄養素を追加
    for nutrient in enabled_optional:
        if nutrient in OPTIONAL_NUTRIENTS and nutrient not in enabled:
            enabled.append(nutrient)

    return enabled

# =============================================================================
# 耐容上限量（UL: Tolerable Upper Intake Level）
# 厚生労働省「日本人の食事摂取基準（2020年版）」より
# 推奨量(RDA)に対する倍率で定義。Noneは上限なし（通常の食事では過剰摂取の心配なし）
# =============================================================================
NUTRIENT_UPPER_LIMIT_RATIO: dict[str, float | None] = {
    # マクロ栄養素（上限なし、ただしカロリーは別途管理）
    "calories": 1.3,        # カロリーは1.3倍程度を上限とする
    "protein": None,        # 上限なし
    "fat": None,            # 上限なし（脂質エネルギー比で管理）
    "carbohydrate": None,   # 上限なし
    "fiber": None,          # 上限なし（むしろ多いほど良い）
    # ミネラル
    "sodium": 1.0,          # 特殊：目標量7.5g未満（減らす方向）
    "potassium": None,      # 上限なし
    "calcium": 3.3,         # 推奨750mg、上限2,500mg
    "magnesium": None,      # 食事からの上限なし（サプリは350mg）
    "iron": 6.7,            # 推奨7.5mg、上限50mg
    "zinc": 4.1,            # 推奨11mg、上限45mg
    # ビタミン
    "vitamin_a": 3.0,       # 推奨900μg、上限2,700μg
    "vitamin_d": 12.0,      # 推奨8.5μg、上限100μg
    "vitamin_e": 150.0,     # 推奨6mg、上限900mg（非常に高い）
    "vitamin_k": None,      # 上限なし
    "vitamin_b1": None,     # 上限なし
    "vitamin_b2": None,     # 上限なし
    "vitamin_b6": 43.0,     # 推奨1.4mg、上限60mg
    "vitamin_b12": None,    # 上限なし
    "niacin": 23.0,         # 推奨15mg、上限350mg
    "pantothenic_acid": None,  # 上限なし
    "biotin": None,         # 上限なし
    "folate": 4.2,          # 推奨240μg、上限1,000μg
    "vitamin_c": None,      # 上限なし
}

# 上限方向が目標の栄養素（減らす方向が良い）
# これらは100%以下を目指す（他の栄養素は100%以上を目指す）
UPPER_TARGET_NUTRIENTS = ["sodium"]

# =============================================================================
# 栄養素グループ定義（最適化の目標設定用）
# =============================================================================
# グループA（範囲型）: min ≤ x ≤ max を等しく重視
#   - エネルギー、脂質、炭水化物
# グループB（下限重視）: x ≥ min を強く目指す、ULがあれば x ≤ UL も制約
#   - たんぱく質、食物繊維、ビタミン類、ミネラル類
# グループC（上限重視）: x ≤ max を目指す（下限なし）
#   - 食塩（ナトリウム）

RANGE_TARGET_NUTRIENTS = ["calories", "fat", "carbohydrate"]  # グループA
# グループB: RANGE_TARGET_NUTRIENTSでもUPPER_TARGET_NUTRIENTSでもない栄養素
# グループC: UPPER_TARGET_NUTRIENTS（sodium）

# =============================================================================
# 最適化ペナルティ設定
# =============================================================================
# 目標は推奨量（100%）以上の摂取
SATURATION_THRESHOLD = 1.0

# ペナルティ係数
# 通常栄養素: 100%未満はペナルティ、100%〜上限はOK、上限超過はペナルティ
# ナトリウム: 100%超過はペナルティ、100%以下はOK
UNDER_PENALTY = 2.0      # 推奨量未達のペナルティ（不足は避けたい）
OVER_PENALTY = 0.5       # 推奨量超過のペナルティ（軽い、超えてもOK）
UPPER_LIMIT_PENALTY = 10.0  # 耐容上限量超過のペナルティ（強く抑制）

# 栄養素の重み（最適化時の優先度）
NUTRIENT_WEIGHTS = {
    "calories": 1.0,
    "protein": 1.5,
    "fat": 1.0,
    "carbohydrate": 1.0,
    "fiber": 1.2,
    # ミネラル
    "sodium": 0.8,  # 過剰摂取を避ける
    "potassium": 1.0,
    "calcium": 1.2,
    "magnesium": 1.0,
    "iron": 1.3,
    "zinc": 1.0,
    # ビタミン
    "vitamin_a": 1.0,
    "vitamin_d": 1.5,
    "vitamin_e": 0.8,
    "vitamin_k": 0.8,
    "vitamin_b1": 1.2,
    "vitamin_b2": 1.2,
    "vitamin_b6": 1.0,
    "vitamin_b12": 1.3,
    "niacin": 1.0,
    "pantothenic_acid": 0.8,
    "biotin": 0.8,
    "folate": 1.2,
    "vitamin_c": 1.0,
}

# 食事ごとのカロリー比率
MEAL_RATIOS = {
    "breakfast": 0.25,
    "lunch": 0.35,
    "dinner": 0.40,
}

# デフォルトのカテゴリ別品数制約（朝昼夜別プリセット）
DEFAULT_MEAL_CATEGORY_CONSTRAINTS = {
    "breakfast": {
        "主食": (1, 1),
        "主菜": (0, 1),
        "副菜": (0, 1),
        "汁物": (0, 0),
        "デザート": (0, 0),
    },
    "lunch": {
        "主食": (1, 1),
        "主菜": (1, 1),
        "副菜": (0, 1),
        "汁物": (0, 1),
        "デザート": (0, 0),
    },
    "dinner": {
        "主食": (1, 1),
        "主菜": (1, 1),
        "副菜": (1, 2),
        "汁物": (0, 1),
        "デザート": (0, 0),
    },
}

# volume（small/normal/large）からカテゴリ制約への変換
CATEGORY_CONSTRAINTS_BY_VOLUME = {
    "minimal": {
        "主食": (1, 1),
        "主菜": (0, 0),
        "副菜": (0, 0),
        "汁物": (0, 0),
        "デザート": (0, 0),
    },
    "light": {
        "主食": (1, 1),
        "主菜": (1, 1),
        "副菜": (0, 0),
        "汁物": (0, 0),
        "デザート": (0, 0),
    },
    "standard": {
        "主食": (1, 1),
        "主菜": (1, 1),
        "副菜": (1, 1),
        "汁物": (0, 1),
        "デザート": (0, 0),
    },
    "full": {
        "主食": (1, 1),
        "主菜": (1, 1),
        "副菜": (1, 2),
        "汁物": (1, 1),
        "デザート": (0, 1),
    },
    "japanese": {
        "主食": (1, 1),
        "主菜": (1, 1),
        "副菜": (2, 3),
        "汁物": (1, 1),
        "デザート": (0, 0),
    },
    # 後方互換（旧volume値）
    "small": {
        "主食": (1, 1),
        "主菜": (1, 1),
        "副菜": (0, 0),
        "汁物": (0, 0),
        "デザート": (0, 0),
    },
    "normal": {
        "主食": (1, 1),
        "主菜": (1, 1),
        "副菜": (1, 1),
        "汁物": (0, 1),
        "デザート": (0, 0),
    },
    "large": {
        "主食": (1, 1),
        "主菜": (1, 1),
        "副菜": (1, 2),
        "汁物": (1, 1),
        "デザート": (0, 1),
    },
}
