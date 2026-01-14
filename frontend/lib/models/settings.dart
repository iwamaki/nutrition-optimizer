/// アレルゲン（7大アレルゲン）
enum Allergen {
  egg('卵', 'EGG'),
  milk('乳', 'MILK'),
  wheat('小麦', 'WHEAT'),
  buckwheat('そば', 'BUCKWHEAT'),
  peanut('落花生', 'PEANUT'),
  shrimp('えび', 'SHRIMP'),
  crab('かに', 'CRAB');

  final String displayName;
  final String apiValue;

  const Allergen(this.displayName, this.apiValue);

  static Allergen? fromApiValue(String value) {
    for (final allergen in Allergen.values) {
      if (allergen.displayName == value || allergen.apiValue == value) {
        return allergen;
      }
    }
    return null;
  }
}

/// 栄養素目標
class NutrientTarget {
  final double caloriesMin;
  final double caloriesMax;
  final double proteinMin;
  final double proteinMax;
  final double fatMin;
  final double fatMax;
  final double carbohydrateMin;
  final double carbohydrateMax;
  final double fiberMin;
  final double sodiumMax;
  final double calciumMin;
  final double ironMin;
  final double vitaminAMin;
  final double vitaminCMin;
  final double vitaminDMin;

  NutrientTarget({
    this.caloriesMin = 1800,
    this.caloriesMax = 2200,
    this.proteinMin = 60,
    this.proteinMax = 100,
    this.fatMin = 50,
    this.fatMax = 80,
    this.carbohydrateMin = 250,
    this.carbohydrateMax = 350,
    this.fiberMin = 20,
    this.sodiumMax = 2500,
    this.calciumMin = 650,
    this.ironMin = 7.5,
    this.vitaminAMin = 850,
    this.vitaminCMin = 100,
    this.vitaminDMin = 8.5,
  });

  Map<String, dynamic> toJson() {
    return {
      'calories_min': caloriesMin,
      'calories_max': caloriesMax,
      'protein_min': proteinMin,
      'protein_max': proteinMax,
      'fat_min': fatMin,
      'fat_max': fatMax,
      'carbohydrate_min': carbohydrateMin,
      'carbohydrate_max': carbohydrateMax,
      'fiber_min': fiberMin,
      'sodium_max': sodiumMax,
      'calcium_min': calciumMin,
      'iron_min': ironMin,
      'vitamin_a_min': vitaminAMin,
      'vitamin_c_min': vitaminCMin,
      'vitamin_d_min': vitaminDMin,
    };
  }

  factory NutrientTarget.fromJson(Map<String, dynamic> json) {
    return NutrientTarget(
      caloriesMin: (json['calories_min'] ?? 1800).toDouble(),
      caloriesMax: (json['calories_max'] ?? 2200).toDouble(),
      proteinMin: (json['protein_min'] ?? 60).toDouble(),
      proteinMax: (json['protein_max'] ?? 100).toDouble(),
      fatMin: (json['fat_min'] ?? 50).toDouble(),
      fatMax: (json['fat_max'] ?? 80).toDouble(),
      carbohydrateMin: (json['carbohydrate_min'] ?? 250).toDouble(),
      carbohydrateMax: (json['carbohydrate_max'] ?? 350).toDouble(),
      fiberMin: (json['fiber_min'] ?? 20).toDouble(),
      sodiumMax: (json['sodium_max'] ?? 2500).toDouble(),
      calciumMin: (json['calcium_min'] ?? 650).toDouble(),
      ironMin: (json['iron_min'] ?? 7.5).toDouble(),
      vitaminAMin: (json['vitamin_a_min'] ?? 850).toDouble(),
      vitaminCMin: (json['vitamin_c_min'] ?? 100).toDouble(),
      vitaminDMin: (json['vitamin_d_min'] ?? 8.5).toDouble(),
    );
  }

  NutrientTarget copyWith({
    double? caloriesMin,
    double? caloriesMax,
    double? proteinMin,
    double? proteinMax,
  }) {
    return NutrientTarget(
      caloriesMin: caloriesMin ?? this.caloriesMin,
      caloriesMax: caloriesMax ?? this.caloriesMax,
      proteinMin: proteinMin ?? this.proteinMin,
      proteinMax: proteinMax ?? this.proteinMax,
      fatMin: fatMin,
      fatMax: fatMax,
      carbohydrateMin: carbohydrateMin,
      carbohydrateMax: carbohydrateMax,
      fiberMin: fiberMin,
      sodiumMax: sodiumMax,
      calciumMin: calciumMin,
      ironMin: ironMin,
      vitaminAMin: vitaminAMin,
      vitaminCMin: vitaminCMin,
      vitaminDMin: vitaminDMin,
    );
  }
}

/// ユーザー設定
class UserPreferences {
  final double caloriesTarget;
  final List<String> excludedCategories;
  final List<int> excludedFoodIds;

  UserPreferences({
    this.caloriesTarget = 2000,
    this.excludedCategories = const [],
    this.excludedFoodIds = const [],
  });

  factory UserPreferences.fromJson(Map<String, dynamic> json) {
    return UserPreferences(
      caloriesTarget: (json['calories_target'] ?? 2000).toDouble(),
      excludedCategories: (json['excluded_categories'] as List?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      excludedFoodIds:
          (json['excluded_food_ids'] as List?)?.map((e) => e as int).toList() ??
              [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'calories_target': caloriesTarget,
      'excluded_categories': excludedCategories,
      'excluded_food_ids': excludedFoodIds,
    };
  }
}

/// アプリ設定（ローカル保存用）
class AppSettings {
  final int defaultDays;
  final int defaultPeople;
  final Set<Allergen> excludedAllergens;
  final NutrientTarget nutrientTarget;
  final bool preferBatchCooking;

  AppSettings({
    this.defaultDays = 3,
    this.defaultPeople = 2,
    this.excludedAllergens = const {},
    NutrientTarget? nutrientTarget,
    this.preferBatchCooking = false,
  }) : nutrientTarget = nutrientTarget ?? NutrientTarget();

  AppSettings copyWith({
    int? defaultDays,
    int? defaultPeople,
    Set<Allergen>? excludedAllergens,
    NutrientTarget? nutrientTarget,
    bool? preferBatchCooking,
  }) {
    return AppSettings(
      defaultDays: defaultDays ?? this.defaultDays,
      defaultPeople: defaultPeople ?? this.defaultPeople,
      excludedAllergens: excludedAllergens ?? this.excludedAllergens,
      nutrientTarget: nutrientTarget ?? this.nutrientTarget,
      preferBatchCooking: preferBatchCooking ?? this.preferBatchCooking,
    );
  }
}
