import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../domain/entities/settings.dart';

part 'settings_provider.g.dart';

/// アプリ設定の状態
class SettingsState {
  final AppSettings settings;
  final bool isLoading;

  const SettingsState({
    this.settings = const AppSettings(),
    this.isLoading = false,
  });

  SettingsState copyWith({
    AppSettings? settings,
    bool? isLoading,
  }) {
    return SettingsState(
      settings: settings ?? this.settings,
      isLoading: isLoading ?? this.isLoading,
    );
  }

  // 便利なgetters
  int get defaultDays => settings.defaultDays;
  int get defaultPeople => settings.defaultPeople;
  Set<Allergen> get excludedAllergens => settings.excludedAllergens;
  NutrientTarget get nutrientTarget => settings.nutrientTarget;
  Set<int> get favoriteDishIds => settings.favoriteDishIds;
  Set<int> get favoriteIngredientIds => settings.favoriteIngredientIds;
  Set<int> get excludedIngredientIds => settings.excludedIngredientIds;
  String get varietyLevel => settings.varietyLevel;
  Map<String, MealSetting> get mealSettings => settings.mealSettings;
  Set<String>? get enabledOptionalNutrients => settings.enabledOptionalNutrients;

  bool isFavorite(int dishId) => settings.favoriteDishIds.contains(dishId);
  bool isIngredientFavorite(int ingredientId) => settings.favoriteIngredientIds.contains(ingredientId);
  bool isIngredientExcluded(int ingredientId) => settings.excludedIngredientIds.contains(ingredientId);

  /// オプション栄養素が有効かどうか（nullの場合は全て有効）
  bool isOptionalNutrientEnabled(String key) {
    final enabled = settings.enabledOptionalNutrients;
    return enabled == null || enabled.contains(key);
  }
}

/// 設定管理Notifier
@riverpod
class SettingsNotifier extends _$SettingsNotifier {
  @override
  SettingsState build() {
    _loadSettings();
    return const SettingsState(isLoading: true);
  }

  Future<void> _loadSettings() async {
    try {
      final prefs = await SharedPreferences.getInstance();

      final days = prefs.getInt('defaultDays') ?? 3;
      final people = prefs.getInt('defaultPeople') ?? 2;

      final allergenList = prefs.getStringList('excludedAllergens') ?? [];
      final allergens = allergenList
          .map((a) => Allergen.fromApiValue(a))
          .whereType<Allergen>()
          .toSet();

      final favoriteList = prefs.getStringList('favoriteDishIds') ?? [];
      final favorites = favoriteList
          .map((s) => int.tryParse(s))
          .whereType<int>()
          .toSet();

      final favoriteIngredientList = prefs.getStringList('favoriteIngredientIds') ?? [];
      final favoriteIngredients = favoriteIngredientList
          .map((s) => int.tryParse(s))
          .whereType<int>()
          .toSet();

      final excludedIngredientList = prefs.getStringList('excludedIngredientIds') ?? [];
      final excludedIngredients = excludedIngredientList
          .map((s) => int.tryParse(s))
          .whereType<int>()
          .toSet();

      final caloriesMin = prefs.getDouble('caloriesMin') ?? 1800;
      final caloriesMax = prefs.getDouble('caloriesMax') ?? 2200;
      final proteinMin = prefs.getDouble('proteinMin') ?? 60;
      final proteinMax = prefs.getDouble('proteinMax') ?? 100;

      // 新しい設定項目
      final varietyLevel = prefs.getString('varietyLevel') ?? 'normal';

      // 朝昼夜のプリセット
      final mealSettings = <String, MealSetting>{};
      for (final mealType in ['breakfast', 'lunch', 'dinner']) {
        final enabled = prefs.getBool('meal_${mealType}_enabled') ?? true;
        final presetStr = prefs.getString('meal_${mealType}_preset');
        final preset = _parseMealPreset(presetStr, mealType);
        mealSettings[mealType] = MealSetting(enabled: enabled, preset: preset);
      }

      // オプション栄養素の有効/無効設定（nullの場合は全て有効）
      final enabledOptionalNutrientsStr = prefs.getStringList('enabledOptionalNutrients');
      final enabledOptionalNutrients = enabledOptionalNutrientsStr?.toSet();

      state = SettingsState(
        settings: AppSettings(
          defaultDays: days,
          defaultPeople: people,
          excludedAllergens: allergens,
          favoriteDishIds: favorites,
          favoriteIngredientIds: favoriteIngredients,
          excludedIngredientIds: excludedIngredients,
          nutrientTarget: NutrientTarget(
            caloriesMin: caloriesMin,
            caloriesMax: caloriesMax,
            proteinMin: proteinMin,
            proteinMax: proteinMax,
          ),
          varietyLevel: varietyLevel,
          mealSettings: mealSettings,
          enabledOptionalNutrients: enabledOptionalNutrients,
        ),
        isLoading: false,
      );
    } catch (e) {
      state = const SettingsState(isLoading: false);
    }
  }

  MealPreset _parseMealPreset(String? str, String mealType) {
    if (str == null) {
      // デフォルト値
      return defaultMealPresets[mealType] ?? MealPreset.standard;
    }
    for (final preset in MealPreset.values) {
      if (preset.apiValue == str) return preset;
    }
    return defaultMealPresets[mealType] ?? MealPreset.standard;
  }

  Future<void> _saveSettings() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final settings = state.settings;

      await prefs.setInt('defaultDays', settings.defaultDays);
      await prefs.setInt('defaultPeople', settings.defaultPeople);
      await prefs.setStringList(
        'excludedAllergens',
        settings.excludedAllergens.map((a) => a.displayName).toList(),
      );
      await prefs.setStringList(
        'favoriteDishIds',
        settings.favoriteDishIds.map((id) => id.toString()).toList(),
      );
      await prefs.setStringList(
        'favoriteIngredientIds',
        settings.favoriteIngredientIds.map((id) => id.toString()).toList(),
      );
      await prefs.setStringList(
        'excludedIngredientIds',
        settings.excludedIngredientIds.map((id) => id.toString()).toList(),
      );
      await prefs.setDouble('caloriesMin', settings.nutrientTarget.caloriesMin);
      await prefs.setDouble('caloriesMax', settings.nutrientTarget.caloriesMax);
      await prefs.setDouble('proteinMin', settings.nutrientTarget.proteinMin);
      await prefs.setDouble('proteinMax', settings.nutrientTarget.proteinMax);

      // 新しい設定項目
      await prefs.setString('varietyLevel', settings.varietyLevel);

      // 朝昼夜のプリセット
      for (final entry in settings.mealSettings.entries) {
        await prefs.setBool('meal_${entry.key}_enabled', entry.value.enabled);
        await prefs.setString('meal_${entry.key}_preset', entry.value.preset.apiValue);
      }

      // オプション栄養素の有効/無効設定
      if (settings.enabledOptionalNutrients != null) {
        await prefs.setStringList(
          'enabledOptionalNutrients',
          settings.enabledOptionalNutrients!.toList(),
        );
      } else {
        await prefs.remove('enabledOptionalNutrients');
      }
    } catch (e) {
      // 保存失敗を無視
    }
  }

  Future<void> setDefaultDays(int days) async {
    state = state.copyWith(
      settings: state.settings.copyWith(defaultDays: days.clamp(1, 7)),
    );
    await _saveSettings();
  }

  Future<void> setDefaultPeople(int people) async {
    state = state.copyWith(
      settings: state.settings.copyWith(defaultPeople: people.clamp(1, 6)),
    );
    await _saveSettings();
  }

  Future<void> toggleAllergen(Allergen allergen) async {
    final current = Set<Allergen>.from(state.settings.excludedAllergens);
    if (current.contains(allergen)) {
      current.remove(allergen);
    } else {
      current.add(allergen);
    }
    state = state.copyWith(
      settings: state.settings.copyWith(excludedAllergens: current),
    );
    await _saveSettings();
  }

  Future<void> setExcludedAllergens(Set<Allergen> allergens) async {
    state = state.copyWith(
      settings: state.settings.copyWith(excludedAllergens: allergens),
    );
    await _saveSettings();
  }

  Future<void> setVarietyLevel(String level) async {
    state = state.copyWith(
      settings: state.settings.copyWith(varietyLevel: level),
    );
    await _saveSettings();
  }

  Future<void> setMealSetting(String mealType, MealSetting setting) async {
    final current = Map<String, MealSetting>.from(state.settings.mealSettings);
    current[mealType] = setting;
    state = state.copyWith(
      settings: state.settings.copyWith(mealSettings: current),
    );
    await _saveSettings();
  }

  Future<void> setMealEnabled(String mealType, bool enabled) async {
    final current = Map<String, MealSetting>.from(state.settings.mealSettings);
    final currentSetting = current[mealType] ?? const MealSetting();
    current[mealType] = currentSetting.copyWith(enabled: enabled);
    state = state.copyWith(
      settings: state.settings.copyWith(mealSettings: current),
    );
    await _saveSettings();
  }

  Future<void> setMealPreset(String mealType, MealPreset preset) async {
    final current = Map<String, MealSetting>.from(state.settings.mealSettings);
    final currentSetting = current[mealType] ?? const MealSetting();
    current[mealType] = currentSetting.copyWith(preset: preset);
    state = state.copyWith(
      settings: state.settings.copyWith(mealSettings: current),
    );
    await _saveSettings();
  }

  Future<void> setCaloriesRange(double min, double max) async {
    state = state.copyWith(
      settings: state.settings.copyWith(
        nutrientTarget: state.settings.nutrientTarget.copyWith(
          caloriesMin: min,
          caloriesMax: max,
        ),
      ),
    );
    await _saveSettings();
  }

  Future<void> setProteinRange(double min, double max) async {
    state = state.copyWith(
      settings: state.settings.copyWith(
        nutrientTarget: state.settings.nutrientTarget.copyWith(
          proteinMin: min,
          proteinMax: max,
        ),
      ),
    );
    await _saveSettings();
  }

  Future<void> resetSettings() async {
    state = const SettingsState();
    await _saveSettings();
  }

  Future<void> toggleFavoriteDish(int dishId) async {
    final current = Set<int>.from(state.settings.favoriteDishIds);
    if (current.contains(dishId)) {
      current.remove(dishId);
    } else {
      current.add(dishId);
    }
    state = state.copyWith(
      settings: state.settings.copyWith(favoriteDishIds: current),
    );
    await _saveSettings();
  }

  Future<void> toggleFavoriteIngredient(int ingredientId) async {
    final currentFavorites = Set<int>.from(state.settings.favoriteIngredientIds);
    final currentExcluded = Set<int>.from(state.settings.excludedIngredientIds);

    if (currentFavorites.contains(ingredientId)) {
      currentFavorites.remove(ingredientId);
    } else {
      currentFavorites.add(ingredientId);
      // お気に入りにしたら除外から削除
      currentExcluded.remove(ingredientId);
    }
    state = state.copyWith(
      settings: state.settings.copyWith(
        favoriteIngredientIds: currentFavorites,
        excludedIngredientIds: currentExcluded,
      ),
    );
    await _saveSettings();
  }

  Future<void> toggleExcludedIngredient(int ingredientId) async {
    final currentFavorites = Set<int>.from(state.settings.favoriteIngredientIds);
    final currentExcluded = Set<int>.from(state.settings.excludedIngredientIds);

    if (currentExcluded.contains(ingredientId)) {
      currentExcluded.remove(ingredientId);
    } else {
      currentExcluded.add(ingredientId);
      // 除外したらお気に入りから削除
      currentFavorites.remove(ingredientId);
    }
    state = state.copyWith(
      settings: state.settings.copyWith(
        favoriteIngredientIds: currentFavorites,
        excludedIngredientIds: currentExcluded,
      ),
    );
    await _saveSettings();
  }

  /// オプション栄養素の有効/無効を切り替え
  Future<void> toggleOptionalNutrient(String nutrientKey) async {
    final current = state.settings.enabledOptionalNutrients;

    Set<String> newEnabled;
    if (current == null) {
      // 初回: 全て有効から1つ除外
      newEnabled = {
        'sodium', 'potassium', 'magnesium', 'zinc',
        'vitamin_a', 'vitamin_e', 'vitamin_k',
        'vitamin_b1', 'vitamin_b2', 'vitamin_b6', 'vitamin_b12',
        'niacin', 'pantothenic_acid', 'biotin', 'folate', 'vitamin_c',
      };
      newEnabled.remove(nutrientKey);
    } else if (current.contains(nutrientKey)) {
      // 有効→無効
      newEnabled = Set<String>.from(current)..remove(nutrientKey);
    } else {
      // 無効→有効
      newEnabled = Set<String>.from(current)..add(nutrientKey);
    }

    state = state.copyWith(
      settings: state.settings.copyWith(enabledOptionalNutrients: newEnabled),
    );
    await _saveSettings();
  }

  /// 全オプション栄養素を有効化（nullに戻す）
  Future<void> enableAllOptionalNutrients() async {
    state = state.copyWith(
      settings: state.settings.copyWith(clearEnabledOptionalNutrients: true),
    );
    await _saveSettings();
  }

  /// コア栄養素のみ有効化（全オプションを無効化）
  Future<void> enableCoreNutrientsOnly() async {
    state = state.copyWith(
      settings: state.settings.copyWith(enabledOptionalNutrients: {}),
    );
    await _saveSettings();
  }
}
