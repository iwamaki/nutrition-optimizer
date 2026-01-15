import 'dish.dart';

/// 1食分のメニュー（料理ベース）
class MealPlan {
  final String name;
  final List<DishPortion> dishes;
  final double totalCalories;
  final double totalProtein;
  final double totalFat;
  final double totalCarbohydrate;
  final double totalFiber;
  final double totalSodium;
  final double totalCalcium;
  final double totalIron;
  final double totalVitaminA;
  final double totalVitaminC;
  final double totalVitaminD;

  MealPlan({
    required this.name,
    required this.dishes,
    this.totalCalories = 0,
    this.totalProtein = 0,
    this.totalFat = 0,
    this.totalCarbohydrate = 0,
    this.totalFiber = 0,
    this.totalSodium = 0,
    this.totalCalcium = 0,
    this.totalIron = 0,
    this.totalVitaminA = 0,
    this.totalVitaminC = 0,
    this.totalVitaminD = 0,
  });

  factory MealPlan.fromJson(Map<String, dynamic> json) {
    return MealPlan(
      name: json['name'],
      dishes: (json['dishes'] as List?)
              ?.map((e) => DishPortion.fromJson(e))
              .toList() ??
          [],
      totalCalories: (json['total_calories'] ?? 0).toDouble(),
      totalProtein: (json['total_protein'] ?? 0).toDouble(),
      totalFat: (json['total_fat'] ?? 0).toDouble(),
      totalCarbohydrate: (json['total_carbohydrate'] ?? 0).toDouble(),
      totalFiber: (json['total_fiber'] ?? 0).toDouble(),
      totalSodium: (json['total_sodium'] ?? 0).toDouble(),
      totalCalcium: (json['total_calcium'] ?? 0).toDouble(),
      totalIron: (json['total_iron'] ?? 0).toDouble(),
      totalVitaminA: (json['total_vitamin_a'] ?? 0).toDouble(),
      totalVitaminC: (json['total_vitamin_c'] ?? 0).toDouble(),
      totalVitaminD: (json['total_vitamin_d'] ?? 0).toDouble(),
    );
  }

  String get displayName {
    switch (name) {
      case 'breakfast':
        return '朝食';
      case 'lunch':
        return '昼食';
      case 'dinner':
        return '夕食';
      default:
        return name;
    }
  }
}

/// 食事タイプ
enum MealType { breakfast, lunch, dinner }

/// 1日分の食事割り当て
class DailyMealAssignment {
  final int day;
  final List<DishPortion> breakfast;
  final List<DishPortion> lunch;
  final List<DishPortion> dinner;
  final Map<String, double> totalNutrients;
  final Map<String, double> achievementRate;

  DailyMealAssignment({
    required this.day,
    required this.breakfast,
    required this.lunch,
    required this.dinner,
    required this.totalNutrients,
    required this.achievementRate,
  });

  /// 指定した食事タイプの料理リストを取得
  List<DishPortion> getMealDishes(MealType mealType) {
    switch (mealType) {
      case MealType.breakfast:
        return breakfast;
      case MealType.lunch:
        return lunch;
      case MealType.dinner:
        return dinner;
    }
  }

  /// コピーを作成（食事リストを更新可能）
  DailyMealAssignment copyWith({
    int? day,
    List<DishPortion>? breakfast,
    List<DishPortion>? lunch,
    List<DishPortion>? dinner,
    Map<String, double>? totalNutrients,
    Map<String, double>? achievementRate,
  }) {
    return DailyMealAssignment(
      day: day ?? this.day,
      breakfast: breakfast ?? List.from(this.breakfast),
      lunch: lunch ?? List.from(this.lunch),
      dinner: dinner ?? List.from(this.dinner),
      totalNutrients: totalNutrients ?? Map.from(this.totalNutrients),
      achievementRate: achievementRate ?? Map.from(this.achievementRate),
    );
  }

  factory DailyMealAssignment.fromJson(Map<String, dynamic> json) {
    return DailyMealAssignment(
      day: json['day'],
      breakfast: (json['breakfast'] as List?)
              ?.map((e) => DishPortion.fromJson(e))
              .toList() ??
          [],
      lunch: (json['lunch'] as List?)
              ?.map((e) => DishPortion.fromJson(e))
              .toList() ??
          [],
      dinner: (json['dinner'] as List?)
              ?.map((e) => DishPortion.fromJson(e))
              .toList() ??
          [],
      totalNutrients: _parseDoubleMap(json['total_nutrients']),
      achievementRate: _parseDoubleMap(json['achievement_rate']),
    );
  }

  double get totalCalories => totalNutrients['calories'] ?? 0;
}

/// 栄養素警告
class NutrientWarning {
  final String nutrient;
  final String message;
  final double currentValue;
  final double targetValue;
  final double deficitPercent;

  NutrientWarning({
    required this.nutrient,
    required this.message,
    required this.currentValue,
    required this.targetValue,
    required this.deficitPercent,
  });

  factory NutrientWarning.fromJson(Map<String, dynamic> json) {
    return NutrientWarning(
      nutrient: json['nutrient'],
      message: json['message'],
      currentValue: (json['current_value'] ?? 0).toDouble(),
      targetValue: (json['target_value'] ?? 0).toDouble(),
      deficitPercent: (json['deficit_percent'] ?? 0).toDouble(),
    );
  }
}

/// 複数日メニュープラン
class MultiDayMenuPlan {
  final String planId;
  final int days;
  final int people;
  final List<DailyMealAssignment> dailyPlans;
  final List<CookingTask> cookingTasks;
  final List<ShoppingItem> shoppingList;
  final Map<String, double> overallNutrients;
  final Map<String, double> overallAchievement;
  final List<NutrientWarning> warnings;

  MultiDayMenuPlan({
    required this.planId,
    required this.days,
    required this.people,
    required this.dailyPlans,
    required this.cookingTasks,
    required this.shoppingList,
    required this.overallNutrients,
    required this.overallAchievement,
    this.warnings = const [],
  });

  factory MultiDayMenuPlan.fromJson(Map<String, dynamic> json) {
    return MultiDayMenuPlan(
      planId: json['plan_id'],
      days: json['days'],
      people: json['people'],
      dailyPlans: (json['daily_plans'] as List?)
              ?.map((e) => DailyMealAssignment.fromJson(e))
              .toList() ??
          [],
      cookingTasks: (json['cooking_tasks'] as List?)
              ?.map((e) => CookingTask.fromJson(e))
              .toList() ??
          [],
      shoppingList: (json['shopping_list'] as List?)
              ?.map((e) => ShoppingItem.fromJson(e))
              .toList() ??
          [],
      overallNutrients: _parseDoubleMap(json['overall_nutrients']),
      overallAchievement: _parseDoubleMap(json['overall_achievement']),
      warnings: (json['warnings'] as List?)
              ?.map((e) => NutrientWarning.fromJson(e))
              .toList() ??
          [],
    );
  }

  double get averageAchievement {
    if (overallAchievement.isEmpty) return 0;
    final values = overallAchievement.values.toList();
    return values.reduce((a, b) => a + b) / values.length;
  }
}

/// 調理タスク
class CookingTask {
  final int cookDay;
  final Dish dish;
  final int servings;
  final List<int> consumeDays;

  CookingTask({
    required this.cookDay,
    required this.dish,
    required this.servings,
    required this.consumeDays,
  });

  factory CookingTask.fromJson(Map<String, dynamic> json) {
    return CookingTask(
      cookDay: json['cook_day'],
      dish: Dish.fromJson(json['dish']),
      servings: json['servings'],
      consumeDays:
          (json['consume_days'] as List?)?.map((e) => e as int).toList() ?? [],
    );
  }
}

/// 買い物リストアイテム
class ShoppingItem {
  final String foodName;
  final double totalAmount;
  final String displayAmount;  // 表示用の量（例: "2", "1/2"）
  final String unit;           // 単位（例: "本", "個", "g"）
  final String category;
  final bool isOwned;          // 手持ち食材かどうか（念のため購入検討用）
  bool isChecked;

  ShoppingItem({
    required this.foodName,
    required this.totalAmount,
    this.displayAmount = '',
    this.unit = 'g',
    required this.category,
    this.isOwned = false,
    this.isChecked = false,
  });

  factory ShoppingItem.fromJson(Map<String, dynamic> json) {
    return ShoppingItem(
      foodName: json['food_name'],
      totalAmount: (json['total_amount'] ?? 0).toDouble(),
      displayAmount: json['display_amount'] ?? '',
      unit: json['unit'] ?? 'g',
      category: json['category'] ?? '',
      isOwned: json['is_owned'] ?? false,
    );
  }

  /// 表示用の量（単位付き + グラム表示）
  String get amountDisplay {
    // 単位がgやkg、mlの場合は重量のみ
    if (unit == 'g' || unit == 'kg' || unit == 'ml' || unit == 'L') {
      if (totalAmount >= 1000) {
        return '${(totalAmount / 1000).toStringAsFixed(1)}kg';
      }
      return '${totalAmount.toStringAsFixed(0)}$unit';
    }
    // それ以外は「2本 (150g)」のような形式
    final gramDisplay = totalAmount >= 1000
        ? '${(totalAmount / 1000).toStringAsFixed(1)}kg'
        : '${totalAmount.toStringAsFixed(0)}g';
    return '$displayAmount$unit ($gramDisplay)';
  }
}

// Map<String, double>パーサー
Map<String, double> _parseDoubleMap(dynamic json) {
  if (json == null) return {};
  return Map<String, double>.from(
    (json as Map).map(
      (k, v) => MapEntry(k.toString(), (v ?? 0).toDouble()),
    ),
  );
}
