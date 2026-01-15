import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../domain/entities/dish.dart';
import '../../../../domain/entities/menu_plan.dart';
import '../../../../presentation/widgets/nutrient_progress_bar.dart';
import '../generate_modal_controller.dart';

/// Step3: 献立確認
class StepConfirmation extends ConsumerWidget {
  final ScrollController scrollController;
  final VoidCallback onRetry;

  const StepConfirmation({
    super.key,
    required this.scrollController,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(generateModalControllerProvider);

    if (state.isGenerating) {
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

    if (state.error != null) {
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
                state.error!,
                textAlign: TextAlign.center,
                style: TextStyle(color: Theme.of(context).colorScheme.outline),
              ),
            ),
            const SizedBox(height: 24),
            FilledButton.tonal(
              onPressed: onRetry,
              child: const Text('再試行'),
            ),
          ],
        ),
      );
    }

    if (state.generatedPlan == null) {
      return const Center(child: Text('献立を生成してください'));
    }

    return ListView(
      controller: scrollController,
      padding: const EdgeInsets.all(16),
      children: [
        _buildConditionsSummary(context, state),
        const SizedBox(height: 16),
        _buildExplanationCard(context),
        const SizedBox(height: 16),
        _buildAchievementCard(context, state.generatedPlan!),
        const SizedBox(height: 16),
        _buildDishList(context, ref, state),
        if (state.generatedPlan!.warnings.isNotEmpty) ...[
          const SizedBox(height: 16),
          _buildWarningsCard(context, state.generatedPlan!.warnings),
        ],
        const SizedBox(height: 16),
      ],
    );
  }

  Widget _buildConditionsSummary(BuildContext context, GenerateModalState state) {
    // 食事設定のサマリーを作成
    final mealSummary = <String>[];
    final meals = {'breakfast': '朝', 'lunch': '昼', 'dinner': '夜'};
    for (final entry in meals.entries) {
      final setting = state.mealSettings[entry.key];
      if (setting != null && setting.enabled) {
        mealSummary.add('${entry.value}:${setting.preset.displayName}');
      }
    }

    // バリエーション設定
    String varietyText;
    switch (state.varietyLevel) {
      case 'small':
        varietyText = '繰り返す';
        break;
      case 'large':
        varietyText = '繰り返さない';
        break;
      default:
        varietyText = '適度に';
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.settings, size: 16, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 6),
                Text(
                  '生成条件',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
              ],
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 6,
              children: [
                _buildConditionChip(context, '${state.days}日間'),
                _buildConditionChip(context, '${state.people}人分'),
                _buildConditionChip(context, mealSummary.join(' / ')),
                _buildConditionChip(context, '繰り返し: $varietyText'),
                if (state.excludedAllergens.isNotEmpty)
                  _buildConditionChip(
                    context,
                    '除外: ${state.excludedAllergens.map((a) => a.displayName).join(',')}',
                    isWarning: true,
                  ),
                if (state.ownedIngredientIds.isNotEmpty)
                  _buildConditionChip(context, '手持ち食材: ${state.ownedIngredientIds.length}品'),
                if (state.favoriteDishes.isNotEmpty)
                  _buildConditionChip(
                    context,
                    'お気に入り: ${state.favoriteDishes.length}品${state.guaranteeFavorites ? "(確定)" : ""}',
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildConditionChip(BuildContext context, String label, {bool isWarning = false}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: isWarning
            ? Colors.orange.shade50
            : Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(12),
        border: isWarning ? Border.all(color: Colors.orange.shade200) : null,
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 12,
          color: isWarning
              ? Colors.orange.shade800
              : Theme.of(context).colorScheme.onSurfaceVariant,
        ),
      ),
    );
  }

  Widget _buildExplanationCard(BuildContext context) {
    return Card(
      color: const Color(0xFFE8F5E9),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Text(
          '不要な料理をタップで除外',
          textAlign: TextAlign.center,
          style: TextStyle(color: const Color(0xFF2E7D32)),
        ),
      ),
    );
  }

  Widget _buildAchievementCard(BuildContext context, MultiDayMenuPlan plan) {
    // 表示する栄養素の定義（キー、ラベル、色）
    final nutrients = [
      {'key': 'calories', 'label': 'カロリー', 'color': Colors.orange},
      {'key': 'protein', 'label': 'タンパク質', 'color': Colors.red},
      {'key': 'fat', 'label': '脂質', 'color': Colors.amber},
      {'key': 'carbohydrate', 'label': '炭水化物', 'color': Colors.brown},
      {'key': 'fiber', 'label': '食物繊維', 'color': Colors.green},
      {'key': 'sodium', 'label': 'ナトリウム', 'color': Colors.purple},
      {'key': 'calcium', 'label': 'カルシウム', 'color': Colors.blue},
      {'key': 'iron', 'label': '鉄', 'color': Colors.grey},
      {'key': 'vitamin_a', 'label': 'ビタミンA', 'color': Colors.deepOrange},
      {'key': 'vitamin_c', 'label': 'ビタミンC', 'color': Colors.lime},
      {'key': 'vitamin_d', 'label': 'ビタミンD', 'color': Colors.teal},
    ];

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
            ...nutrients.map((n) {
              final value = plan.overallAchievement[n['key'] as String] ?? 0;
              // 値が0の場合はスキップ（データがない栄養素）
              if (value == 0 && !plan.overallAchievement.containsKey(n['key'])) {
                return const SizedBox.shrink();
              }
              return Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: NutrientProgressBar(
                  label: n['label'] as String,
                  value: value.toDouble(),
                  color: n['color'] as Color,
                ),
              );
            }),
          ],
        ),
      ),
    );
  }

  Widget _buildDishList(
    BuildContext context,
    WidgetRef ref,
    GenerateModalState state,
  ) {
    final plan = state.generatedPlan!;
    final controller = ref.read(generateModalControllerProvider.notifier);

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

    // 重複を除去
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
          final isExcluded =
              state.excludedDishIdsInStep3.contains(entry.portion.dish.id);
          return _buildDishCard(context, entry, isExcluded, controller);
        }),
      ],
    );
  }

  Widget _buildDishCard(
    BuildContext context,
    _DishEntry entry,
    bool isExcluded,
    GenerateModalController controller,
  ) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      color: isExcluded ? Colors.red.shade50 : null,
      child: InkWell(
        onTap: () => controller.toggleDishExclusion(entry.portion.dish.id),
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
                        decoration:
                            isExcluded ? TextDecoration.lineThrough : null,
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

  Widget _buildWarningsCard(
    BuildContext context,
    List<NutrientWarning> warnings,
  ) {
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
