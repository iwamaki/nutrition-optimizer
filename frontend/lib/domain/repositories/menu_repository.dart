import '../entities/food.dart';
import '../entities/menu_plan.dart';
import '../entities/settings.dart';

/// 献立リポジトリのインターフェース
abstract class MenuRepository {
  /// 複数日の献立を生成
  Future<MultiDayMenuPlan> generateMultiDayPlan({
    required int days,
    required int people,
    NutrientTarget? target,
    List<Allergen> excludedAllergens = const [],
    List<int> excludedDishIds = const [],
    String batchCookingLevel = 'normal',
    String varietyLevel = 'normal',
    Map<String, MealSetting>? mealSettings,
  });

  /// 献立を調整して再生成
  Future<MultiDayMenuPlan> refineMultiDayPlan({
    required int days,
    required int people,
    NutrientTarget? target,
    List<int> keepDishIds = const [],
    List<int> excludeDishIds = const [],
    List<Allergen> excludedAllergens = const [],
    String batchCookingLevel = 'normal',
    String varietyLevel = 'normal',
    Map<String, MealSetting>? mealSettings,
  });

  /// 1日分の献立を最適化（シンプル版）
  Future<MenuPlan> optimizeMenu({
    List<int> excludedFoodIds = const [],
  });
}
