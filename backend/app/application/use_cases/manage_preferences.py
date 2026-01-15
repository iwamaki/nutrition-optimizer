"""
ユーザー設定管理ユースケース

クリーンアーキテクチャ: application層
"""
from dataclasses import dataclass

from app.domain.entities import UserPreferences, AllergenEnum
from app.domain.interfaces import PreferenceRepositoryInterface


@dataclass
class GetPreferencesUseCase:
    """ユーザー設定を取得するユースケース"""

    preference_repo: PreferenceRepositoryInterface

    def execute(self) -> UserPreferences:
        """ユーザー設定を取得

        Returns:
            現在のユーザー設定
        """
        return self.preference_repo.get()


@dataclass
class UpdatePreferencesUseCase:
    """ユーザー設定を更新するユースケース"""

    preference_repo: PreferenceRepositoryInterface

    def execute(
        self,
        excluded_allergens: list[AllergenEnum] | None = None,
        target_calories_min: float | None = None,
        target_calories_max: float | None = None,
        target_protein_min: float | None = None,
        target_protein_max: float | None = None,
        target_fat_min: float | None = None,
        target_fat_max: float | None = None,
        target_carbohydrate_min: float | None = None,
        target_carbohydrate_max: float | None = None,
        target_fiber_min: float | None = None,
        target_sodium_max: float | None = None,
        # ミネラル
        target_potassium_min: float | None = None,
        target_calcium_min: float | None = None,
        target_magnesium_min: float | None = None,
        target_iron_min: float | None = None,
        target_zinc_min: float | None = None,
        # ビタミン
        target_vitamin_a_min: float | None = None,
        target_vitamin_d_min: float | None = None,
        target_vitamin_e_min: float | None = None,
        target_vitamin_k_min: float | None = None,
        target_vitamin_b1_min: float | None = None,
        target_vitamin_b2_min: float | None = None,
        target_vitamin_b6_min: float | None = None,
        target_vitamin_b12_min: float | None = None,
        target_niacin_min: float | None = None,
        target_pantothenic_acid_min: float | None = None,
        target_biotin_min: float | None = None,
        target_folate_min: float | None = None,
        target_vitamin_c_min: float | None = None,
    ) -> UserPreferences:
        """ユーザー設定を更新

        指定されたパラメータのみを更新し、Noneのパラメータは現在の値を維持。

        Returns:
            更新後のユーザー設定
        """
        current = self.preference_repo.get()

        # 更新するフィールドのみマージ
        updated = UserPreferences(
            excluded_allergens=excluded_allergens if excluded_allergens is not None else current.excluded_allergens,
            target_calories_min=target_calories_min if target_calories_min is not None else current.target_calories_min,
            target_calories_max=target_calories_max if target_calories_max is not None else current.target_calories_max,
            target_protein_min=target_protein_min if target_protein_min is not None else current.target_protein_min,
            target_protein_max=target_protein_max if target_protein_max is not None else current.target_protein_max,
            target_fat_min=target_fat_min if target_fat_min is not None else current.target_fat_min,
            target_fat_max=target_fat_max if target_fat_max is not None else current.target_fat_max,
            target_carbohydrate_min=target_carbohydrate_min if target_carbohydrate_min is not None else current.target_carbohydrate_min,
            target_carbohydrate_max=target_carbohydrate_max if target_carbohydrate_max is not None else current.target_carbohydrate_max,
            target_fiber_min=target_fiber_min if target_fiber_min is not None else current.target_fiber_min,
            target_sodium_max=target_sodium_max if target_sodium_max is not None else current.target_sodium_max,
            # ミネラル
            target_potassium_min=target_potassium_min if target_potassium_min is not None else current.target_potassium_min,
            target_calcium_min=target_calcium_min if target_calcium_min is not None else current.target_calcium_min,
            target_magnesium_min=target_magnesium_min if target_magnesium_min is not None else current.target_magnesium_min,
            target_iron_min=target_iron_min if target_iron_min is not None else current.target_iron_min,
            target_zinc_min=target_zinc_min if target_zinc_min is not None else current.target_zinc_min,
            # ビタミン
            target_vitamin_a_min=target_vitamin_a_min if target_vitamin_a_min is not None else current.target_vitamin_a_min,
            target_vitamin_d_min=target_vitamin_d_min if target_vitamin_d_min is not None else current.target_vitamin_d_min,
            target_vitamin_e_min=target_vitamin_e_min if target_vitamin_e_min is not None else current.target_vitamin_e_min,
            target_vitamin_k_min=target_vitamin_k_min if target_vitamin_k_min is not None else current.target_vitamin_k_min,
            target_vitamin_b1_min=target_vitamin_b1_min if target_vitamin_b1_min is not None else current.target_vitamin_b1_min,
            target_vitamin_b2_min=target_vitamin_b2_min if target_vitamin_b2_min is not None else current.target_vitamin_b2_min,
            target_vitamin_b6_min=target_vitamin_b6_min if target_vitamin_b6_min is not None else current.target_vitamin_b6_min,
            target_vitamin_b12_min=target_vitamin_b12_min if target_vitamin_b12_min is not None else current.target_vitamin_b12_min,
            target_niacin_min=target_niacin_min if target_niacin_min is not None else current.target_niacin_min,
            target_pantothenic_acid_min=target_pantothenic_acid_min if target_pantothenic_acid_min is not None else current.target_pantothenic_acid_min,
            target_biotin_min=target_biotin_min if target_biotin_min is not None else current.target_biotin_min,
            target_folate_min=target_folate_min if target_folate_min is not None else current.target_folate_min,
            target_vitamin_c_min=target_vitamin_c_min if target_vitamin_c_min is not None else current.target_vitamin_c_min,
        )

        return self.preference_repo.save(updated)


@dataclass
class GetAllergensUseCase:
    """アレルゲン一覧を取得するユースケース"""

    def execute(self) -> list[dict]:
        """7大アレルゲン一覧を取得

        Returns:
            アレルゲン情報リスト
        """
        return [
            {"id": allergen.value, "name": allergen.value}
            for allergen in AllergenEnum
        ]
