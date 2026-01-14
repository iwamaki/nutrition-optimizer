import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../domain/entities/dish.dart';
import '../../domain/entities/menu_plan.dart';
import '../../domain/entities/settings.dart';
import '../../data/repositories/menu_repository_impl.dart';

part 'menu_provider.g.dart';

/// 献立生成の状態
class MenuState {
  final MultiDayMenuPlan? currentPlan;
  final bool isLoading;
  final String? error;
  final int days;
  final int people;
  final Set<Allergen> excludedAllergens;
  final Set<int> excludedDishIds;
  final Set<int> keepDishIds;
  final String batchCookingLevel;
  final String volumeLevel;
  final String varietyLevel;

  const MenuState({
    this.currentPlan,
    this.isLoading = false,
    this.error,
    this.days = 3,
    this.people = 2,
    this.excludedAllergens = const {},
    this.excludedDishIds = const {},
    this.keepDishIds = const {},
    this.batchCookingLevel = 'normal',
    this.volumeLevel = 'normal',
    this.varietyLevel = 'normal',
  });

  MenuState copyWith({
    MultiDayMenuPlan? currentPlan,
    bool? isLoading,
    String? error,
    int? days,
    int? people,
    Set<Allergen>? excludedAllergens,
    Set<int>? excludedDishIds,
    Set<int>? keepDishIds,
    String? batchCookingLevel,
    String? volumeLevel,
    String? varietyLevel,
    bool clearPlan = false,
    bool clearError = false,
  }) {
    return MenuState(
      currentPlan: clearPlan ? null : (currentPlan ?? this.currentPlan),
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      days: days ?? this.days,
      people: people ?? this.people,
      excludedAllergens: excludedAllergens ?? this.excludedAllergens,
      excludedDishIds: excludedDishIds ?? this.excludedDishIds,
      keepDishIds: keepDishIds ?? this.keepDishIds,
      batchCookingLevel: batchCookingLevel ?? this.batchCookingLevel,
      volumeLevel: volumeLevel ?? this.volumeLevel,
      varietyLevel: varietyLevel ?? this.varietyLevel,
    );
  }

  bool get hasPlan => currentPlan != null;
  double get averageAchievement => currentPlan?.averageAchievement ?? 0;
  DailyMealAssignment? get todayPlan => getDayPlan(1);

  DailyMealAssignment? getDayPlan(int day) {
    if (currentPlan == null) return null;
    return currentPlan!.dailyPlans.firstWhere(
      (p) => p.day == day,
      orElse: () => currentPlan!.dailyPlans.first,
    );
  }
}

/// 献立管理Notifier
@riverpod
class MenuNotifier extends _$MenuNotifier {
  @override
  MenuState build() => const MenuState();

  void setDays(int days) {
    state = state.copyWith(days: days.clamp(1, 7));
  }

  void setPeople(int people) {
    state = state.copyWith(people: people.clamp(1, 6));
  }

  void setExcludedAllergens(Set<Allergen> allergens) {
    state = state.copyWith(excludedAllergens: allergens);
  }

  void toggleAllergen(Allergen allergen) {
    final current = Set<Allergen>.from(state.excludedAllergens);
    if (current.contains(allergen)) {
      current.remove(allergen);
    } else {
      current.add(allergen);
    }
    state = state.copyWith(excludedAllergens: current);
  }

  void setBatchCookingLevel(String value) {
    state = state.copyWith(batchCookingLevel: value);
  }

  void setVolumeLevel(String value) {
    state = state.copyWith(volumeLevel: value);
  }

  void setVarietyLevel(String value) {
    state = state.copyWith(varietyLevel: value);
  }

  void excludeDish(int dishId) {
    final excluded = Set<int>.from(state.excludedDishIds)..add(dishId);
    final keep = Set<int>.from(state.keepDishIds)..remove(dishId);
    state = state.copyWith(excludedDishIds: excluded, keepDishIds: keep);
  }

  void keepDish(int dishId) {
    final keep = Set<int>.from(state.keepDishIds)..add(dishId);
    final excluded = Set<int>.from(state.excludedDishIds)..remove(dishId);
    state = state.copyWith(keepDishIds: keep, excludedDishIds: excluded);
  }

  void resetDishSelections() {
    state = state.copyWith(
      excludedDishIds: {},
      keepDishIds: {},
    );
  }

  Future<void> generatePlan({NutrientTarget? target}) async {
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final repo = ref.read(menuRepositoryProvider);
      final plan = await repo.generateMultiDayPlan(
        days: state.days,
        people: state.people,
        target: target,
        excludedAllergens: state.excludedAllergens.toList(),
        excludedDishIds: state.excludedDishIds.toList(),
        batchCookingLevel: state.batchCookingLevel,
        volumeLevel: state.volumeLevel,
        varietyLevel: state.varietyLevel,
      );
      state = state.copyWith(
        currentPlan: plan,
        isLoading: false,
        excludedDishIds: {},
        keepDishIds: {},
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  Future<void> refinePlan({NutrientTarget? target}) async {
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final repo = ref.read(menuRepositoryProvider);
      final plan = await repo.refineMultiDayPlan(
        days: state.days,
        people: state.people,
        target: target,
        keepDishIds: state.keepDishIds.toList(),
        excludeDishIds: state.excludedDishIds.toList(),
        excludedAllergens: state.excludedAllergens.toList(),
        batchCookingLevel: state.batchCookingLevel,
        volumeLevel: state.volumeLevel,
        varietyLevel: state.varietyLevel,
      );
      state = state.copyWith(
        currentPlan: plan,
        isLoading: false,
        excludedDishIds: {},
        keepDishIds: {},
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  void clearPlan() {
    state = state.copyWith(
      clearPlan: true,
      excludedDishIds: {},
      keepDishIds: {},
      clearError: true,
    );
  }

  void clearError() {
    state = state.copyWith(clearError: true);
  }

  /// 外部で生成された献立を設定
  void setPlan(MultiDayMenuPlan plan) {
    state = state.copyWith(
      currentPlan: plan,
      days: plan.days,
      people: plan.people,
      excludedDishIds: {},
      keepDishIds: {},
      clearError: true,
    );
  }

  /// 料理を別の日/食事に移動（ドラッグ&ドロップ用）
  void moveDish({
    required int fromDay,
    required MealType fromMeal,
    required int fromIndex,
    required int toDay,
    required MealType toMeal,
    required int toIndex,
  }) {
    if (state.currentPlan == null) return;
    if (fromDay == toDay && fromMeal == toMeal && fromIndex == toIndex) return;

    final dailyPlans = List<DailyMealAssignment>.from(state.currentPlan!.dailyPlans);

    final fromDayIndex = dailyPlans.indexWhere((p) => p.day == fromDay);
    final toDayIndex = dailyPlans.indexWhere((p) => p.day == toDay);
    if (fromDayIndex == -1 || toDayIndex == -1) return;

    final fromDayPlan = dailyPlans[fromDayIndex];
    final fromMealList = List<DishPortion>.from(fromDayPlan.getMealDishes(fromMeal));
    if (fromIndex >= fromMealList.length) return;

    final dish = fromMealList.removeAt(fromIndex);

    if (fromDay == toDay) {
      if (fromMeal == toMeal) {
        final adjustedIndex = fromIndex < toIndex ? toIndex - 1 : toIndex;
        fromMealList.insert(adjustedIndex.clamp(0, fromMealList.length), dish);
        dailyPlans[fromDayIndex] = _updateMealList(fromDayPlan, fromMeal, fromMealList);
      } else {
        final toMealList = List<DishPortion>.from(fromDayPlan.getMealDishes(toMeal));
        toMealList.insert(toIndex.clamp(0, toMealList.length), dish);
        var updatedPlan = _updateMealList(fromDayPlan, fromMeal, fromMealList);
        updatedPlan = _updateMealList(updatedPlan, toMeal, toMealList);
        dailyPlans[fromDayIndex] = updatedPlan;
      }
    } else {
      dailyPlans[fromDayIndex] = _updateMealList(fromDayPlan, fromMeal, fromMealList);

      final toDayPlan = dailyPlans[toDayIndex];
      final toMealList = List<DishPortion>.from(toDayPlan.getMealDishes(toMeal));
      toMealList.insert(toIndex.clamp(0, toMealList.length), dish);
      dailyPlans[toDayIndex] = _updateMealList(toDayPlan, toMeal, toMealList);
    }

    final newPlan = MultiDayMenuPlan(
      planId: state.currentPlan!.planId,
      days: state.currentPlan!.days,
      people: state.currentPlan!.people,
      dailyPlans: dailyPlans,
      cookingTasks: state.currentPlan!.cookingTasks,
      shoppingList: state.currentPlan!.shoppingList,
      overallNutrients: state.currentPlan!.overallNutrients,
      overallAchievement: state.currentPlan!.overallAchievement,
      warnings: state.currentPlan!.warnings,
    );

    state = state.copyWith(currentPlan: newPlan);
  }

  DailyMealAssignment _updateMealList(
    DailyMealAssignment plan,
    MealType mealType,
    List<DishPortion> newList,
  ) {
    switch (mealType) {
      case MealType.breakfast:
        return plan.copyWith(breakfast: newList);
      case MealType.lunch:
        return plan.copyWith(lunch: newList);
      case MealType.dinner:
        return plan.copyWith(dinner: newList);
    }
  }

  void swapDishes({
    required int day1,
    required MealType meal1,
    required int index1,
    required int day2,
    required MealType meal2,
    required int index2,
  }) {
    if (state.currentPlan == null) return;

    final dailyPlans = List<DailyMealAssignment>.from(state.currentPlan!.dailyPlans);

    final dayIndex1 = dailyPlans.indexWhere((p) => p.day == day1);
    final dayIndex2 = dailyPlans.indexWhere((p) => p.day == day2);
    if (dayIndex1 == -1 || dayIndex2 == -1) return;

    final dayPlan1 = dailyPlans[dayIndex1];
    final dayPlan2 = dailyPlans[dayIndex2];
    final mealList1 = List<DishPortion>.from(dayPlan1.getMealDishes(meal1));
    final mealList2 = List<DishPortion>.from(dayPlan2.getMealDishes(meal2));

    if (index1 >= mealList1.length || index2 >= mealList2.length) return;

    final temp = mealList1[index1];
    mealList1[index1] = mealList2[index2];
    mealList2[index2] = temp;

    dailyPlans[dayIndex1] = _updateMealList(dayPlan1, meal1, mealList1);
    if (dayIndex1 != dayIndex2) {
      dailyPlans[dayIndex2] = _updateMealList(dayPlan2, meal2, mealList2);
    } else if (meal1 != meal2) {
      dailyPlans[dayIndex1] = _updateMealList(dailyPlans[dayIndex1], meal2, mealList2);
    }

    final newPlan = MultiDayMenuPlan(
      planId: state.currentPlan!.planId,
      days: state.currentPlan!.days,
      people: state.currentPlan!.people,
      dailyPlans: dailyPlans,
      cookingTasks: state.currentPlan!.cookingTasks,
      shoppingList: state.currentPlan!.shoppingList,
      overallNutrients: state.currentPlan!.overallNutrients,
      overallAchievement: state.currentPlan!.overallAchievement,
      warnings: state.currentPlan!.warnings,
    );

    state = state.copyWith(currentPlan: newPlan);
  }
}
