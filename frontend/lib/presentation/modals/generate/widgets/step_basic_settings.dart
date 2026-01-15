import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../domain/entities/settings.dart';
import '../generate_modal_controller.dart';

/// Step1: 基本設定
class StepBasicSettings extends ConsumerWidget {
  final ScrollController scrollController;

  const StepBasicSettings({
    super.key,
    required this.scrollController,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(generateModalControllerProvider);
    final controller = ref.read(generateModalControllerProvider.notifier);

    return ListView(
      controller: scrollController,
      padding: const EdgeInsets.all(16),
      children: [
        _buildPeriodCard(context, state, controller),
        const SizedBox(height: 16),
        _buildPeopleCard(context, state, controller),
        const SizedBox(height: 16),
        _buildMealSettingsCard(context, state, controller, ref),
        const SizedBox(height: 16),
        _buildAllergenCard(context, state, controller),
        const SizedBox(height: 16),
        _buildVarietyCard(context, state, controller),
      ],
    );
  }

  Widget _buildPeriodCard(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
  ) {
    return Card(
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
                _buildPeriodChip(state, controller, 1, '1日'),
                _buildPeriodChip(state, controller, 3, '3日'),
                _buildPeriodChip(state, controller, 7, '1週間'),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              '${state.days}日分の献立を生成',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.outline,
                  ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPeriodChip(
    GenerateModalState state,
    GenerateModalController controller,
    int days,
    String label,
  ) {
    return ChoiceChip(
      label: Text(label),
      selected: state.days == days,
      onSelected: (_) => controller.setDays(days),
    );
  }

  Widget _buildPeopleCard(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
  ) {
    return Card(
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
                        onPressed: state.people > 1
                            ? () => controller.setPeople(state.people - 1)
                            : null,
                      ),
                      SizedBox(
                        width: 48,
                        child: Text(
                          '${state.people}人',
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.add),
                        onPressed: state.people < 6
                            ? () => controller.setPeople(state.people + 1)
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
    );
  }

  Widget _buildMealSettingsCard(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
    WidgetRef ref,
  ) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.restaurant_menu, size: 20),
                const SizedBox(width: 8),
                Text('朝昼夜の設定', style: Theme.of(context).textTheme.titleSmall),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              'プリセットを選択するか、カスタムで品数を細かく設定できます',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.outline,
                  ),
            ),
            const SizedBox(height: 12),
            _buildMealSection(context, state, controller, '朝食', 'breakfast', Icons.wb_sunny),
            const Divider(height: 24),
            _buildMealSection(context, state, controller, '昼食', 'lunch', Icons.light_mode),
            const Divider(height: 24),
            _buildMealSection(context, state, controller, '夕食', 'dinner', Icons.nightlight),
          ],
        ),
      ),
    );
  }

  Widget _buildMealSection(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
    String label,
    String mealType,
    IconData icon,
  ) {
    final setting = state.mealSettings[mealType] ?? const MealSetting();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 食事名と有効/無効スイッチ
        Row(
          children: [
            Icon(icon, size: 20, color: Theme.of(context).colorScheme.primary),
            const SizedBox(width: 8),
            Text(label, style: Theme.of(context).textTheme.titleSmall),
            const Spacer(),
            Text(
              setting.enabled ? 'ON' : 'OFF',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: setting.enabled
                        ? Theme.of(context).colorScheme.primary
                        : Theme.of(context).colorScheme.outline,
                  ),
            ),
            Switch(
              value: setting.enabled,
              onChanged: (v) => controller.setMealEnabled(mealType, v),
            ),
          ],
        ),

        if (setting.enabled) ...[
          const SizedBox(height: 8),
          // プリセット選択
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: MealPreset.values
                .where((p) => p != MealPreset.custom) // カスタムは個別ボタン
                .map((preset) => ChoiceChip(
                      label: Text(preset.displayName),
                      selected: setting.preset == preset,
                      onSelected: (_) => controller.setMealPreset(mealType, preset),
                    ))
                .toList(),
          ),
          const SizedBox(height: 4),
          // プリセット説明
          Text(
            setting.preset.description,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.outline,
                  fontStyle: FontStyle.italic,
                ),
          ),
          const SizedBox(height: 8),
          // カスタム設定ボタン
          OutlinedButton.icon(
            icon: Icon(
              setting.preset == MealPreset.custom ? Icons.edit : Icons.tune,
              size: 16,
            ),
            label: Text(setting.preset == MealPreset.custom ? 'カスタム設定中' : 'カスタム設定'),
            onPressed: () => _showCustomSettingsDialog(context, controller, mealType, setting),
            style: OutlinedButton.styleFrom(
              foregroundColor: setting.preset == MealPreset.custom
                  ? Theme.of(context).colorScheme.primary
                  : null,
            ),
          ),
          // カスタムの場合は現在の設定を表示
          if (setting.preset == MealPreset.custom) ...[
            const SizedBox(height: 8),
            _buildCategoryConstraintsSummary(context, setting.getCategories()),
          ],
        ],
      ],
    );
  }

  Widget _buildCategoryConstraintsSummary(BuildContext context, MealCategoryConstraints categories) {
    final items = <String>[];
    if (categories.staple.max > 0) items.add('主食${categories.staple.min}-${categories.staple.max}');
    if (categories.main.max > 0) items.add('主菜${categories.main.min}-${categories.main.max}');
    if (categories.side.max > 0) items.add('副菜${categories.side.min}-${categories.side.max}');
    if (categories.soup.max > 0) items.add('汁物${categories.soup.min}-${categories.soup.max}');
    if (categories.dessert.max > 0) items.add('デザート${categories.dessert.min}-${categories.dessert.max}');

    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        items.join(' / '),
        style: Theme.of(context).textTheme.bodySmall,
      ),
    );
  }

  void _showCustomSettingsDialog(
    BuildContext context,
    GenerateModalController controller,
    String mealType,
    MealSetting currentSetting,
  ) {
    // 現在のカテゴリ設定を取得（プリセットからの初期値も含む）
    final categories = currentSetting.customCategories ??
        mealPresets[currentSetting.preset] ??
        const MealCategoryConstraints();

    showDialog(
      context: context,
      builder: (context) => _CustomSettingsDialog(
        mealType: mealType,
        mealLabel: mealType == 'breakfast' ? '朝食' : (mealType == 'lunch' ? '昼食' : '夕食'),
        initialCategories: categories,
        onSave: (newCategories) {
          // 各カテゴリを個別に更新（全体をカスタムとして設定）
          controller.setMealCategoryConstraint(mealType, '主食', newCategories.staple.min, newCategories.staple.max);
          controller.setMealCategoryConstraint(mealType, '主菜', newCategories.main.min, newCategories.main.max);
          controller.setMealCategoryConstraint(mealType, '副菜', newCategories.side.min, newCategories.side.max);
          controller.setMealCategoryConstraint(mealType, '汁物', newCategories.soup.min, newCategories.soup.max);
          controller.setMealCategoryConstraint(mealType, 'デザート', newCategories.dessert.min, newCategories.dessert.max);
        },
      ),
    );
  }

  Widget _buildAllergenCard(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
  ) {
    return Card(
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
                final isSelected = state.excludedAllergens.contains(allergen);
                return FilterChip(
                  label: Text(allergen.displayName),
                  selected: isSelected,
                  selectedColor: Colors.red.shade100,
                  checkmarkColor: Colors.red.shade700,
                  onSelected: (_) => controller.toggleAllergen(allergen),
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildVarietyCard(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
  ) {
    String description;
    switch (state.varietyLevel) {
      case 'small':
        description = '同じ料理を繰り返し使用（作り置きしやすい）';
        break;
      case 'large':
        description = '毎食違う料理を提案（バリエーション重視）';
        break;
      default:
        description = '適度なバランスで料理を提案';
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.repeat, size: 20),
                const SizedBox(width: 8),
                Text('料理の繰り返し', style: Theme.of(context).textTheme.titleSmall),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              '同じ料理を繰り返すかどうかを設定します',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.outline,
                  ),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _buildLevelChip(state.varietyLevel, 'small', '繰り返す',
                    () => controller.setVarietyLevel('small')),
                _buildLevelChip(state.varietyLevel, 'normal', '適度に',
                    () => controller.setVarietyLevel('normal')),
                _buildLevelChip(state.varietyLevel, 'large', '繰り返さない',
                    () => controller.setVarietyLevel('large')),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              description,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.outline,
                    fontStyle: FontStyle.italic,
                  ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLevelChip(
    String currentLevel,
    String value,
    String label,
    VoidCallback onSelected,
  ) {
    return ChoiceChip(
      label: Text(label),
      selected: currentLevel == value,
      onSelected: (_) => onSelected(),
    );
  }
}

/// カスタム設定ダイアログ
class _CustomSettingsDialog extends StatefulWidget {
  final String mealType;
  final String mealLabel;
  final MealCategoryConstraints initialCategories;
  final void Function(MealCategoryConstraints) onSave;

  const _CustomSettingsDialog({
    required this.mealType,
    required this.mealLabel,
    required this.initialCategories,
    required this.onSave,
  });

  @override
  State<_CustomSettingsDialog> createState() => _CustomSettingsDialogState();
}

class _CustomSettingsDialogState extends State<_CustomSettingsDialog> {
  late int stapleMin, stapleMax;
  late int mainMin, mainMax;
  late int sideMin, sideMax;
  late int soupMin, soupMax;
  late int dessertMin, dessertMax;

  @override
  void initState() {
    super.initState();
    stapleMin = widget.initialCategories.staple.min;
    stapleMax = widget.initialCategories.staple.max;
    mainMin = widget.initialCategories.main.min;
    mainMax = widget.initialCategories.main.max;
    sideMin = widget.initialCategories.side.min;
    sideMax = widget.initialCategories.side.max;
    soupMin = widget.initialCategories.soup.min;
    soupMax = widget.initialCategories.soup.max;
    dessertMin = widget.initialCategories.dessert.min;
    dessertMax = widget.initialCategories.dessert.max;
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('${widget.mealLabel}のカスタム設定'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildCategoryRow('主食', stapleMin, stapleMax, (min, max) {
              setState(() { stapleMin = min; stapleMax = max; });
            }),
            const Divider(),
            _buildCategoryRow('主菜', mainMin, mainMax, (min, max) {
              setState(() { mainMin = min; mainMax = max; });
            }),
            const Divider(),
            _buildCategoryRow('副菜', sideMin, sideMax, (min, max) {
              setState(() { sideMin = min; sideMax = max; });
            }),
            const Divider(),
            _buildCategoryRow('汁物', soupMin, soupMax, (min, max) {
              setState(() { soupMin = min; soupMax = max; });
            }),
            const Divider(),
            _buildCategoryRow('デザート', dessertMin, dessertMax, (min, max) {
              setState(() { dessertMin = min; dessertMax = max; });
            }),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('キャンセル'),
        ),
        FilledButton(
          onPressed: () {
            widget.onSave(MealCategoryConstraints(
              staple: CategoryConstraint(min: stapleMin, max: stapleMax),
              main: CategoryConstraint(min: mainMin, max: mainMax),
              side: CategoryConstraint(min: sideMin, max: sideMax),
              soup: CategoryConstraint(min: soupMin, max: soupMax),
              dessert: CategoryConstraint(min: dessertMin, max: dessertMax),
            ));
            Navigator.of(context).pop();
          },
          child: const Text('保存'),
        ),
      ],
    );
  }

  Widget _buildCategoryRow(
    String label,
    int min,
    int max,
    void Function(int min, int max) onChanged,
  ) {
    return Row(
      children: [
        SizedBox(
          width: 80,
          child: Text(label, style: Theme.of(context).textTheme.titleSmall),
        ),
        const SizedBox(width: 8),
        const Text('最小'),
        const SizedBox(width: 4),
        DropdownButton<int>(
          value: min,
          items: List.generate(4, (i) => DropdownMenuItem(value: i, child: Text('$i'))),
          onChanged: (v) {
            if (v != null) {
              final newMax = max < v ? v : max;
              onChanged(v, newMax);
            }
          },
        ),
        const SizedBox(width: 16),
        const Text('最大'),
        const SizedBox(width: 4),
        DropdownButton<int>(
          value: max,
          items: List.generate(4, (i) => DropdownMenuItem(value: i, child: Text('$i'))),
          onChanged: (v) {
            if (v != null) {
              final newMin = min > v ? v : min;
              onChanged(newMin, v);
            }
          },
        ),
      ],
    );
  }
}
