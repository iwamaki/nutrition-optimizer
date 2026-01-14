import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../../domain/entities/menu_plan.dart';
import '../../../domain/entities/settings.dart';
import '../../../data/repositories/menu_repository_impl.dart';
import '../../../data/repositories/food_repository_impl.dart';

part 'generate_modal_controller.g.dart';

/// 献立生成モーダルの状態
class GenerateModalState {
  // 現在のステップ
  final int currentStep;

  // Step1: 基本設定
  final int days;
  final int people;
  final Set<Allergen> excludedAllergens;
  final String batchCookingLevel;
  final String volumeLevel;
  final String varietyLevel;

  // Step2: 手持ち食材
  final Set<int> ownedFoodIds;
  final List<Map<String, dynamic>> searchResults;
  final String searchQuery;
  final bool isSearching;

  // Step3: 生成結果
  final MultiDayMenuPlan? generatedPlan;
  final bool isGenerating;
  final String? error;
  final Set<int> excludedDishIdsInStep3;

  const GenerateModalState({
    this.currentStep = 0,
    this.days = 3,
    this.people = 2,
    this.excludedAllergens = const {},
    this.batchCookingLevel = 'normal',
    this.volumeLevel = 'normal',
    this.varietyLevel = 'normal',
    this.ownedFoodIds = const {},
    this.searchResults = const [],
    this.searchQuery = '',
    this.isSearching = false,
    this.generatedPlan,
    this.isGenerating = false,
    this.error,
    this.excludedDishIdsInStep3 = const {},
  });

  GenerateModalState copyWith({
    int? currentStep,
    int? days,
    int? people,
    Set<Allergen>? excludedAllergens,
    String? batchCookingLevel,
    String? volumeLevel,
    String? varietyLevel,
    Set<int>? ownedFoodIds,
    List<Map<String, dynamic>>? searchResults,
    String? searchQuery,
    bool? isSearching,
    MultiDayMenuPlan? generatedPlan,
    bool? isGenerating,
    String? error,
    Set<int>? excludedDishIdsInStep3,
    bool clearPlan = false,
    bool clearError = false,
  }) {
    return GenerateModalState(
      currentStep: currentStep ?? this.currentStep,
      days: days ?? this.days,
      people: people ?? this.people,
      excludedAllergens: excludedAllergens ?? this.excludedAllergens,
      batchCookingLevel: batchCookingLevel ?? this.batchCookingLevel,
      volumeLevel: volumeLevel ?? this.volumeLevel,
      varietyLevel: varietyLevel ?? this.varietyLevel,
      ownedFoodIds: ownedFoodIds ?? this.ownedFoodIds,
      searchResults: searchResults ?? this.searchResults,
      searchQuery: searchQuery ?? this.searchQuery,
      isSearching: isSearching ?? this.isSearching,
      generatedPlan: clearPlan ? null : (generatedPlan ?? this.generatedPlan),
      isGenerating: isGenerating ?? this.isGenerating,
      error: clearError ? null : (error ?? this.error),
      excludedDishIdsInStep3: excludedDishIdsInStep3 ?? this.excludedDishIdsInStep3,
    );
  }
}

/// よく使う食材のデータ
const frequentFoods = [
  {'id': 1, 'name': '卵', 'emoji': '🥚'},
  {'id': 2, 'name': '玉ねぎ', 'emoji': '🧅'},
  {'id': 3, 'name': 'にんじん', 'emoji': '🥕'},
  {'id': 4, 'name': '豚肉', 'emoji': '🍖'},
  {'id': 5, 'name': '鶏肉', 'emoji': '🐔'},
  {'id': 6, 'name': '牛乳', 'emoji': '🥛'},
  {'id': 7, 'name': 'キャベツ', 'emoji': '🥬'},
  {'id': 8, 'name': '豆腐', 'emoji': '🧈'},
];

/// 食品カテゴリのデータ
const foodCategories = [
  {'name': '肉類', 'colorValue': 0xFFFFCCBC, 'textColorValue': 0xFFBF360C},
  {'name': '魚介類', 'colorValue': 0xFFB3E5FC, 'textColorValue': 0xFF01579B},
  {'name': '野菜類', 'colorValue': 0xFFC8E6C9, 'textColorValue': 0xFF2E7D32},
  {'name': '卵類', 'colorValue': 0xFFFFF9C4, 'textColorValue': 0xFFF57F17},
];

/// 献立生成モーダルのコントローラ
@riverpod
class GenerateModalController extends _$GenerateModalController {
  @override
  GenerateModalState build() => const GenerateModalState();

  /// 初期設定を読み込み
  void initFromSettings({
    required int defaultDays,
    required int defaultPeople,
    required Set<Allergen> excludedAllergens,
  }) {
    state = state.copyWith(
      days: defaultDays,
      people: defaultPeople,
      excludedAllergens: excludedAllergens,
    );
  }

  // === Step Navigation ===
  void nextStep() {
    if (state.currentStep < 2) {
      state = state.copyWith(currentStep: state.currentStep + 1);
      if (state.currentStep == 2) {
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
    state = state.copyWith(currentStep: step.clamp(0, 2));
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

  void setVolumeLevel(String level) {
    state = state.copyWith(volumeLevel: level);
  }

  void setVarietyLevel(String level) {
    state = state.copyWith(varietyLevel: level);
  }

  // === Step2: Owned Foods ===
  void toggleFood(int foodId) {
    final current = Set<int>.from(state.ownedFoodIds);
    if (current.contains(foodId)) {
      current.remove(foodId);
    } else {
      current.add(foodId);
    }
    state = state.copyWith(ownedFoodIds: current);
  }

  void clearOwnedFoods() {
    state = state.copyWith(ownedFoodIds: {});
  }

  Future<void> searchFoods(String query) async {
    if (query.length < 2) {
      state = state.copyWith(searchResults: [], searchQuery: query);
      return;
    }

    state = state.copyWith(isSearching: true, searchQuery: query);

    try {
      final repo = ref.read(foodRepositoryProvider);
      final results = await repo.searchFoods(query: query, limit: 10);
      state = state.copyWith(searchResults: results, isSearching: false);
    } catch (e) {
      state = state.copyWith(searchResults: [], isSearching: false);
    }
  }

  Future<void> searchFoodsByCategory(String category) async {
    state = state.copyWith(isSearching: true, searchQuery: category);

    try {
      final repo = ref.read(foodRepositoryProvider);
      final results = await repo.searchFoods(category: category, limit: 20);
      state = state.copyWith(searchResults: results, isSearching: false);
    } catch (e) {
      state = state.copyWith(searchResults: [], isSearching: false);
    }
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

  Future<void> generatePlan({NutrientTarget? target}) async {
    state = state.copyWith(
      isGenerating: true,
      clearError: true,
      excludedDishIdsInStep3: {},
    );

    try {
      final repo = ref.read(menuRepositoryProvider);
      final plan = await repo.generateMultiDayPlan(
        days: state.days,
        people: state.people,
        target: target,
        excludedAllergens: state.excludedAllergens.toList(),
        batchCookingLevel: state.batchCookingLevel,
        volumeLevel: state.volumeLevel,
        varietyLevel: state.varietyLevel,
      );
      state = state.copyWith(generatedPlan: plan, isGenerating: false);
    } catch (e) {
      state = state.copyWith(error: e.toString(), isGenerating: false);
    }
  }

  Future<void> regeneratePlan({NutrientTarget? target}) async {
    state = state.copyWith(isGenerating: true, clearError: true);

    try {
      final repo = ref.read(menuRepositoryProvider);
      final plan = await repo.refineMultiDayPlan(
        days: state.days,
        people: state.people,
        target: target,
        excludeDishIds: state.excludedDishIdsInStep3.toList(),
        excludedAllergens: state.excludedAllergens.toList(),
        batchCookingLevel: state.batchCookingLevel,
        volumeLevel: state.volumeLevel,
        varietyLevel: state.varietyLevel,
      );
      state = state.copyWith(
        generatedPlan: plan,
        isGenerating: false,
        excludedDishIdsInStep3: {},
      );
    } catch (e) {
      state = state.copyWith(error: e.toString(), isGenerating: false);
    }
  }
}
