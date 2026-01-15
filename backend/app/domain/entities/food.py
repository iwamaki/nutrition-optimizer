"""Food domain entities."""

from pydantic import BaseModel, Field


class Food(BaseModel):
    """食品データモデル（文科省食品成分表ベース）"""
    id: int
    name: str
    category: str
    # 基本栄養素
    calories: float = Field(ge=0, description="kcal/100g")
    protein: float = Field(ge=0, description="g/100g")
    fat: float = Field(ge=0, description="g/100g")
    carbohydrate: float = Field(ge=0, description="g/100g")
    fiber: float = Field(ge=0, description="g/100g")
    # ミネラル
    sodium: float = Field(ge=0, description="mg/100g")
    potassium: float = Field(default=0, ge=0, description="mg/100g (カリウム)")
    calcium: float = Field(ge=0, description="mg/100g")
    magnesium: float = Field(default=0, ge=0, description="mg/100g")
    iron: float = Field(ge=0, description="mg/100g")
    zinc: float = Field(default=0, ge=0, description="mg/100g (亜鉛)")
    # ビタミン
    vitamin_a: float = Field(ge=0, description="μg/100g (レチノール活性当量)")
    vitamin_d: float = Field(ge=0, description="μg/100g")
    vitamin_e: float = Field(default=0, ge=0, description="mg/100g (α-トコフェロール)")
    vitamin_k: float = Field(default=0, ge=0, description="μg/100g")
    vitamin_b1: float = Field(default=0, ge=0, description="mg/100g (チアミン)")
    vitamin_b2: float = Field(default=0, ge=0, description="mg/100g (リボフラビン)")
    vitamin_b6: float = Field(default=0, ge=0, description="mg/100g")
    vitamin_b12: float = Field(default=0, ge=0, description="μg/100g")
    niacin: float = Field(default=0, ge=0, description="mg/100g (ナイアシン/B3)")
    pantothenic_acid: float = Field(default=0, ge=0, description="mg/100g (パントテン酸/B5)")
    biotin: float = Field(default=0, ge=0, description="μg/100g (ビオチン/B7)")
    folate: float = Field(default=0, ge=0, description="μg/100g (葉酸)")
    vitamin_c: float = Field(ge=0, description="mg/100g")
    # 制約
    max_portion: float = Field(default=300, ge=0, description="1食あたり最大量(g)")


class FoodPortion(BaseModel):
    """食材と分量"""
    food: Food
    amount: float = Field(ge=0, description="g")


class NutrientTarget(BaseModel):
    """
    栄養素目標値（1日）

    デフォルト値は日本人の食事摂取基準(2020年版)厚生労働省に準拠
    成人男女(18-64歳)の平均値を使用
    """
    # エネルギー・三大栄養素
    calories_min: float = Field(default=1800, ge=0)
    calories_max: float = Field(default=2200, ge=0)
    protein_min: float = Field(default=58, ge=0, description="男65/女50の平均")
    protein_max: float = Field(default=100, ge=0)
    fat_min: float = Field(default=50, ge=0)
    fat_max: float = Field(default=80, ge=0)
    carbohydrate_min: float = Field(default=250, ge=0)
    carbohydrate_max: float = Field(default=350, ge=0)
    fiber_min: float = Field(default=20, ge=0, description="男21/女18の平均")
    # ミネラル
    sodium_max: float = Field(default=2500, ge=0, description="mg - 食塩7.5g未満相当")
    potassium_min: float = Field(default=2500, ge=0, description="mg (カリウム) - 目安量")
    calcium_min: float = Field(default=700, ge=0, description="mg - 男775/女650の平均")
    magnesium_min: float = Field(default=320, ge=0, description="mg - 男355/女280の平均")
    iron_min: float = Field(default=9.0, ge=0, description="mg - 男7.5/女10.5の平均")
    zinc_min: float = Field(default=10, ge=0, description="mg (亜鉛) - 男11/女8の平均")
    # ビタミン
    vitamin_a_min: float = Field(default=775, ge=0, description="μg (RAE) - 男875/女675の平均")
    vitamin_d_min: float = Field(default=8.5, ge=0, description="μg - 目安量")
    vitamin_e_min: float = Field(default=6.0, ge=0, description="mg (α-トコフェロール) - 目安量")
    vitamin_k_min: float = Field(default=150, ge=0, description="μg - 目安量")
    vitamin_b1_min: float = Field(default=1.2, ge=0, description="mg - 男1.35/女1.1の平均")
    vitamin_b2_min: float = Field(default=1.4, ge=0, description="mg - 男1.55/女1.2の平均")
    vitamin_b6_min: float = Field(default=1.3, ge=0, description="mg - 男1.4/女1.1の平均")
    vitamin_b12_min: float = Field(default=2.4, ge=0, description="μg - 推奨量")
    niacin_min: float = Field(default=13.5, ge=0, description="mg NE (ナイアシン) - 男15/女12の平均")
    pantothenic_acid_min: float = Field(default=5.5, ge=0, description="mg (パントテン酸) - 男6/女5の平均")
    biotin_min: float = Field(default=50, ge=0, description="μg (ビオチン) - 目安量")
    folate_min: float = Field(default=240, ge=0, description="μg (葉酸) - 推奨量")
    vitamin_c_min: float = Field(default=100, ge=0, description="mg - 推奨量")

    def get_target_for_nutrient(self, nutrient: str) -> float:
        """栄養素の目標値を取得（達成率計算用）"""
        # min値がある栄養素
        min_nutrients = [
            "protein", "fiber", "potassium", "calcium", "magnesium", "iron", "zinc",
            "vitamin_a", "vitamin_d", "vitamin_e", "vitamin_k",
            "vitamin_b1", "vitamin_b2", "vitamin_b6", "vitamin_b12",
            "niacin", "pantothenic_acid", "biotin", "folate", "vitamin_c"
        ]

        if nutrient == "calories":
            return (self.calories_min + self.calories_max) / 2
        elif nutrient == "fat":
            return (self.fat_min + self.fat_max) / 2
        elif nutrient == "carbohydrate":
            return (self.carbohydrate_min + self.carbohydrate_max) / 2
        elif nutrient == "sodium":
            return self.sodium_max
        elif nutrient in min_nutrients:
            return getattr(self, f"{nutrient}_min", 0)
        else:
            return 0
