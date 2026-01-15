"""Domain constants for nutrition optimization."""

# 全栄養素リスト
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
