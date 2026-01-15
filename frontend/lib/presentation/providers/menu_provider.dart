import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../domain/entities/dish.dart';
import '../../domain/entities/menu_plan.dart';
import '../../domain/entities/settings.dart';
import '../../data/repositories/menu_repository_impl.dart';
import 'settings_provider.dart';

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
      final settingsState = ref.read(settingsNotifierProvider);
      final plan = await repo.generateMultiDayPlan(
        days: state.days,
        people: state.people,
        target: target,
        excludedAllergens: state.excludedAllergens.toList(),
        excludedDishIds: state.excludedDishIds.toList(),
        preferredDishIds: settingsState.favoriteDishIds.toList(),
        batchCookingLevel: state.batchCookingLevel,
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
      final settingsState = ref.read(settingsNotifierProvider);
      final plan = await repo.refineMultiDayPlan(
        days: state.days,
        people: state.people,
        target: target,
        keepDishIds: state.keepDishIds.toList(),
        excludeDishIds: state.excludedDishIds.toList(),
        excludedAllergens: state.excludedAllergens.toList(),
        preferredDishIds: settingsState.favoriteDishIds.toList(),
        batchCookingLevel: state.batchCookingLevel,
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

    // 移動した日の栄養素を再計算
    final recalculatedPlans = dailyPlans.map((dayPlan) {
      if (fromDay == toDay) {
        // 同じ日の中での移動: その日のみ再計算
        if (dayPlan.day == fromDay) {
          return _recalculateDayNutrients(dayPlan);
        }
      } else {
        // 異なる日への移動: 両日を再計算
        if (dayPlan.day == fromDay || dayPlan.day == toDay) {
          return _recalculateDayNutrients(dayPlan);
        }
      }
      return dayPlan;
    }).toList();

    // 全体の栄養素を再計算
    final overallNutrients = _calculateOverallNutrients(recalculatedPlans);
    final overallAchievement = _calculateOverallAchievement(
      overallNutrients,
      state.currentPlan!.days,
    );

    final newPlan = MultiDayMenuPlan(
      planId: state.currentPlan!.planId,
      days: state.currentPlan!.days,
      people: state.currentPlan!.people,
      dailyPlans: recalculatedPlans,
      cookingTasks: state.currentPlan!.cookingTasks,
      shoppingList: state.currentPlan!.shoppingList,
      overallNutrients: overallNutrients,
      overallAchievement: overallAchievement,
      warnings: state.currentPlan!.warnings,
    );

    state = state.copyWith(currentPlan: newPlan);
  }

  /// 1日分の栄養素を再計算
  DailyMealAssignment _recalculateDayNutrients(DailyMealAssignment dayPlan) {
    final allDishes = [
      ...dayPlan.breakfast,
      ...dayPlan.lunch,
      ...dayPlan.dinner,
    ];

    // 人数を取得（バックエンドと同じく1人あたりに換算するため）
    final people = state.currentPlan?.people ?? 1;

    final totalNutrients = <String, double>{
      // 基本栄養素
      'calories': 0,
      'protein': 0,
      'fat': 0,
      'carbohydrate': 0,
      'fiber': 0,
      // ミネラル
      'sodium': 0,
      'potassium': 0,
      'calcium': 0,
      'magnesium': 0,
      'iron': 0,
      'zinc': 0,
      // ビタミン
      'vitamin_a': 0,
      'vitamin_d': 0,
      'vitamin_e': 0,
      'vitamin_k': 0,
      'vitamin_b1': 0,
      'vitamin_b2': 0,
      'vitamin_b6': 0,
      'vitamin_b12': 0,
      'niacin': 0,
      'pantothenic_acid': 0,
      'biotin': 0,
      'folate': 0,
      'vitamin_c': 0,
    };

    for (final portion in allDishes) {
      final dish = portion.dish;
      final servings = portion.servings;
      // 基本栄養素
      totalNutrients['calories'] = totalNutrients['calories']! + dish.calories * servings;
      totalNutrients['protein'] = totalNutrients['protein']! + dish.protein * servings;
      totalNutrients['fat'] = totalNutrients['fat']! + dish.fat * servings;
      totalNutrients['carbohydrate'] = totalNutrients['carbohydrate']! + dish.carbohydrate * servings;
      totalNutrients['fiber'] = totalNutrients['fiber']! + dish.fiber * servings;
      // ミネラル
      totalNutrients['sodium'] = totalNutrients['sodium']! + dish.sodium * servings;
      totalNutrients['potassium'] = totalNutrients['potassium']! + dish.potassium * servings;
      totalNutrients['calcium'] = totalNutrients['calcium']! + dish.calcium * servings;
      totalNutrients['magnesium'] = totalNutrients['magnesium']! + dish.magnesium * servings;
      totalNutrients['iron'] = totalNutrients['iron']! + dish.iron * servings;
      totalNutrients['zinc'] = totalNutrients['zinc']! + dish.zinc * servings;
      // ビタミン
      totalNutrients['vitamin_a'] = totalNutrients['vitamin_a']! + dish.vitaminA * servings;
      totalNutrients['vitamin_d'] = totalNutrients['vitamin_d']! + dish.vitaminD * servings;
      totalNutrients['vitamin_e'] = totalNutrients['vitamin_e']! + dish.vitaminE * servings;
      totalNutrients['vitamin_k'] = totalNutrients['vitamin_k']! + dish.vitaminK * servings;
      totalNutrients['vitamin_b1'] = totalNutrients['vitamin_b1']! + dish.vitaminB1 * servings;
      totalNutrients['vitamin_b2'] = totalNutrients['vitamin_b2']! + dish.vitaminB2 * servings;
      totalNutrients['vitamin_b6'] = totalNutrients['vitamin_b6']! + dish.vitaminB6 * servings;
      totalNutrients['vitamin_b12'] = totalNutrients['vitamin_b12']! + dish.vitaminB12 * servings;
      totalNutrients['niacin'] = totalNutrients['niacin']! + dish.niacin * servings;
      totalNutrients['pantothenic_acid'] = totalNutrients['pantothenic_acid']! + dish.pantothenicAcid * servings;
      totalNutrients['biotin'] = totalNutrients['biotin']! + dish.biotin * servings;
      totalNutrients['folate'] = totalNutrients['folate']! + dish.folate * servings;
      totalNutrients['vitamin_c'] = totalNutrients['vitamin_c']! + dish.vitaminC * servings;
    }

    // 1人あたりに換算（バックエンドと同じ処理）
    final nutrientsPerPerson = <String, double>{};
    for (final entry in totalNutrients.entries) {
      nutrientsPerPerson[entry.key] = entry.value / people;
    }

    // 達成率を再計算（バックエンドと同じロジック）
    final achievementRate = _calcAchievement(nutrientsPerPerson);

    return dayPlan.copyWith(
      totalNutrients: nutrientsPerPerson,
      achievementRate: achievementRate,
    );
  }

  /// 達成率を計算（バックエンド _calc_achievement と完全一致）
  Map<String, double> _calcAchievement(Map<String, double> nutrients) {
    // デフォルトの目標値を使用
    const target = NutrientTarget();
    final achievement = <String, double>{};

    // バックエンドと同じロジック:
    // - min/maxがある栄養素: (min + max) / 2 を目標に
    // - minのみの栄養素: (min + min * 1.5) / 2 = min * 1.25 を目標に
    // - sodium: 目標上限 / 実績 * 100（100でclamp）

    // 基本栄養素（min/maxの平均を目標に）
    final caloriesTarget = (target.caloriesMin + target.caloriesMax) / 2;
    achievement['calories'] = caloriesTarget > 0
        ? (nutrients['calories'] ?? 0) / caloriesTarget * 100 : 100;

    final proteinTarget = (target.proteinMin + target.proteinMax) / 2;
    achievement['protein'] = proteinTarget > 0
        ? (nutrients['protein'] ?? 0) / proteinTarget * 100 : 100;

    final fatTarget = (target.fatMin + target.fatMax) / 2;
    achievement['fat'] = fatTarget > 0
        ? (nutrients['fat'] ?? 0) / fatTarget * 100 : 100;

    final carbTarget = (target.carbohydrateMin + target.carbohydrateMax) / 2;
    achievement['carbohydrate'] = carbTarget > 0
        ? (nutrients['carbohydrate'] ?? 0) / carbTarget * 100 : 100;

    // fiber: minのみなので (min + min*1.5) / 2 = min * 1.25
    final fiberTarget = target.fiberMin * 1.25;
    achievement['fiber'] = fiberTarget > 0
        ? (nutrients['fiber'] ?? 0) / fiberTarget * 100 : 100;

    // ミネラル
    // sodium: 少ないほど良い（バックエンドと同じ: min(100, target / max(val, 1) * 100)）
    final sodiumVal = nutrients['sodium'] ?? 0;
    if (sodiumVal > 0) {
      final sodiumAchievement = target.sodiumMax / sodiumVal * 100;
      achievement['sodium'] = sodiumAchievement < 100 ? sodiumAchievement : 100;
    } else {
      achievement['sodium'] = 100;
    }

    // その他のミネラル: minのみなので min * 1.25 を目標に
    final potassiumTarget = target.potassiumMin * 1.25;
    achievement['potassium'] = potassiumTarget > 0
        ? (nutrients['potassium'] ?? 0) / potassiumTarget * 100 : 100;

    final calciumTarget = target.calciumMin * 1.25;
    achievement['calcium'] = calciumTarget > 0
        ? (nutrients['calcium'] ?? 0) / calciumTarget * 100 : 100;

    final magnesiumTarget = target.magnesiumMin * 1.25;
    achievement['magnesium'] = magnesiumTarget > 0
        ? (nutrients['magnesium'] ?? 0) / magnesiumTarget * 100 : 100;

    final ironTarget = target.ironMin * 1.25;
    achievement['iron'] = ironTarget > 0
        ? (nutrients['iron'] ?? 0) / ironTarget * 100 : 100;

    final zincTarget = target.zincMin * 1.25;
    achievement['zinc'] = zincTarget > 0
        ? (nutrients['zinc'] ?? 0) / zincTarget * 100 : 100;

    // ビタミン: minのみなので min * 1.25 を目標に
    final vitaminATarget = target.vitaminAMin * 1.25;
    achievement['vitamin_a'] = vitaminATarget > 0
        ? (nutrients['vitamin_a'] ?? 0) / vitaminATarget * 100 : 100;

    final vitaminDTarget = target.vitaminDMin * 1.25;
    achievement['vitamin_d'] = vitaminDTarget > 0
        ? (nutrients['vitamin_d'] ?? 0) / vitaminDTarget * 100 : 100;

    final vitaminETarget = target.vitaminEMin * 1.25;
    achievement['vitamin_e'] = vitaminETarget > 0
        ? (nutrients['vitamin_e'] ?? 0) / vitaminETarget * 100 : 100;

    final vitaminKTarget = target.vitaminKMin * 1.25;
    achievement['vitamin_k'] = vitaminKTarget > 0
        ? (nutrients['vitamin_k'] ?? 0) / vitaminKTarget * 100 : 100;

    final vitaminB1Target = target.vitaminB1Min * 1.25;
    achievement['vitamin_b1'] = vitaminB1Target > 0
        ? (nutrients['vitamin_b1'] ?? 0) / vitaminB1Target * 100 : 100;

    final vitaminB2Target = target.vitaminB2Min * 1.25;
    achievement['vitamin_b2'] = vitaminB2Target > 0
        ? (nutrients['vitamin_b2'] ?? 0) / vitaminB2Target * 100 : 100;

    final vitaminB6Target = target.vitaminB6Min * 1.25;
    achievement['vitamin_b6'] = vitaminB6Target > 0
        ? (nutrients['vitamin_b6'] ?? 0) / vitaminB6Target * 100 : 100;

    final vitaminB12Target = target.vitaminB12Min * 1.25;
    achievement['vitamin_b12'] = vitaminB12Target > 0
        ? (nutrients['vitamin_b12'] ?? 0) / vitaminB12Target * 100 : 100;

    final niacinTarget = target.niacinMin * 1.25;
    achievement['niacin'] = niacinTarget > 0
        ? (nutrients['niacin'] ?? 0) / niacinTarget * 100 : 100;

    final pantothenicAcidTarget = target.pantothenicAcidMin * 1.25;
    achievement['pantothenic_acid'] = pantothenicAcidTarget > 0
        ? (nutrients['pantothenic_acid'] ?? 0) / pantothenicAcidTarget * 100 : 100;

    final biotinTarget = target.biotinMin * 1.25;
    achievement['biotin'] = biotinTarget > 0
        ? (nutrients['biotin'] ?? 0) / biotinTarget * 100 : 100;

    final folateTarget = target.folateMin * 1.25;
    achievement['folate'] = folateTarget > 0
        ? (nutrients['folate'] ?? 0) / folateTarget * 100 : 100;

    final vitaminCTarget = target.vitaminCMin * 1.25;
    achievement['vitamin_c'] = vitaminCTarget > 0
        ? (nutrients['vitamin_c'] ?? 0) / vitaminCTarget * 100 : 100;

    return achievement;
  }

  /// 全体の栄養素を計算
  Map<String, double> _calculateOverallNutrients(List<DailyMealAssignment> dailyPlans) {
    final overall = <String, double>{
      // 基本栄養素
      'calories': 0,
      'protein': 0,
      'fat': 0,
      'carbohydrate': 0,
      'fiber': 0,
      // ミネラル
      'sodium': 0,
      'potassium': 0,
      'calcium': 0,
      'magnesium': 0,
      'iron': 0,
      'zinc': 0,
      // ビタミン
      'vitamin_a': 0,
      'vitamin_d': 0,
      'vitamin_e': 0,
      'vitamin_k': 0,
      'vitamin_b1': 0,
      'vitamin_b2': 0,
      'vitamin_b6': 0,
      'vitamin_b12': 0,
      'niacin': 0,
      'pantothenic_acid': 0,
      'biotin': 0,
      'folate': 0,
      'vitamin_c': 0,
    };

    for (final day in dailyPlans) {
      for (final key in overall.keys) {
        overall[key] = overall[key]! + (day.totalNutrients[key] ?? 0);
      }
    }

    return overall;
  }

  /// 全体の達成率を計算（期間平均で計算）
  Map<String, double> _calculateOverallAchievement(
    Map<String, double> overallNutrients,
    int days,
  ) {
    // 期間平均（1日あたり）で達成率計算
    final avgNutrients = <String, double>{};
    for (final key in overallNutrients.keys) {
      avgNutrients[key] = (overallNutrients[key] ?? 0) / days;
    }
    return _calcAchievement(avgNutrients);
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
