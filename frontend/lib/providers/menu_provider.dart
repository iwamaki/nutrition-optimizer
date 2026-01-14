import 'package:flutter/foundation.dart';
import '../models/dish.dart';
import '../models/menu_plan.dart';
import '../models/settings.dart';
import '../services/api_service.dart';

/// 献立状態管理Provider
class MenuProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();

  MultiDayMenuPlan? _currentPlan;
  bool _isLoading = false;
  String? _error;

  // 生成パラメータ
  int _days = 3;
  int _people = 2;
  Set<Allergen> _excludedAllergens = {};
  Set<int> _excludedDishIds = {};
  Set<int> _keepDishIds = {};
  bool _preferBatchCooking = false;

  // Getters
  MultiDayMenuPlan? get currentPlan => _currentPlan;
  bool get isLoading => _isLoading;
  String? get error => _error;
  int get days => _days;
  int get people => _people;
  Set<Allergen> get excludedAllergens => _excludedAllergens;
  Set<int> get excludedDishIds => _excludedDishIds;
  Set<int> get keepDishIds => _keepDishIds;
  bool get preferBatchCooking => _preferBatchCooking;

  bool get hasPlan => _currentPlan != null;

  // パラメータ設定
  void setDays(int days) {
    _days = days.clamp(1, 7);
    notifyListeners();
  }

  void setPeople(int people) {
    _people = people.clamp(1, 6);
    notifyListeners();
  }

  void setExcludedAllergens(Set<Allergen> allergens) {
    _excludedAllergens = allergens;
    notifyListeners();
  }

  void toggleAllergen(Allergen allergen) {
    if (_excludedAllergens.contains(allergen)) {
      _excludedAllergens = Set.from(_excludedAllergens)..remove(allergen);
    } else {
      _excludedAllergens = Set.from(_excludedAllergens)..add(allergen);
    }
    notifyListeners();
  }

  void setPreferBatchCooking(bool value) {
    _preferBatchCooking = value;
    notifyListeners();
  }

  void excludeDish(int dishId) {
    _excludedDishIds = Set.from(_excludedDishIds)..add(dishId);
    _keepDishIds = Set.from(_keepDishIds)..remove(dishId);
    notifyListeners();
  }

  void keepDish(int dishId) {
    _keepDishIds = Set.from(_keepDishIds)..add(dishId);
    _excludedDishIds = Set.from(_excludedDishIds)..remove(dishId);
    notifyListeners();
  }

  void resetDishSelections() {
    _excludedDishIds = {};
    _keepDishIds = {};
    notifyListeners();
  }

  /// 献立を生成
  Future<void> generatePlan({NutrientTarget? target}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _currentPlan = await _apiService.optimizeMultiDay(
        days: _days,
        people: _people,
        target: target,
        excludedAllergens: _excludedAllergens.toList(),
        excludedDishIds: _excludedDishIds.toList(),
        preferBatchCooking: _preferBatchCooking,
      );
      _excludedDishIds = {};
      _keepDishIds = {};
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// 献立を調整して再生成
  Future<void> refinePlan({NutrientTarget? target}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _currentPlan = await _apiService.refineMultiDay(
        days: _days,
        people: _people,
        target: target,
        keepDishIds: _keepDishIds.toList(),
        excludeDishIds: _excludedDishIds.toList(),
        excludedAllergens: _excludedAllergens.toList(),
        preferBatchCooking: _preferBatchCooking,
      );
      _excludedDishIds = {};
      _keepDishIds = {};
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// 献立をクリア
  void clearPlan() {
    _currentPlan = null;
    _excludedDishIds = {};
    _keepDishIds = {};
    _error = null;
    notifyListeners();
  }

  /// エラーをクリア
  void clearError() {
    _error = null;
    notifyListeners();
  }

  /// 特定の日の献立を取得
  DailyMealAssignment? getDayPlan(int day) {
    if (_currentPlan == null) return null;
    return _currentPlan!.dailyPlans.firstWhere(
      (p) => p.day == day,
      orElse: () => _currentPlan!.dailyPlans.first,
    );
  }

  /// 今日の献立を取得（day=1）
  DailyMealAssignment? get todayPlan => getDayPlan(1);

  /// 全日程の平均栄養達成率
  double get averageAchievement => _currentPlan?.averageAchievement ?? 0;

  /// 料理を別の日/食事に移動（ドラッグ&ドロップ用）
  void moveDish({
    required int fromDay,
    required MealType fromMeal,
    required int fromIndex,
    required int toDay,
    required MealType toMeal,
    required int toIndex,
  }) {
    if (_currentPlan == null) return;

    // 同じ場所への移動は無視
    if (fromDay == toDay && fromMeal == toMeal && fromIndex == toIndex) return;

    final dailyPlans = List<DailyMealAssignment>.from(_currentPlan!.dailyPlans);

    // ソースの日を取得
    final fromDayIndex = dailyPlans.indexWhere((p) => p.day == fromDay);
    final toDayIndex = dailyPlans.indexWhere((p) => p.day == toDay);
    if (fromDayIndex == -1 || toDayIndex == -1) return;

    // ソースの料理を取得
    final fromDayPlan = dailyPlans[fromDayIndex];
    final fromMealList = List<DishPortion>.from(fromDayPlan.getMealDishes(fromMeal));
    if (fromIndex >= fromMealList.length) return;

    final dish = fromMealList.removeAt(fromIndex);

    // 同じ日の場合
    if (fromDay == toDay) {
      if (fromMeal == toMeal) {
        // 同じ食事内での並べ替え
        final adjustedIndex = fromIndex < toIndex ? toIndex - 1 : toIndex;
        fromMealList.insert(adjustedIndex.clamp(0, fromMealList.length), dish);
        dailyPlans[fromDayIndex] = _updateMealList(fromDayPlan, fromMeal, fromMealList);
      } else {
        // 異なる食事への移動
        final toMealList = List<DishPortion>.from(fromDayPlan.getMealDishes(toMeal));
        toMealList.insert(toIndex.clamp(0, toMealList.length), dish);
        var updatedPlan = _updateMealList(fromDayPlan, fromMeal, fromMealList);
        updatedPlan = _updateMealList(updatedPlan, toMeal, toMealList);
        dailyPlans[fromDayIndex] = updatedPlan;
      }
    } else {
      // 異なる日への移動
      dailyPlans[fromDayIndex] = _updateMealList(fromDayPlan, fromMeal, fromMealList);

      final toDayPlan = dailyPlans[toDayIndex];
      final toMealList = List<DishPortion>.from(toDayPlan.getMealDishes(toMeal));
      toMealList.insert(toIndex.clamp(0, toMealList.length), dish);
      dailyPlans[toDayIndex] = _updateMealList(toDayPlan, toMeal, toMealList);
    }

    // プランを更新
    _currentPlan = MultiDayMenuPlan(
      planId: _currentPlan!.planId,
      days: _currentPlan!.days,
      people: _currentPlan!.people,
      dailyPlans: dailyPlans,
      cookingTasks: _currentPlan!.cookingTasks,
      shoppingList: _currentPlan!.shoppingList,
      overallNutrients: _currentPlan!.overallNutrients,
      overallAchievement: _currentPlan!.overallAchievement,
      warnings: _currentPlan!.warnings,
    );

    notifyListeners();
  }

  /// 食事リストを更新したDailyMealAssignmentを返す
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

  /// 2つの料理を入れ替え
  void swapDishes({
    required int day1,
    required MealType meal1,
    required int index1,
    required int day2,
    required MealType meal2,
    required int index2,
  }) {
    if (_currentPlan == null) return;

    final dailyPlans = List<DailyMealAssignment>.from(_currentPlan!.dailyPlans);

    final dayIndex1 = dailyPlans.indexWhere((p) => p.day == day1);
    final dayIndex2 = dailyPlans.indexWhere((p) => p.day == day2);
    if (dayIndex1 == -1 || dayIndex2 == -1) return;

    final dayPlan1 = dailyPlans[dayIndex1];
    final dayPlan2 = dailyPlans[dayIndex2];
    final mealList1 = List<DishPortion>.from(dayPlan1.getMealDishes(meal1));
    final mealList2 = List<DishPortion>.from(dayPlan2.getMealDishes(meal2));

    if (index1 >= mealList1.length || index2 >= mealList2.length) return;

    // 入れ替え
    final temp = mealList1[index1];
    mealList1[index1] = mealList2[index2];
    mealList2[index2] = temp;

    dailyPlans[dayIndex1] = _updateMealList(dayPlan1, meal1, mealList1);
    if (dayIndex1 != dayIndex2) {
      dailyPlans[dayIndex2] = _updateMealList(dayPlan2, meal2, mealList2);
    } else if (meal1 != meal2) {
      dailyPlans[dayIndex1] = _updateMealList(dailyPlans[dayIndex1], meal2, mealList2);
    }

    _currentPlan = MultiDayMenuPlan(
      planId: _currentPlan!.planId,
      days: _currentPlan!.days,
      people: _currentPlan!.people,
      dailyPlans: dailyPlans,
      cookingTasks: _currentPlan!.cookingTasks,
      shoppingList: _currentPlan!.shoppingList,
      overallNutrients: _currentPlan!.overallNutrients,
      overallAchievement: _currentPlan!.overallAchievement,
      warnings: _currentPlan!.warnings,
    );

    notifyListeners();
  }
}
