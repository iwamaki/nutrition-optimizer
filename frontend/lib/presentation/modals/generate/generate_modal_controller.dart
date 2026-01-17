import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../../domain/entities/dish.dart';
import '../../../domain/entities/menu_plan.dart';
import '../../../domain/entities/settings.dart';
import '../../../domain/entities/optimize_progress.dart';
import '../../../data/repositories/menu_repository_impl.dart';
import '../../../data/repositories/food_repository_impl.dart';
import '../../../data/datasources/api_service.dart';

part 'generate_modal_controller.g.dart';

/// 献立生成モーダルの状態
class GenerateModalState {
  // 現在のステップ（0:基本設定, 1:お気に入り, 2:手持ち食材, 3:確認）
  final int currentStep;

  // Step0: 基本設定
  final int days;
  final int people;
  final Set<Allergen> excludedAllergens;
  final String batchCookingLevel;
  final String varietyLevel;
  // 朝昼夜別の設定（プリセット or カスタム）
  final Map<String, MealSetting> mealSettings;
  // 栄養目標
  final NutrientTarget nutrientTarget;

  // Step1: お気に入り料理
  final List<Dish> favoriteDishes; // お気に入り料理の実データ
  final bool isLoadingFavorites;
  final bool guaranteeFavorites; // 確実に献立に入れる

  // Step2: 手持ち食材
  final Set<int> ownedIngredientIds;
  final Set<int> excludedIngredientIds; // 除外食材（嫌いな食材）
  final List<Map<String, dynamic>> ingredients; // APIから取得した基本食材リスト
  final bool isLoadingIngredients;
  final List<Map<String, dynamic>> searchResults;
  final String searchQuery;
  final bool isSearching;

  // Step3: 生成結果
  final MultiDayMenuPlan? generatedPlan;
  final bool isGenerating;
  final String? error;
  final Set<int> excludedDishIdsInStep3;
  // 進捗状態（SSE対応）
  final OptimizeProgress? currentProgress;

  const GenerateModalState({
    this.currentStep = 0,
    this.days = 3,
    this.people = 2,
    this.excludedAllergens = const {},
    this.batchCookingLevel = 'normal',
    this.varietyLevel = 'normal',
    this.mealSettings = const {
      'breakfast': MealSetting(enabled: true, preset: MealPreset.light),
      'lunch': MealSetting(enabled: true, preset: MealPreset.standard),
      'dinner': MealSetting(enabled: true, preset: MealPreset.full),
    },
    this.nutrientTarget = const NutrientTarget(),
    this.favoriteDishes = const [],
    this.isLoadingFavorites = false,
    this.guaranteeFavorites = false,
    this.ownedIngredientIds = const {},
    this.excludedIngredientIds = const {},
    this.ingredients = const [],
    this.isLoadingIngredients = false,
    this.searchResults = const [],
    this.searchQuery = '',
    this.isSearching = false,
    this.generatedPlan,
    this.isGenerating = false,
    this.error,
    this.excludedDishIdsInStep3 = const {},
    this.currentProgress,
  });

  GenerateModalState copyWith({
    int? currentStep,
    int? days,
    int? people,
    Set<Allergen>? excludedAllergens,
    String? batchCookingLevel,
    String? varietyLevel,
    Map<String, MealSetting>? mealSettings,
    NutrientTarget? nutrientTarget,
    List<Dish>? favoriteDishes,
    bool? isLoadingFavorites,
    bool? guaranteeFavorites,
    Set<int>? ownedIngredientIds,
    Set<int>? excludedIngredientIds,
    List<Map<String, dynamic>>? ingredients,
    bool? isLoadingIngredients,
    List<Map<String, dynamic>>? searchResults,
    String? searchQuery,
    bool? isSearching,
    MultiDayMenuPlan? generatedPlan,
    bool? isGenerating,
    String? error,
    Set<int>? excludedDishIdsInStep3,
    OptimizeProgress? currentProgress,
    bool clearPlan = false,
    bool clearError = false,
    bool clearProgress = false,
  }) {
    return GenerateModalState(
      currentStep: currentStep ?? this.currentStep,
      days: days ?? this.days,
      people: people ?? this.people,
      excludedAllergens: excludedAllergens ?? this.excludedAllergens,
      batchCookingLevel: batchCookingLevel ?? this.batchCookingLevel,
      varietyLevel: varietyLevel ?? this.varietyLevel,
      mealSettings: mealSettings ?? this.mealSettings,
      nutrientTarget: nutrientTarget ?? this.nutrientTarget,
      favoriteDishes: favoriteDishes ?? this.favoriteDishes,
      isLoadingFavorites: isLoadingFavorites ?? this.isLoadingFavorites,
      guaranteeFavorites: guaranteeFavorites ?? this.guaranteeFavorites,
      ownedIngredientIds: ownedIngredientIds ?? this.ownedIngredientIds,
      excludedIngredientIds: excludedIngredientIds ?? this.excludedIngredientIds,
      ingredients: ingredients ?? this.ingredients,
      isLoadingIngredients: isLoadingIngredients ?? this.isLoadingIngredients,
      searchResults: searchResults ?? this.searchResults,
      searchQuery: searchQuery ?? this.searchQuery,
      isSearching: isSearching ?? this.isSearching,
      generatedPlan: clearPlan ? null : (generatedPlan ?? this.generatedPlan),
      isGenerating: isGenerating ?? this.isGenerating,
      error: clearError ? null : (error ?? this.error),
      excludedDishIdsInStep3: excludedDishIdsInStep3 ?? this.excludedDishIdsInStep3,
      currentProgress: clearProgress ? null : (currentProgress ?? this.currentProgress),
    );
  }
}

/// 基本食材カテゴリのデータ（フィルタリング用）
const ingredientCategories = [
  {'name': '穀類', 'colorValue': 0xFFFFF3E0, 'textColorValue': 0xFFE65100},
  {'name': '野菜類', 'colorValue': 0xFFC8E6C9, 'textColorValue': 0xFF2E7D32},
  {'name': 'きのこ類', 'colorValue': 0xFFEFEBE9, 'textColorValue': 0xFF6D4C41},
  {'name': '豆類', 'colorValue': 0xFFD7CCC8, 'textColorValue': 0xFF5D4037},
  {'name': 'いも類', 'colorValue': 0xFFFBE9E7, 'textColorValue': 0xFFBF360C},
  {'name': '肉類', 'colorValue': 0xFFFFCCBC, 'textColorValue': 0xFFBF360C},
  {'name': '魚介類', 'colorValue': 0xFFB3E5FC, 'textColorValue': 0xFF01579B},
  {'name': '卵類', 'colorValue': 0xFFFFF9C4, 'textColorValue': 0xFFF57F17},
  {'name': '乳類', 'colorValue': 0xFFFFFDE7, 'textColorValue': 0xFFF57F17},
  {'name': '調味料', 'colorValue': 0xFFECEFF1, 'textColorValue': 0xFF455A64},
];

/// 献立生成モーダルのコントローラ
/// keepAlive: true で設定をキャッシュし、次回も引き継ぐ
@Riverpod(keepAlive: true)
class GenerateModalController extends _$GenerateModalController {
  /// 初回かどうか（設定画面のデフォルト値を適用するか判定用）
  bool _isInitialized = false;

  bool get isInitialized => _isInitialized;

  @override
  GenerateModalState build() => const GenerateModalState();

  /// 初期設定を読み込み（初回のみ）
  void initFromSettings({
    required int defaultDays,
    required int defaultPeople,
    required Set<Allergen> excludedAllergens,
    required Set<int> excludedIngredientIds,
    required String varietyLevel,
    required Map<String, MealSetting> mealSettings,
    required NutrientTarget nutrientTarget,
  }) {
    // 初回のみデフォルト設定を適用
    if (!_isInitialized) {
      state = state.copyWith(
        days: defaultDays,
        people: defaultPeople,
        excludedAllergens: excludedAllergens,
        excludedIngredientIds: excludedIngredientIds,
        varietyLevel: varietyLevel,
        mealSettings: mealSettings,
        nutrientTarget: nutrientTarget,
      );
      _isInitialized = true;
    } else {
      // 初期化済みでも除外食材は常に最新を反映
      state = state.copyWith(excludedIngredientIds: excludedIngredientIds);
    }
  }

  /// モーダルを閉じる時に呼ぶ（生成結果のみクリアし、設定は保持）
  void resetForNextSession() {
    state = state.copyWith(
      currentStep: 0,
      generatedPlan: null,
      clearPlan: true,
      error: null,
      clearError: true,
      excludedDishIdsInStep3: {},
      isGenerating: false,
      clearProgress: true,
    );
  }

  /// キャッシュをクリアして設定画面のデフォルト値に戻す
  void resetToDefaults({
    required int defaultDays,
    required int defaultPeople,
    required Set<Allergen> excludedAllergens,
    required Set<int> excludedIngredientIds,
    required String varietyLevel,
    required Map<String, MealSetting> mealSettings,
    required NutrientTarget nutrientTarget,
  }) {
    // キャッシュ状態をリセット
    _isInitialized = false;

    // デフォルト値で状態を再初期化
    state = GenerateModalState(
      days: defaultDays,
      people: defaultPeople,
      excludedAllergens: excludedAllergens,
      excludedIngredientIds: excludedIngredientIds,
      varietyLevel: varietyLevel,
      mealSettings: mealSettings,
      nutrientTarget: nutrientTarget,
    );

    // 再度初期化済みにマーク
    _isInitialized = true;
  }

  // === Step Navigation ===
  void nextStep() {
    if (state.currentStep < 3) {
      state = state.copyWith(currentStep: state.currentStep + 1);
      if (state.currentStep == 3) {
        generatePlan();
      }
    }
  }

  void previousStep() {
    if (state.currentStep > 0) {
      state = state.copyWith(currentStep: state.currentStep - 1);
    }
  }

  void goToStep(int step) {
    state = state.copyWith(currentStep: step.clamp(0, 3));
  }

  // === Step1: お気に入り料理 ===

  /// お気に入り料理を読み込み
  Future<void> loadFavoriteDishes(Set<int> favoriteIds) async {
    if (favoriteIds.isEmpty) {
      state = state.copyWith(favoriteDishes: [], isLoadingFavorites: false);
      return;
    }

    state = state.copyWith(isLoadingFavorites: true);

    try {
      final apiService = ApiService();
      final dishes = <Dish>[];

      for (final id in favoriteIds) {
        try {
          final dish = await apiService.getDish(id);
          dishes.add(dish);
        } catch (e) {
          debugPrint('料理 $id の読み込み失敗: $e');
        }
      }

      state = state.copyWith(
        favoriteDishes: dishes,
        isLoadingFavorites: false,
      );
    } catch (e) {
      debugPrint('お気に入り料理の読み込みに失敗: $e');
      state = state.copyWith(isLoadingFavorites: false);
    }
  }

  /// 確実に献立に入れるオプションを切り替え
  void setGuaranteeFavorites(bool value) {
    state = state.copyWith(guaranteeFavorites: value);
  }

  // === Step1: Basic Settings ===
  void setDays(int days) {
    state = state.copyWith(days: days.clamp(1, 7));
  }

  void setPeople(int people) {
    state = state.copyWith(people: people.clamp(1, 6));
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

  void setBatchCookingLevel(String level) {
    state = state.copyWith(batchCookingLevel: level);
  }

  void setVarietyLevel(String level) {
    state = state.copyWith(varietyLevel: level);
  }

  // === 栄養目標設定 ===
  void setCaloriesRange(double min, double max) {
    state = state.copyWith(
      nutrientTarget: state.nutrientTarget.copyWith(
        caloriesMin: min,
        caloriesMax: max,
      ),
    );
  }

  void setProteinRange(double min, double max) {
    state = state.copyWith(
      nutrientTarget: state.nutrientTarget.copyWith(
        proteinMin: min,
        proteinMax: max,
      ),
    );
  }

  // === 朝昼夜別設定 ===
  void setMealEnabled(String mealType, bool enabled) {
    final current = Map<String, MealSetting>.from(state.mealSettings);
    final currentSetting = current[mealType] ?? const MealSetting();
    current[mealType] = currentSetting.copyWith(enabled: enabled);
    state = state.copyWith(mealSettings: current);
  }

  void setMealPreset(String mealType, MealPreset preset) {
    final current = Map<String, MealSetting>.from(state.mealSettings);
    final currentSetting = current[mealType] ?? const MealSetting();
    current[mealType] = currentSetting.copyWith(
      preset: preset,
      // プリセット変更時はカスタム設定をクリア（customの場合を除く）
      customCategories: preset == MealPreset.custom ? currentSetting.customCategories : null,
    );
    state = state.copyWith(mealSettings: current);
  }

  void setMealCategoryConstraint(
    String mealType,
    String category,
    int min,
    int max,
  ) {
    final current = Map<String, MealSetting>.from(state.mealSettings);
    final currentSetting = current[mealType] ?? const MealSetting();

    // カスタムモードに切り替え
    var customCategories = currentSetting.customCategories ??
        mealPresets[currentSetting.preset] ??
        const MealCategoryConstraints();

    final constraint = CategoryConstraint(min: min, max: max);
    switch (category) {
      case '主食':
        customCategories = customCategories.copyWith(staple: constraint);
        break;
      case '主菜':
        customCategories = customCategories.copyWith(main: constraint);
        break;
      case '副菜':
        customCategories = customCategories.copyWith(side: constraint);
        break;
      case '汁物':
        customCategories = customCategories.copyWith(soup: constraint);
        break;
      case 'デザート':
        customCategories = customCategories.copyWith(dessert: constraint);
        break;
    }

    current[mealType] = currentSetting.copyWith(
      preset: MealPreset.custom,
      customCategories: customCategories,
    );
    state = state.copyWith(mealSettings: current);
  }

  // === Step2: Owned Ingredients ===

  /// APIから基本食材一覧を読み込み
  Future<void> loadIngredients() async {
    if (state.ingredients.isNotEmpty || state.isLoadingIngredients) {
      return; // 既に読み込み済みまたは読み込み中
    }

    state = state.copyWith(isLoadingIngredients: true);

    try {
      final repo = ref.read(foodRepositoryProvider);
      final ingredients = await repo.getIngredients();
      state = state.copyWith(
        ingredients: ingredients,
        isLoadingIngredients: false,
      );
    } catch (e) {
      debugPrint('基本食材の読み込みに失敗: $e');
      state = state.copyWith(isLoadingIngredients: false);
    }
  }

  void toggleIngredient(int ingredientId) {
    final current = Set<int>.from(state.ownedIngredientIds);
    if (current.contains(ingredientId)) {
      current.remove(ingredientId);
    } else {
      current.add(ingredientId);
    }
    state = state.copyWith(ownedIngredientIds: current);
  }

  void clearOwnedIngredients() {
    state = state.copyWith(ownedIngredientIds: {});
  }

  /// 基本食材をローカル検索（API不要）
  void searchIngredients(String query) {
    if (query.isEmpty) {
      state = state.copyWith(searchResults: [], searchQuery: '');
      return;
    }

    state = state.copyWith(searchQuery: query);

    // ローカルの ingredients リストから検索
    final lowerQuery = query.toLowerCase();
    final results = state.ingredients
        .where((ing) => (ing['name'] as String? ?? '').toLowerCase().contains(lowerQuery))
        .toList();

    state = state.copyWith(searchResults: results);
  }

  void clearSearch() {
    state = state.copyWith(searchResults: [], searchQuery: '');
  }

  // === Step3: Plan Generation ===
  void toggleDishExclusion(int dishId) {
    final current = Set<int>.from(state.excludedDishIdsInStep3);
    if (current.contains(dishId)) {
      current.remove(dishId);
    } else {
      current.add(dishId);
    }
    state = state.copyWith(excludedDishIdsInStep3: current);
  }

  Future<void> generatePlan({List<int>? preferredDishIds}) async {
    // SSE対応のgeneratePlanWithProgressを使用
    await generatePlanWithProgress(preferredDishIds: preferredDishIds);
  }

  /// SSEストリームを使用して進捗付きで献立を生成
  Future<void> generatePlanWithProgress({List<int>? preferredDishIds}) async {
    state = state.copyWith(
      isGenerating: true,
      clearError: true,
      excludedDishIdsInStep3: {},
      currentProgress: OptimizeProgress.initial,
    );

    try {
      final apiService = ApiService();

      // お気に入り料理のID
      final favoriteIds = state.favoriteDishes.map((d) => d.id).toList();

      // SSEストリームを購読
      await for (final event in apiService.optimizeMultiDayWithProgress(
        days: state.days,
        people: state.people,
        target: state.nutrientTarget,
        excludedAllergens: state.excludedAllergens.toList(),
        keepDishIds: state.guaranteeFavorites ? favoriteIds : [],
        preferredIngredientIds: state.ownedIngredientIds.toList(),
        preferredDishIds: preferredDishIds ?? favoriteIds,
        excludedIngredientIds: state.excludedIngredientIds.toList(),
        batchCookingLevel: state.batchCookingLevel,
        varietyLevel: state.varietyLevel,
        mealSettings: state.mealSettings,
      )) {
        switch (event) {
          case OptimizeProgressStreamEvent(:final progress):
            state = state.copyWith(currentProgress: progress);
          case OptimizeResultStreamEvent(:final plan):
            state = state.copyWith(
              generatedPlan: plan,
              isGenerating: false,
              currentProgress: OptimizeProgress.completed,
            );
          case OptimizeErrorStreamEvent(:final message):
            state = state.copyWith(
              error: message,
              isGenerating: false,
              clearProgress: true,
            );
        }
      }
    } catch (e) {
      state = state.copyWith(
        error: e.toString(),
        isGenerating: false,
        clearProgress: true,
      );
    }
  }

  Future<void> regeneratePlan() async {
    state = state.copyWith(
      isGenerating: true,
      clearError: true,
      currentProgress: OptimizeProgress.initial,
    );

    try {
      final apiService = ApiService();

      // お気に入り料理のID
      final favoriteIds = state.favoriteDishes.map((d) => d.id).toList();

      // SSEストリームを購読（除外料理IDを追加）
      await for (final event in apiService.optimizeMultiDayWithProgress(
        days: state.days,
        people: state.people,
        target: state.nutrientTarget,
        excludedAllergens: state.excludedAllergens.toList(),
        excludedDishIds: state.excludedDishIdsInStep3.toList(),
        keepDishIds: state.guaranteeFavorites ? favoriteIds : [],
        preferredIngredientIds: state.ownedIngredientIds.toList(),
        preferredDishIds: favoriteIds,
        excludedIngredientIds: state.excludedIngredientIds.toList(),
        batchCookingLevel: state.batchCookingLevel,
        varietyLevel: state.varietyLevel,
        mealSettings: state.mealSettings,
      )) {
        switch (event) {
          case OptimizeProgressStreamEvent(:final progress):
            state = state.copyWith(currentProgress: progress);
          case OptimizeResultStreamEvent(:final plan):
            state = state.copyWith(
              generatedPlan: plan,
              isGenerating: false,
              excludedDishIdsInStep3: {},
              currentProgress: OptimizeProgress.completed,
            );
          case OptimizeErrorStreamEvent(:final message):
            state = state.copyWith(
              error: message,
              isGenerating: false,
              clearProgress: true,
            );
        }
      }
    } catch (e) {
      state = state.copyWith(
        error: e.toString(),
        isGenerating: false,
        clearProgress: true,
      );
    }
  }
}
