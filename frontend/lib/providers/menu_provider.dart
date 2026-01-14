import 'package:flutter/foundation.dart';
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
}
