import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/menu_provider.dart';
import '../providers/settings_provider.dart';
import '../providers/shopping_provider.dart';
import '../models/dish.dart';
import '../models/settings.dart';
import '../models/menu_plan.dart';
import '../services/api_service.dart';
import '../widgets/nutrient_progress_bar.dart';

/// 献立生成モーダル（3ステップウィザード）
class GenerateModal extends StatefulWidget {
  const GenerateModal({super.key});

  @override
  State<GenerateModal> createState() => _GenerateModalState();
}

class _GenerateModalState extends State<GenerateModal> {
  int _currentStep = 0;
  final ApiService _apiService = ApiService();

  // Step1: 設定
  late int _days;
  late int _people;
  late Set<Allergen> _excludedAllergens;
  late bool _preferBatchCooking;

  // Step2: 手持ち食材
  Set<int> _ownedFoodIds = {};
  List<Map<String, dynamic>> _searchResults = [];
  String _searchQuery = '';
  bool _isSearching = false;
  final TextEditingController _searchController = TextEditingController();

  // よく使う食材（ハードコードだが将来的にはユーザー履歴から）
  final List<Map<String, dynamic>> _frequentFoods = [
    {'id': 1, 'name': '卵', 'emoji': '🥚'},
    {'id': 2, 'name': '玉ねぎ', 'emoji': '🧅'},
    {'id': 3, 'name': 'にんじん', 'emoji': '🥕'},
    {'id': 4, 'name': '豚肉', 'emoji': '🍖'},
    {'id': 5, 'name': '鶏肉', 'emoji': '🐔'},
    {'id': 6, 'name': '牛乳', 'emoji': '🥛'},
    {'id': 7, 'name': 'キャベツ', 'emoji': '🥬'},
    {'id': 8, 'name': '豆腐', 'emoji': '🧈'},
  ];

  // 食品カテゴリ
  final List<Map<String, dynamic>> _foodCategories = [
    {'name': '肉類', 'color': const Color(0xFFFFCCBC), 'textColor': const Color(0xFFBF360C)},
    {'name': '魚介類', 'color': const Color(0xFFB3E5FC), 'textColor': const Color(0xFF01579B)},
    {'name': '野菜類', 'color': const Color(0xFFC8E6C9), 'textColor': const Color(0xFF2E7D32)},
    {'name': '卵類', 'color': const Color(0xFFFFF9C4), 'textColor': const Color(0xFFF57F17)},
  ];

  // Step3: 生成結果
  MultiDayMenuPlan? _generatedPlan;
  bool _isGenerating = false;
  String? _error;
  Set<int> _excludedDishIdsInStep3 = {};

  @override
  void initState() {
    super.initState();
    final settings = context.read<SettingsProvider>();
    _days = settings.defaultDays;
    _people = settings.defaultPeople;
    _excludedAllergens = Set.from(settings.excludedAllergens);
    _preferBatchCooking = settings.preferBatchCooking;
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.9,
      minChildSize: 0.5,
      maxChildSize: 0.95,
      expand: false,
      builder: (context, scrollController) {
        return Container(
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.surface,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
          ),
          child: Column(
            children: [
              // ヘッダー
              _buildHeader(context),
              // ステップインジケーター
              _buildStepIndicator(),
              const Divider(height: 1),
              // コンテンツ
              Expanded(
                child: _buildStepContent(scrollController),
              ),
              // フッター
              _buildFooter(context),
            ],
          ),
        );
      },
    );
  }

  Widget _buildHeader(BuildContext context) {
    final titles = ['基本設定', '手持ち食材', '献立確認'];
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.primary,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
      ),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.close),
            color: Theme.of(context).colorScheme.onPrimary,
            onPressed: () => Navigator.pop(context),
          ),
          Expanded(
            child: Text(
              '献立を生成 - ${titles[_currentStep]}',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onPrimary,
                  ),
              textAlign: TextAlign.center,
            ),
          ),
          const SizedBox(width: 48), // バランス用
        ],
      ),
    );
  }

  Widget _buildStepIndicator() {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          _buildStepDot(0, '基本設定'),
          _buildStepLine(0),
          _buildStepDot(1, '食材'),
          _buildStepLine(1),
          _buildStepDot(2, '確認'),
        ],
      ),
    );
  }

  Widget _buildStepDot(int step, String label) {
    final isActive = _currentStep >= step;
    final isCurrent = _currentStep == step;
    final colorScheme = Theme.of(context).colorScheme;

    return Column(
      children: [
        Container(
          width: 32,
          height: 32,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: isActive ? colorScheme.primary : colorScheme.surfaceContainerHighest,
            border: isCurrent
                ? Border.all(color: colorScheme.primary, width: 2)
                : null,
          ),
          child: Center(
            child: isActive
                ? Icon(
                    step < _currentStep ? Icons.check : Icons.circle,
                    size: 16,
                    color: colorScheme.onPrimary,
                  )
                : Text(
                    '${step + 1}',
                    style: TextStyle(color: colorScheme.outline),
                  ),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: TextStyle(
            fontSize: 10,
            color: isActive ? colorScheme.primary : colorScheme.outline,
          ),
        ),
      ],
    );
  }

  Widget _buildStepLine(int afterStep) {
    final isActive = _currentStep > afterStep;
    return Container(
      width: 40,
      height: 2,
      margin: const EdgeInsets.only(bottom: 16),
      color: isActive
          ? Theme.of(context).colorScheme.primary
          : Theme.of(context).colorScheme.outline.withValues(alpha: 0.3),
    );
  }

  Widget _buildStepContent(ScrollController scrollController) {
    switch (_currentStep) {
      case 0:
        return _buildStep1Settings(scrollController);
      case 1:
        return _buildStep2Ingredients(scrollController);
      case 2:
        return _buildStep3Confirm(scrollController);
      default:
        return const SizedBox.shrink();
    }
  }

  // ========== Step 1: 基本設定 ==========
  Widget _buildStep1Settings(ScrollController scrollController) {
    return ListView(
      controller: scrollController,
      padding: const EdgeInsets.all(16),
      children: [
        // 期間設定
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.calendar_today, size: 20),
                    const SizedBox(width: 8),
                    Text('期間', style: Theme.of(context).textTheme.titleSmall),
                  ],
                ),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    _buildPeriodChip(1, '1日'),
                    _buildPeriodChip(3, '3日'),
                    _buildPeriodChip(7, '1週間'),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  '$_days日分の献立を生成',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Theme.of(context).colorScheme.outline,
                      ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),

        // 人数設定
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.people, size: 20),
                    const SizedBox(width: 8),
                    Text('人数', style: Theme.of(context).textTheme.titleSmall),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Container(
                      decoration: BoxDecoration(
                        color: Theme.of(context).colorScheme.surfaceContainerHighest,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          IconButton(
                            icon: const Icon(Icons.remove),
                            onPressed: _people > 1
                                ? () => setState(() => _people--)
                                : null,
                          ),
                          SizedBox(
                            width: 48,
                            child: Text(
                              '$_people人',
                              textAlign: TextAlign.center,
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.add),
                            onPressed: _people < 6
                                ? () => setState(() => _people++)
                                : null,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),

        // アレルゲン除外
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.warning_amber, size: 20),
                    const SizedBox(width: 8),
                    Text('アレルゲン除外', style: Theme.of(context).textTheme.titleSmall),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  '選択したアレルゲンを含む料理を除外します',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Theme.of(context).colorScheme.outline,
                      ),
                ),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: Allergen.values.map((allergen) {
                    final isSelected = _excludedAllergens.contains(allergen);
                    return FilterChip(
                      label: Text(allergen.displayName),
                      selected: isSelected,
                      selectedColor: Colors.red.shade100,
                      checkmarkColor: Colors.red.shade700,
                      onSelected: (_) {
                        setState(() {
                          if (isSelected) {
                            _excludedAllergens.remove(allergen);
                          } else {
                            _excludedAllergens.add(allergen);
                          }
                        });
                      },
                    );
                  }).toList(),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),

        // 作り置き優先
        Card(
          child: SwitchListTile(
            secondary: const Icon(Icons.kitchen),
            title: const Text('作り置き優先'),
            subtitle: const Text('調理回数を減らして効率化'),
            value: _preferBatchCooking,
            onChanged: (value) => setState(() => _preferBatchCooking = value),
          ),
        ),
      ],
    );
  }

  Widget _buildPeriodChip(int days, String label) {
    final isSelected = _days == days;
    return ChoiceChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (_) => setState(() => _days = days),
    );
  }

  // ========== Step 2: 手持ち食材 ==========
  Widget _buildStep2Ingredients(ScrollController scrollController) {
    return ListView(
      controller: scrollController,
      padding: const EdgeInsets.all(16),
      children: [
        // 説明カード
        Card(
          color: const Color(0xFFE8F5E9),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                const Icon(Icons.home, color: Color(0xFF2E7D32)),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '家にある食材を選択',
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                              color: const Color(0xFF2E7D32),
                            ),
                      ),
                      Text(
                        '→ 買い物リストから除外されます',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Theme.of(context).colorScheme.outline,
                            ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),

        // 検索バー
        TextField(
          controller: _searchController,
          decoration: InputDecoration(
            hintText: '🔍 食材を検索...',
            filled: true,
            fillColor: Theme.of(context).colorScheme.surfaceContainerHighest,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(24),
              borderSide: BorderSide.none,
            ),
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            suffixIcon: _searchQuery.isNotEmpty
                ? IconButton(
                    icon: const Icon(Icons.clear),
                    onPressed: () {
                      _searchController.clear();
                      setState(() {
                        _searchQuery = '';
                        _searchResults = [];
                      });
                    },
                  )
                : null,
          ),
          onChanged: (value) {
            setState(() {
              _searchQuery = value;
            });
            if (value.length >= 2) {
              _searchFoods(value);
            } else {
              setState(() {
                _searchResults = [];
              });
            }
          },
        ),
        const SizedBox(height: 16),

        // 検索結果
        if (_isSearching)
          const Center(child: CircularProgressIndicator())
        else if (_searchResults.isNotEmpty) ...[
          Text(
            '検索結果',
            style: Theme.of(context).textTheme.titleSmall,
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _searchResults.map((food) {
              final isSelected = _ownedFoodIds.contains(food['id']);
              return FilterChip(
                label: Text(food['name'] ?? ''),
                selected: isSelected,
                selectedColor: const Color(0xFFE8F5E9),
                onSelected: (_) => _toggleFood(food['id'] as int),
              );
            }).toList(),
          ),
          const SizedBox(height: 16),
        ],

        // よく使う食材
        Text(
          '⭐ よく使う',
          style: Theme.of(context).textTheme.titleSmall,
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: _frequentFoods.map((food) {
            final isSelected = _ownedFoodIds.contains(food['id']);
            return FilterChip(
              label: Text('${food['emoji']}${food['name']}'),
              selected: isSelected,
              selectedColor: const Color(0xFFE8F5E9),
              onSelected: (_) => _toggleFood(food['id'] as int),
            );
          }).toList(),
        ),
        const SizedBox(height: 16),

        // カテゴリから探す
        Text(
          '📁 カテゴリから探す',
          style: Theme.of(context).textTheme.titleSmall,
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: _foodCategories.map((cat) {
            return ActionChip(
              label: Text(cat['name'] as String),
              backgroundColor: cat['color'] as Color,
              labelStyle: TextStyle(color: cat['textColor'] as Color),
              onPressed: () => _searchFoodsByCategory(cat['name'] as String),
            );
          }).toList(),
        ),
        const SizedBox(height: 16),

        // 選択中の食材
        if (_ownedFoodIds.isNotEmpty)
          Card(
            color: const Color(0xFFE8F5E9),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  const Icon(Icons.check, color: Color(0xFF2E7D32), size: 20),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '選択中: ${_ownedFoodIds.length}品目',
                      style: TextStyle(color: const Color(0xFF2E7D32)),
                    ),
                  ),
                  TextButton(
                    onPressed: () => setState(() => _ownedFoodIds = {}),
                    child: const Text('クリア'),
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }

  void _toggleFood(int foodId) {
    setState(() {
      if (_ownedFoodIds.contains(foodId)) {
        _ownedFoodIds.remove(foodId);
      } else {
        _ownedFoodIds.add(foodId);
      }
    });
  }

  Future<void> _searchFoods(String query) async {
    setState(() => _isSearching = true);
    try {
      final results = await _apiService.searchFoods(query: query, limit: 10);
      setState(() {
        _searchResults = results;
      });
    } catch (e) {
      // エラーは無視（検索結果なしとして表示）
    } finally {
      setState(() => _isSearching = false);
    }
  }

  Future<void> _searchFoodsByCategory(String category) async {
    setState(() => _isSearching = true);
    try {
      final results = await _apiService.searchFoods(category: category, limit: 20);
      setState(() {
        _searchResults = results;
        _searchQuery = category;
        _searchController.text = category;
      });
    } catch (e) {
      // エラーは無視
    } finally {
      setState(() => _isSearching = false);
    }
  }

  // ========== Step 3: 献立確認 ==========
  Widget _buildStep3Confirm(ScrollController scrollController) {
    if (_isGenerating) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('献立を生成中...'),
          ],
        ),
      );
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            const Text('エラーが発生しました'),
            const SizedBox(height: 8),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32),
              child: Text(
                _error!,
                textAlign: TextAlign.center,
                style: TextStyle(color: Theme.of(context).colorScheme.outline),
              ),
            ),
            const SizedBox(height: 24),
            FilledButton.tonal(
              onPressed: _generatePlan,
              child: const Text('再試行'),
            ),
          ],
        ),
      );
    }

    if (_generatedPlan == null) {
      return const Center(child: Text('献立を生成してください'));
    }

    final plan = _generatedPlan!;
    return ListView(
      controller: scrollController,
      padding: const EdgeInsets.all(16),
      children: [
        // 説明カード
        Card(
          color: const Color(0xFFE8F5E9),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Text(
              '不要な料理をタップで除外',
              textAlign: TextAlign.center,
              style: TextStyle(color: const Color(0xFF2E7D32)),
            ),
          ),
        ),
        const SizedBox(height: 16),

        // 栄養達成率サマリー
        _buildAchievementCard(plan),
        const SizedBox(height: 16),

        // 料理リスト（除外可能）
        _buildDishList(plan),

        // 警告
        if (plan.warnings.isNotEmpty) ...[
          const SizedBox(height: 16),
          _buildWarningsCard(plan.warnings),
        ],
        const SizedBox(height: 16),
      ],
    );
  }

  Widget _buildAchievementCard(MultiDayMenuPlan plan) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '${plan.days}日間の栄養達成率',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  decoration: BoxDecoration(
                    color: _getAchievementColor(plan.averageAchievement)
                        .withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Text(
                    '${plan.averageAchievement.toInt()}%',
                    style: TextStyle(
                      color: _getAchievementColor(plan.averageAchievement),
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            NutrientProgressBar(
              label: 'カロリー',
              value: plan.overallAchievement['calories'] ?? 0,
              color: Colors.orange,
            ),
            const SizedBox(height: 8),
            NutrientProgressBar(
              label: 'タンパク質',
              value: plan.overallAchievement['protein'] ?? 0,
              color: Colors.red,
            ),
            const SizedBox(height: 8),
            NutrientProgressBar(
              label: '食物繊維',
              value: plan.overallAchievement['fiber'] ?? 0,
              color: Colors.green,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDishList(MultiDayMenuPlan plan) {
    // 全ての料理をフラットに展開
    final allDishes = <_DishEntry>[];
    for (final dayPlan in plan.dailyPlans) {
      for (final portion in dayPlan.breakfast) {
        allDishes.add(_DishEntry(
          portion: portion,
          day: dayPlan.day,
          mealType: '朝食',
        ));
      }
      for (final portion in dayPlan.lunch) {
        allDishes.add(_DishEntry(
          portion: portion,
          day: dayPlan.day,
          mealType: '昼食',
        ));
      }
      for (final portion in dayPlan.dinner) {
        allDishes.add(_DishEntry(
          portion: portion,
          day: dayPlan.day,
          mealType: '夕食',
        ));
      }
    }

    // 重複を除去（同じ料理IDは1回だけ表示）
    final seenIds = <int>{};
    final uniqueDishes = allDishes.where((entry) {
      if (seenIds.contains(entry.portion.dish.id)) {
        return false;
      }
      seenIds.add(entry.portion.dish.id);
      return true;
    }).toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '生成された料理 (${uniqueDishes.length}品)',
          style: Theme.of(context).textTheme.titleSmall,
        ),
        const SizedBox(height: 8),
        ...uniqueDishes.map((entry) {
          final isExcluded = _excludedDishIdsInStep3.contains(entry.portion.dish.id);
          return _buildDishCard(entry, isExcluded);
        }),
      ],
    );
  }

  Widget _buildDishCard(_DishEntry entry, bool isExcluded) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      color: isExcluded ? Colors.red.shade50 : null,
      child: InkWell(
        onTap: () {
          setState(() {
            if (isExcluded) {
              _excludedDishIdsInStep3.remove(entry.portion.dish.id);
            } else {
              _excludedDishIdsInStep3.add(entry.portion.dish.id);
            }
          });
        },
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      entry.portion.dish.name,
                      style: TextStyle(
                        decoration: isExcluded ? TextDecoration.lineThrough : null,
                        color: isExcluded ? Colors.grey : null,
                      ),
                    ),
                    Text(
                      '${entry.portion.dish.categoryDisplay} ・ ${entry.mealType}',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: isExcluded
                                ? Colors.grey
                                : Theme.of(context).colorScheme.outline,
                          ),
                    ),
                  ],
                ),
              ),
              if (isExcluded)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.red.shade100,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    '除外',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.red.shade700,
                    ),
                  ),
                )
              else
                Icon(
                  Icons.check_circle_outline,
                  color: Theme.of(context).colorScheme.primary,
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildWarningsCard(List<NutrientWarning> warnings) {
    return Card(
      color: Colors.orange.shade50,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.warning_amber, color: Colors.orange.shade700),
                const SizedBox(width: 8),
                Text(
                  '栄養バランスの警告',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Colors.orange.shade700,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            ...warnings.map((w) => Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(
                    '・${w.message}',
                    style: TextStyle(color: Colors.orange.shade900),
                  ),
                )),
          ],
        ),
      ),
    );
  }

  Color _getAchievementColor(double value) {
    if (value >= 90) return Colors.green;
    if (value >= 70) return Colors.orange;
    return Colors.red;
  }

  Widget _buildFooter(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.1),
            blurRadius: 4,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Row(
        children: [
          if (_currentStep > 0)
            Expanded(
              child: OutlinedButton(
                onPressed: () => setState(() => _currentStep--),
                child: const Text('← 戻る'),
              ),
            ),
          if (_currentStep > 0) const SizedBox(width: 16),
          // Step3では再生成ボタンを表示
          if (_currentStep == 2 && _generatedPlan != null) ...[
            Expanded(
              child: OutlinedButton.icon(
                onPressed: _isGenerating ? null : _regeneratePlan,
                icon: const Icon(Icons.refresh),
                label: const Text('再生成'),
              ),
            ),
            const SizedBox(width: 16),
          ],
          Expanded(
            flex: _currentStep == 2 && _generatedPlan != null ? 1 : 2,
            child: FilledButton(
              onPressed: _isGenerating ? null : _handleNext,
              child: Text(_getNextButtonLabel()),
            ),
          ),
        ],
      ),
    );
  }

  String _getNextButtonLabel() {
    switch (_currentStep) {
      case 0:
        return '次へ →';
      case 1:
        return '生成 →';
      case 2:
        return _generatedPlan != null ? '✓ 確定' : '生成';
      default:
        return '次へ →';
    }
  }

  void _handleNext() {
    switch (_currentStep) {
      case 0:
        setState(() => _currentStep = 1);
        break;
      case 1:
        setState(() => _currentStep = 2);
        _generatePlan();
        break;
      case 2:
        if (_generatedPlan != null) {
          _confirmPlan();
        } else {
          _generatePlan();
        }
        break;
    }
  }

  Future<void> _generatePlan() async {
    setState(() {
      _isGenerating = true;
      _error = null;
      _excludedDishIdsInStep3 = {};
    });

    try {
      final menuProvider = context.read<MenuProvider>();
      menuProvider.setDays(_days);
      menuProvider.setPeople(_people);
      menuProvider.setExcludedAllergens(_excludedAllergens);
      menuProvider.setPreferBatchCooking(_preferBatchCooking);

      final settings = context.read<SettingsProvider>();
      await menuProvider.generatePlan(target: settings.nutrientTarget);

      if (menuProvider.currentPlan != null) {
        setState(() {
          _generatedPlan = menuProvider.currentPlan;
        });
      } else if (menuProvider.error != null) {
        setState(() {
          _error = menuProvider.error;
        });
      }
    } catch (e) {
      setState(() {
        _error = e.toString();
      });
    } finally {
      setState(() {
        _isGenerating = false;
      });
    }
  }

  Future<void> _regeneratePlan() async {
    setState(() {
      _isGenerating = true;
      _error = null;
    });

    try {
      final menuProvider = context.read<MenuProvider>();
      final settings = context.read<SettingsProvider>();

      // 除外した料理を反映
      for (final dishId in _excludedDishIdsInStep3) {
        menuProvider.excludeDish(dishId);
      }

      await menuProvider.refinePlan(target: settings.nutrientTarget);

      if (menuProvider.currentPlan != null) {
        setState(() {
          _generatedPlan = menuProvider.currentPlan;
          _excludedDishIdsInStep3 = {};
        });
      } else if (menuProvider.error != null) {
        setState(() {
          _error = menuProvider.error;
        });
      }
    } catch (e) {
      setState(() {
        _error = e.toString();
      });
    } finally {
      setState(() {
        _isGenerating = false;
      });
    }
  }

  void _confirmPlan() {
    if (_generatedPlan != null) {
      // 買い物リストを更新
      context.read<ShoppingProvider>().updateFromPlan(_generatedPlan!);
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('献立を生成しました')),
      );
    }
  }
}

/// 料理エントリ（表示用）
class _DishEntry {
  final DishPortion portion;
  final int day;
  final String mealType;

  _DishEntry({
    required this.portion,
    required this.day,
    required this.mealType,
  });
}
