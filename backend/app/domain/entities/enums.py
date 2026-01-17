"""Domain enumerations."""

from enum import Enum


class AllergenEnum(str, Enum):
    """アレルゲン28品目（特定原材料8品目 + 準特定原材料20品目）"""
    # 特定原材料8品目（表示義務）
    EGG = "卵"
    MILK = "乳"
    WHEAT = "小麦"
    BUCKWHEAT = "そば"
    PEANUT = "落花生"
    SHRIMP = "えび"
    CRAB = "かに"
    WALNUT = "くるみ"
    # 準特定原材料20品目（表示推奨）
    ALMOND = "アーモンド"
    ABALONE = "あわび"
    SQUID = "いか"
    SALMON_ROE = "いくら"
    ORANGE = "オレンジ"
    BEEF = "牛肉"
    CASHEW = "カシューナッツ"
    KIWI = "キウイフルーツ"
    SESAME = "ごま"
    SALMON = "さけ"
    MACKEREL = "さば"
    SOYBEAN = "大豆"
    CHICKEN = "鶏肉"
    PORK = "豚肉"
    BANANA = "バナナ"
    PEACH = "もも"
    YAM = "やまいも"
    APPLE = "りんご"
    GELATIN = "ゼラチン"
    MACADAMIA = "マカダミアナッツ"


class VolumeLevelEnum(str, Enum):
    """献立ボリュームレベル"""
    SMALL = "small"    # 少なめ（カロリー目標 × 0.8）
    NORMAL = "normal"  # 普通（カロリー目標 × 1.0）
    LARGE = "large"    # 多め（カロリー目標 × 1.2）


class VarietyLevelEnum(str, Enum):
    """食材の種類レベル（多様性）"""
    SMALL = "small"    # 少なめ（作り置き優先、同じ料理を繰り返す）
    NORMAL = "normal"  # 普通（バランス）
    LARGE = "large"    # 多め（毎食違う料理）


class BatchCookingLevelEnum(str, Enum):
    """作り置き優先度レベル"""
    SMALL = "small"    # 少なめ（調理回数多めでもOK、毎食違う料理）
    NORMAL = "normal"  # 普通（バランス）
    LARGE = "large"    # 多め（調理回数を最小化、作り置き重視）


class MealTypeEnum(str, Enum):
    """食事タイプ"""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class DishCategoryEnum(str, Enum):
    """料理カテゴリ"""
    STAPLE = "主食"
    MAIN = "主菜"
    STAPLE_MAIN = "主食・主菜"  # 丼物、カレー、ラーメンなど（主食と主菜を兼ねる）
    SIDE = "副菜"
    SOUP = "汁物"
    DESSERT = "デザート"


class CookingMethodEnum(str, Enum):
    """調理法"""
    RAW = "生"
    BOIL = "茹でる"
    STEAM = "蒸す"
    GRILL = "焼く"
    FRY = "炒める"
    DEEP_FRY = "揚げる"
    SIMMER = "煮る"
    MICROWAVE = "電子レンジ"


class MealPresetEnum(str, Enum):
    """食事プリセット"""
    MINIMAL = "minimal"      # 最小限（主食のみ）
    LIGHT = "light"          # 軽め（主食+主菜）
    STANDARD = "standard"    # 標準（主食+主菜+副菜）
    FULL = "full"            # 充実（主食+主菜+副菜+汁物）
    JAPANESE = "japanese"    # 和定食（一汁三菜）
    CUSTOM = "custom"        # カスタム（categoriesを直接指定）
