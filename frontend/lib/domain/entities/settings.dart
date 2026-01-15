/// 食事プリセット
enum MealPreset {
  minimal('最小限', 'minimal', '主食のみ'),
  light('軽め', 'light', '主食＋主菜'),
  standard('標準', 'standard', '主食＋主菜＋副菜'),
  full('充実', 'full', '主食＋主菜＋副菜＋汁物'),
  japanese('和定食', 'japanese', '一汁三菜'),
  custom('カスタム', 'custom', '各カテゴリを個別に設定');

  final String displayName;
  final String apiValue;
  final String description;

  const MealPreset(this.displayName, this.apiValue, this.description);
}

/// カテゴリ別品数制約（min/max）
class CategoryConstraint {
  final int min;
  final int max;

  const CategoryConstraint({this.min = 0, this.max = 2});

  Map<String, dynamic> toJson() => {'min': min, 'max': max};

  CategoryConstraint copyWith({int? min, int? max}) {
    return CategoryConstraint(
      min: min ?? this.min,
      max: max ?? this.max,
    );
  }
}

/// 1食分のカテゴリ別品数制約
class MealCategoryConstraints {
  final CategoryConstraint staple;   // 主食
  final CategoryConstraint main;     // 主菜
  final CategoryConstraint side;     // 副菜
  final CategoryConstraint soup;     // 汁物
  final CategoryConstraint dessert;  // デザート

  const MealCategoryConstraints({
    this.staple = const CategoryConstraint(min: 1, max: 1),
    this.main = const CategoryConstraint(min: 1, max: 1),
    this.side = const CategoryConstraint(min: 0, max: 2),
    this.soup = const CategoryConstraint(min: 0, max: 1),
    this.dessert = const CategoryConstraint(min: 0, max: 1),
  });

  Map<String, dynamic> toJson() => {
    '主食': [staple.min, staple.max],
    '主菜': [main.min, main.max],
    '副菜': [side.min, side.max],
    '汁物': [soup.min, soup.max],
    'デザート': [dessert.min, dessert.max],
  };

  MealCategoryConstraints copyWith({
    CategoryConstraint? staple,
    CategoryConstraint? main,
    CategoryConstraint? side,
    CategoryConstraint? soup,
    CategoryConstraint? dessert,
  }) {
    return MealCategoryConstraints(
      staple: staple ?? this.staple,
      main: main ?? this.main,
      side: side ?? this.side,
      soup: soup ?? this.soup,
      dessert: dessert ?? this.dessert,
    );
  }
}

/// プリセット定義（各プリセットのカテゴリ制約）
const Map<MealPreset, MealCategoryConstraints> mealPresets = {
  MealPreset.minimal: MealCategoryConstraints(
    staple: CategoryConstraint(min: 1, max: 1),
    main: CategoryConstraint(min: 0, max: 0),
    side: CategoryConstraint(min: 0, max: 0),
    soup: CategoryConstraint(min: 0, max: 0),
    dessert: CategoryConstraint(min: 0, max: 0),
  ),
  MealPreset.light: MealCategoryConstraints(
    staple: CategoryConstraint(min: 1, max: 1),
    main: CategoryConstraint(min: 1, max: 1),
    side: CategoryConstraint(min: 0, max: 0),
    soup: CategoryConstraint(min: 0, max: 0),
    dessert: CategoryConstraint(min: 0, max: 0),
  ),
  MealPreset.standard: MealCategoryConstraints(
    staple: CategoryConstraint(min: 1, max: 1),
    main: CategoryConstraint(min: 1, max: 1),
    side: CategoryConstraint(min: 1, max: 1),
    soup: CategoryConstraint(min: 0, max: 1),
    dessert: CategoryConstraint(min: 0, max: 0),
  ),
  MealPreset.full: MealCategoryConstraints(
    staple: CategoryConstraint(min: 1, max: 1),
    main: CategoryConstraint(min: 1, max: 1),
    side: CategoryConstraint(min: 1, max: 2),
    soup: CategoryConstraint(min: 1, max: 1),
    dessert: CategoryConstraint(min: 0, max: 1),
  ),
  MealPreset.japanese: MealCategoryConstraints(
    staple: CategoryConstraint(min: 1, max: 1),
    main: CategoryConstraint(min: 1, max: 1),
    side: CategoryConstraint(min: 2, max: 3),
    soup: CategoryConstraint(min: 1, max: 1),
    dessert: CategoryConstraint(min: 0, max: 0),
  ),
};

/// デフォルトの朝昼夜別プリセット
const Map<String, MealPreset> defaultMealPresets = {
  'breakfast': MealPreset.light,
  'lunch': MealPreset.standard,
  'dinner': MealPreset.full,
};

/// 食事タイプ別の設定（拡張版）
class MealSetting {
  final bool enabled;
  final MealPreset preset;
  final MealCategoryConstraints? customCategories;  // preset=customの場合に使用

  const MealSetting({
    this.enabled = true,
    this.preset = MealPreset.standard,
    this.customCategories,
  });

  /// 有効なカテゴリ制約を取得
  MealCategoryConstraints getCategories() {
    if (preset == MealPreset.custom && customCategories != null) {
      return customCategories!;
    }
    return mealPresets[preset] ?? const MealCategoryConstraints();
  }

  Map<String, dynamic> toJson() {
    final categories = getCategories();
    return {
      'enabled': enabled,
      'categories': categories.toJson(),
    };
  }

  MealSetting copyWith({
    bool? enabled,
    MealPreset? preset,
    MealCategoryConstraints? customCategories,
  }) {
    return MealSetting(
      enabled: enabled ?? this.enabled,
      preset: preset ?? this.preset,
      customCategories: customCategories ?? this.customCategories,
    );
  }
}

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

/// 栄養素目標 - 日本人の食事摂取基準(2020年版)厚生労働省 準拠
/// デフォルト値は成人男女(18-64歳)の平均値を使用
/// ※バックエンド(schemas.py)と完全一致させること
class NutrientTarget {
  // 基本栄養素
  final double caloriesMin;
  final double caloriesMax;
  final double proteinMin;    // 男65/女50の平均
  final double proteinMax;
  final double fatMin;
  final double fatMax;
  final double carbohydrateMin;
  final double carbohydrateMax;
  final double fiberMin;      // 男21/女18の平均
  // ミネラル
  final double sodiumMax;     // mg - 食塩7.5g未満相当
  final double potassiumMin;  // mg - 目安量
  final double calciumMin;    // mg - 男775/女650の平均
  final double magnesiumMin;  // mg - 男355/女280の平均
  final double ironMin;       // mg - 男7.5/女10.5の平均
  final double zincMin;       // mg - 男11/女8の平均
  // ビタミン
  final double vitaminAMin;   // μg (RAE) - 男875/女675の平均
  final double vitaminDMin;   // μg - 目安量
  final double vitaminEMin;   // mg (α-トコフェロール) - 目安量
  final double vitaminKMin;   // μg - 目安量
  final double vitaminB1Min;  // mg - 男1.35/女1.1の平均
  final double vitaminB2Min;  // mg - 男1.55/女1.2の平均
  final double vitaminB6Min;  // mg - 男1.4/女1.1の平均
  final double vitaminB12Min; // μg - 推奨量
  final double niacinMin;     // mg NE - 男15/女12の平均
  final double pantothenicAcidMin;  // mg - 男6/女5の平均
  final double biotinMin;     // μg - 目安量
  final double folateMin;     // μg - 推奨量
  final double vitaminCMin;   // mg - 推奨量

  const NutrientTarget({
    this.caloriesMin = 1800,
    this.caloriesMax = 2200,
    this.proteinMin = 58,
    this.proteinMax = 100,
    this.fatMin = 50,
    this.fatMax = 80,
    this.carbohydrateMin = 250,
    this.carbohydrateMax = 350,
    this.fiberMin = 20,
    this.sodiumMax = 2500,
    this.potassiumMin = 2500,    // バックエンドと一致
    this.calciumMin = 700,
    this.magnesiumMin = 320,     // バックエンドと一致
    this.ironMin = 9.0,
    this.zincMin = 10,           // バックエンドと一致
    this.vitaminAMin = 775,
    this.vitaminDMin = 8.5,
    this.vitaminEMin = 6.0,      // バックエンドと一致
    this.vitaminKMin = 150,
    this.vitaminB1Min = 1.2,     // バックエンドと一致
    this.vitaminB2Min = 1.4,
    this.vitaminB6Min = 1.3,     // バックエンドと一致
    this.vitaminB12Min = 2.4,
    this.niacinMin = 13.5,
    this.pantothenicAcidMin = 5.5,
    this.biotinMin = 50,
    this.folateMin = 240,
    this.vitaminCMin = 100,
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
      'potassium_min': potassiumMin,
      'calcium_min': calciumMin,
      'magnesium_min': magnesiumMin,
      'iron_min': ironMin,
      'zinc_min': zincMin,
      'vitamin_a_min': vitaminAMin,
      'vitamin_d_min': vitaminDMin,
      'vitamin_e_min': vitaminEMin,
      'vitamin_k_min': vitaminKMin,
      'vitamin_b1_min': vitaminB1Min,
      'vitamin_b2_min': vitaminB2Min,
      'vitamin_b6_min': vitaminB6Min,
      'vitamin_b12_min': vitaminB12Min,
      'niacin_min': niacinMin,
      'pantothenic_acid_min': pantothenicAcidMin,
      'biotin_min': biotinMin,
      'folate_min': folateMin,
      'vitamin_c_min': vitaminCMin,
    };
  }

  factory NutrientTarget.fromJson(Map<String, dynamic> json) {
    return NutrientTarget(
      caloriesMin: (json['calories_min'] ?? 1800).toDouble(),
      caloriesMax: (json['calories_max'] ?? 2200).toDouble(),
      proteinMin: (json['protein_min'] ?? 58).toDouble(),
      proteinMax: (json['protein_max'] ?? 100).toDouble(),
      fatMin: (json['fat_min'] ?? 50).toDouble(),
      fatMax: (json['fat_max'] ?? 80).toDouble(),
      carbohydrateMin: (json['carbohydrate_min'] ?? 250).toDouble(),
      carbohydrateMax: (json['carbohydrate_max'] ?? 350).toDouble(),
      fiberMin: (json['fiber_min'] ?? 20).toDouble(),
      sodiumMax: (json['sodium_max'] ?? 2500).toDouble(),
      potassiumMin: (json['potassium_min'] ?? 2250).toDouble(),
      calciumMin: (json['calcium_min'] ?? 700).toDouble(),
      magnesiumMin: (json['magnesium_min'] ?? 305).toDouble(),
      ironMin: (json['iron_min'] ?? 9.0).toDouble(),
      zincMin: (json['zinc_min'] ?? 9.5).toDouble(),
      vitaminAMin: (json['vitamin_a_min'] ?? 775).toDouble(),
      vitaminDMin: (json['vitamin_d_min'] ?? 8.5).toDouble(),
      vitaminEMin: (json['vitamin_e_min'] ?? 6.25).toDouble(),
      vitaminKMin: (json['vitamin_k_min'] ?? 150).toDouble(),
      vitaminB1Min: (json['vitamin_b1_min'] ?? 1.25).toDouble(),
      vitaminB2Min: (json['vitamin_b2_min'] ?? 1.4).toDouble(),
      vitaminB6Min: (json['vitamin_b6_min'] ?? 1.25).toDouble(),
      vitaminB12Min: (json['vitamin_b12_min'] ?? 2.4).toDouble(),
      niacinMin: (json['niacin_min'] ?? 13.5).toDouble(),
      pantothenicAcidMin: (json['pantothenic_acid_min'] ?? 5.5).toDouble(),
      biotinMin: (json['biotin_min'] ?? 50).toDouble(),
      folateMin: (json['folate_min'] ?? 240).toDouble(),
      vitaminCMin: (json['vitamin_c_min'] ?? 100).toDouble(),
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
  final Set<int> favoriteDishIds;
  final Set<int> favoriteIngredientIds; // お気に入り食材
  // 献立生成のデフォルト設定
  final String varietyLevel; // small/normal/large
  final Map<String, MealSetting> mealSettings; // 朝昼夜のプリセット

  const AppSettings({
    this.defaultDays = 3,
    this.defaultPeople = 2,
    this.excludedAllergens = const {},
    this.nutrientTarget = const NutrientTarget(),
    this.favoriteDishIds = const {},
    this.favoriteIngredientIds = const {},
    this.varietyLevel = 'normal',
    this.mealSettings = const {
      'breakfast': MealSetting(enabled: true, preset: MealPreset.light),
      'lunch': MealSetting(enabled: true, preset: MealPreset.standard),
      'dinner': MealSetting(enabled: true, preset: MealPreset.full),
    },
  });

  AppSettings copyWith({
    int? defaultDays,
    int? defaultPeople,
    Set<Allergen>? excludedAllergens,
    NutrientTarget? nutrientTarget,
    Set<int>? favoriteDishIds,
    Set<int>? favoriteIngredientIds,
    String? varietyLevel,
    Map<String, MealSetting>? mealSettings,
  }) {
    return AppSettings(
      defaultDays: defaultDays ?? this.defaultDays,
      defaultPeople: defaultPeople ?? this.defaultPeople,
      excludedAllergens: excludedAllergens ?? this.excludedAllergens,
      nutrientTarget: nutrientTarget ?? this.nutrientTarget,
      favoriteDishIds: favoriteDishIds ?? this.favoriteDishIds,
      favoriteIngredientIds: favoriteIngredientIds ?? this.favoriteIngredientIds,
      varietyLevel: varietyLevel ?? this.varietyLevel,
      mealSettings: mealSettings ?? this.mealSettings,
    );
  }
}
