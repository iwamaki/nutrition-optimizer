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
        _buildMealSettingsCard(context, state, controller),
        const SizedBox(height: 16),
        _buildAllergenCard(context, state, controller),
        const SizedBox(height: 16),
        _buildCaloriesCard(context, state, controller),
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
              '各食事の有効/無効と品数を設定します',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.outline,
                  ),
            ),
            const SizedBox(height: 12),
            _buildMealRow(context, state, controller, '朝食', 'breakfast', Icons.wb_sunny),
            const SizedBox(height: 8),
            _buildMealRow(context, state, controller, '昼食', 'lunch', Icons.light_mode),
            const SizedBox(height: 8),
            _buildMealRow(context, state, controller, '夕食', 'dinner', Icons.nightlight),
          ],
        ),
      ),
    );
  }

  Widget _buildMealRow(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
    String label,
    String mealType,
    IconData icon,
  ) {
    final setting = state.mealSettings[mealType] ?? const MealSetting();
    return Row(
      children: [
        Icon(icon, size: 18, color: Theme.of(context).colorScheme.outline),
        const SizedBox(width: 8),
        SizedBox(
          width: 40,
          child: Text(label, style: Theme.of(context).textTheme.bodyMedium),
        ),
        const SizedBox(width: 8),
        Switch(
          value: setting.enabled,
          onChanged: (v) => controller.setMealEnabled(mealType, v),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: SegmentedButton<VolumeLevel>(
            segments: const [
              ButtonSegment(
                value: VolumeLevel.small,
                label: Text('少なめ', style: TextStyle(fontSize: 11)),
              ),
              ButtonSegment(
                value: VolumeLevel.normal,
                label: Text('普通', style: TextStyle(fontSize: 11)),
              ),
              ButtonSegment(
                value: VolumeLevel.large,
                label: Text('多め', style: TextStyle(fontSize: 11)),
              ),
            ],
            selected: {setting.volume},
            onSelectionChanged: setting.enabled
                ? (selected) => controller.setMealVolume(mealType, selected.first)
                : null,
            style: ButtonStyle(
              visualDensity: VisualDensity.compact,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
          ),
        ),
      ],
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

  Widget _buildCaloriesCard(
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
                const Icon(Icons.local_fire_department, size: 20),
                const SizedBox(width: 8),
                Text('カロリー目標', style: Theme.of(context).textTheme.titleSmall),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              'カロリー目標を調整します',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.outline,
                  ),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _buildLevelChip(state.volumeLevel, 'small', '少なめ',
                    () => controller.setVolumeLevel('small')),
                _buildLevelChip(state.volumeLevel, 'normal', '普通',
                    () => controller.setVolumeLevel('normal')),
                _buildLevelChip(state.volumeLevel, 'large', '多め',
                    () => controller.setVolumeLevel('large')),
              ],
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
