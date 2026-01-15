import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../domain/entities/food.dart';
import '../../domain/entities/menu_plan.dart';
import '../../domain/entities/settings.dart';
import '../../domain/repositories/menu_repository.dart';
import '../datasources/api_service.dart';

part 'menu_repository_impl.g.dart';

/// 献立リポジトリの実装
class MenuRepositoryImpl implements MenuRepository {
  final ApiService _apiService;

  MenuRepositoryImpl(this._apiService);

  @override
  Future<MultiDayMenuPlan> generateMultiDayPlan({
    required int days,
    required int people,
    NutrientTarget? target,
    List<Allergen> excludedAllergens = const [],
    List<int> excludedDishIds = const [],
    List<int> preferredFoodIds = const [],
    String batchCookingLevel = 'normal',
    String varietyLevel = 'normal',
    Map<String, MealSetting>? mealSettings,
  }) {
    return _apiService.optimizeMultiDay(
      days: days,
      people: people,
      target: target,
      excludedAllergens: excludedAllergens,
      excludedDishIds: excludedDishIds,
      preferredFoodIds: preferredFoodIds,
      batchCookingLevel: batchCookingLevel,
      varietyLevel: varietyLevel,
      mealSettings: mealSettings,
    );
  }

  @override
  Future<MultiDayMenuPlan> refineMultiDayPlan({
    required int days,
    required int people,
    NutrientTarget? target,
    List<int> keepDishIds = const [],
    List<int> excludeDishIds = const [],
    List<Allergen> excludedAllergens = const [],
    List<int> preferredFoodIds = const [],
    String batchCookingLevel = 'normal',
    String varietyLevel = 'normal',
    Map<String, MealSetting>? mealSettings,
  }) {
    return _apiService.refineMultiDay(
      days: days,
      people: people,
      target: target,
      keepDishIds: keepDishIds,
      excludeDishIds: excludeDishIds,
      excludedAllergens: excludedAllergens,
      preferredFoodIds: preferredFoodIds,
      batchCookingLevel: batchCookingLevel,
      varietyLevel: varietyLevel,
      mealSettings: mealSettings,
    );
  }

  @override
  Future<MenuPlan> optimizeMenu({
    List<int> excludedFoodIds = const [],
  }) {
    return _apiService.optimizeMenu(excludedFoodIds: excludedFoodIds);
  }
}

/// ApiService Provider
@riverpod
ApiService apiService(ApiServiceRef ref) {
  return ApiService();
}

/// MenuRepository Provider
@riverpod
MenuRepository menuRepository(MenuRepositoryRef ref) {
  return MenuRepositoryImpl(ref.watch(apiServiceProvider));
}
