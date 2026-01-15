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
    final widgetRef = ref;

    return ListView(
      controller: scrollController,
      padding: const EdgeInsets.all(16),
      children: [
        _buildSettingTile(
          context,
          icon: Icons.calendar_today,
          title: '期間',
          value: _getDaysLabel(state.days),
          onTap: () => _showDaysModal(context, state, controller),
        ),
        _buildSettingTile(
          context,
          icon: Icons.people,
          title: '人数',
          value: '${state.people}人',
          onTap: () => _showPeopleModal(context, state, controller),
        ),
        const Divider(height: 24),
        _buildMealSettingTile(
          context,
          icon: Icons.wb_sunny,
          title: '朝食',
          setting: state.mealSettings['breakfast'] ?? const MealSetting(),
          onTap: () => _showMealSettingModal(context, controller, 'breakfast', '朝食', widgetRef),
        ),
        _buildMealSettingTile(
          context,
          icon: Icons.light_mode,
          title: '昼食',
          setting: state.mealSettings['lunch'] ?? const MealSetting(),
          onTap: () => _showMealSettingModal(context, controller, 'lunch', '昼食', widgetRef),
        ),
        _buildMealSettingTile(
          context,
          icon: Icons.nightlight,
          title: '夕食',
          setting: state.mealSettings['dinner'] ?? const MealSetting(),
          onTap: () => _showMealSettingModal(context, controller, 'dinner', '夕食', widgetRef),
        ),
        const Divider(height: 24),
        _buildSettingTile(
          context,
          icon: Icons.repeat,
          title: '料理の繰り返し',
          value: _getVarietyLabel(state.varietyLevel),
          description: _getVarietyDescription(state.varietyLevel),
          onTap: () => _showVarietyModal(context, state, controller),
        ),
        _buildSettingTile(
          context,
          icon: Icons.warning_amber,
          title: 'アレルゲン除外',
          value: state.excludedAllergens.isEmpty
              ? 'なし'
              : state.excludedAllergens.map((a) => a.displayName).join(', '),
          onTap: () => _showAllergenModal(context, controller, widgetRef),
        ),
        const Divider(height: 24),
        _buildSettingTile(
          context,
          icon: Icons.local_fire_department,
          title: 'カロリー目標',
          value: '${state.nutrientTarget.caloriesMin.toInt()} - ${state.nutrientTarget.caloriesMax.toInt()} kcal',
          onTap: () => _showCaloriesModal(context, controller, widgetRef),
        ),
        _buildSettingTile(
          context,
          icon: Icons.fitness_center,
          title: 'タンパク質目標',
          value: '${state.nutrientTarget.proteinMin.toInt()} - ${state.nutrientTarget.proteinMax.toInt()} g',
          onTap: () => _showProteinModal(context, controller, widgetRef),
        ),
      ],
    );
  }

  String _getDaysLabel(int days) {
    switch (days) {
      case 1:
        return '1日';
      case 3:
        return '3日';
      case 7:
        return '1週間';
      default:
        return '$days日';
    }
  }

  String _getVarietyLabel(String level) {
    switch (level) {
      case 'small':
        return '繰り返す';
      case 'large':
        return '繰り返さない';
      default:
        return '適度に';
    }
  }

  String _getVarietyDescription(String level) {
    switch (level) {
      case 'small':
        return '作り置きしやすい';
      case 'large':
        return 'バリエーション重視';
      default:
        return 'バランス良く';
    }
  }

  Widget _buildSettingTile(
    BuildContext context, {
    required IconData icon,
    required String title,
    required String value,
    String? description,
    required VoidCallback onTap,
  }) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: Icon(icon, color: Theme.of(context).colorScheme.primary),
        title: Text(title),
        subtitle: description != null ? Text(description, style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.outline)) : null,
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              value,
              style: TextStyle(
                color: Theme.of(context).colorScheme.primary,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(width: 4),
            Icon(Icons.chevron_right, color: Theme.of(context).colorScheme.outline),
          ],
        ),
        onTap: onTap,
      ),
    );
  }

  Widget _buildMealSettingTile(
    BuildContext context, {
    required IconData icon,
    required String title,
    required MealSetting setting,
    required VoidCallback onTap,
  }) {
    final valueText = setting.enabled ? setting.preset.displayName : 'OFF';

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: Icon(
          icon,
          color: setting.enabled
              ? Theme.of(context).colorScheme.primary
              : Theme.of(context).colorScheme.outline,
        ),
        title: Text(
          title,
          style: TextStyle(
            color: setting.enabled ? null : Theme.of(context).colorScheme.outline,
          ),
        ),
        subtitle: setting.enabled && setting.preset != MealPreset.custom
            ? Text(
                setting.preset.description,
                style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.outline),
              )
            : null,
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              valueText,
              style: TextStyle(
                color: setting.enabled
                    ? Theme.of(context).colorScheme.primary
                    : Theme.of(context).colorScheme.outline,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(width: 4),
            Icon(Icons.chevron_right, color: Theme.of(context).colorScheme.outline),
          ],
        ),
        onTap: onTap,
      ),
    );
  }

  // === モーダル表示 ===

  void _showDaysModal(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
  ) {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Padding(
              padding: EdgeInsets.all(16),
              child: Text('期間を選択', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ),
            _buildModalOption(context, '1日', '今日の献立', state.days == 1, () {
              controller.setDays(1);
              Navigator.pop(context);
            }),
            _buildModalOption(context, '3日', '週の前半・後半', state.days == 3, () {
              controller.setDays(3);
              Navigator.pop(context);
            }),
            _buildModalOption(context, '1週間', '週末にまとめて計画', state.days == 7, () {
              controller.setDays(7);
              Navigator.pop(context);
            }),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  void _showPeopleModal(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
  ) {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Padding(
              padding: EdgeInsets.all(16),
              child: Text('人数を選択', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ),
            ...List.generate(6, (i) {
              final people = i + 1;
              return _buildModalOption(
                context,
                '$people人',
                null,
                state.people == people,
                () {
                  controller.setPeople(people);
                  Navigator.pop(context);
                },
              );
            }),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  void _showVarietyModal(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
  ) {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Padding(
              padding: EdgeInsets.all(16),
              child: Text('料理の繰り返し', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ),
            _buildModalOption(context, '繰り返す', '同じ料理を複数回使用（作り置きしやすい）', state.varietyLevel == 'small', () {
              controller.setVarietyLevel('small');
              Navigator.pop(context);
            }),
            _buildModalOption(context, '適度に', '適度なバランスで料理を提案', state.varietyLevel == 'normal', () {
              controller.setVarietyLevel('normal');
              Navigator.pop(context);
            }),
            _buildModalOption(context, '繰り返さない', '毎食違う料理を提案（バリエーション重視）', state.varietyLevel == 'large', () {
              controller.setVarietyLevel('large');
              Navigator.pop(context);
            }),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  void _showAllergenModal(
    BuildContext context,
    GenerateModalController controller,
    WidgetRef ref,
  ) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => Consumer(
        builder: (context, ref, _) {
          final state = ref.watch(generateModalControllerProvider);
          return SafeArea(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      const Expanded(
                        child: Text('アレルゲン除外', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      ),
                      TextButton(
                        onPressed: () => Navigator.pop(context),
                        child: const Text('完了'),
                      ),
                    ],
                  ),
                ),
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 16),
                  child: Text(
                    '選択したアレルゲンを含む料理を除外します',
                    style: TextStyle(fontSize: 13, color: Colors.grey),
                  ),
                ),
                const SizedBox(height: 8),
                ...Allergen.values.map((allergen) {
                  final isSelected = state.excludedAllergens.contains(allergen);
                  return CheckboxListTile(
                    title: Text(allergen.displayName),
                    value: isSelected,
                    activeColor: Colors.red,
                    onChanged: (_) {
                      controller.toggleAllergen(allergen);
                    },
                  );
                }),
                const SizedBox(height: 16),
              ],
            ),
          );
        },
      ),
    );
  }

  void _showCaloriesModal(
    BuildContext context,
    GenerateModalController controller,
    WidgetRef ref,
  ) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => Consumer(
        builder: (context, ref, _) {
          final state = ref.watch(generateModalControllerProvider);
          var minValue = state.nutrientTarget.caloriesMin;
          var maxValue = state.nutrientTarget.caloriesMax;

          return StatefulBuilder(
            builder: (context, setState) => SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Row(
                      children: [
                        const Expanded(
                          child: Text('カロリー目標', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                        ),
                        TextButton(
                          onPressed: () => Navigator.pop(context),
                          child: const Text('完了'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Text('最小: ${minValue.toInt()} kcal'),
                    Slider(
                      value: minValue,
                      min: 1200,
                      max: 3000,
                      divisions: 36,
                      onChanged: (value) {
                        setState(() {
                          minValue = value;
                          if (maxValue < minValue + 200) {
                            maxValue = minValue + 200;
                          }
                        });
                        controller.setCaloriesRange(minValue, maxValue);
                      },
                    ),
                    const SizedBox(height: 8),
                    Text('最大: ${maxValue.toInt()} kcal'),
                    Slider(
                      value: maxValue,
                      min: 1400,
                      max: 4000,
                      divisions: 52,
                      onChanged: (value) {
                        setState(() {
                          maxValue = value;
                          if (minValue > maxValue - 200) {
                            minValue = maxValue - 200;
                          }
                        });
                        controller.setCaloriesRange(minValue, maxValue);
                      },
                    ),
                    const SizedBox(height: 16),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  void _showProteinModal(
    BuildContext context,
    GenerateModalController controller,
    WidgetRef ref,
  ) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => Consumer(
        builder: (context, ref, _) {
          final state = ref.watch(generateModalControllerProvider);
          var minValue = state.nutrientTarget.proteinMin;
          var maxValue = state.nutrientTarget.proteinMax;

          return StatefulBuilder(
            builder: (context, setState) => SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Row(
                      children: [
                        const Expanded(
                          child: Text('タンパク質目標', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                        ),
                        TextButton(
                          onPressed: () => Navigator.pop(context),
                          child: const Text('完了'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Text('最小: ${minValue.toInt()} g'),
                    Slider(
                      value: minValue,
                      min: 30,
                      max: 150,
                      divisions: 24,
                      onChanged: (value) {
                        setState(() {
                          minValue = value;
                          if (maxValue < minValue + 20) {
                            maxValue = minValue + 20;
                          }
                        });
                        controller.setProteinRange(minValue, maxValue);
                      },
                    ),
                    const SizedBox(height: 8),
                    Text('最大: ${maxValue.toInt()} g'),
                    Slider(
                      value: maxValue,
                      min: 50,
                      max: 200,
                      divisions: 30,
                      onChanged: (value) {
                        setState(() {
                          maxValue = value;
                          if (minValue > maxValue - 20) {
                            minValue = maxValue - 20;
                          }
                        });
                        controller.setProteinRange(minValue, maxValue);
                      },
                    ),
                    const SizedBox(height: 16),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  void _showMealSettingModal(
    BuildContext context,
    GenerateModalController controller,
    String mealType,
    String mealLabel,
    WidgetRef ref,
  ) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => Consumer(
        builder: (context, ref, _) {
          final state = ref.watch(generateModalControllerProvider);
          final currentSetting = state.mealSettings[mealType] ?? const MealSetting();

          return SafeArea(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      Expanded(
                        child: Text('$mealLabelの設定', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      ),
                      TextButton(
                        onPressed: () => Navigator.pop(context),
                        child: const Text('完了'),
                      ),
                    ],
                  ),
                ),
                SwitchListTile(
                  title: Text('$mealLabelを含める'),
                  value: currentSetting.enabled,
                  onChanged: (v) {
                    controller.setMealEnabled(mealType, v);
                  },
                ),
                if (currentSetting.enabled) ...[
                  const Divider(),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: Align(
                      alignment: Alignment.centerLeft,
                      child: Text('プリセット', style: TextStyle(fontWeight: FontWeight.w500)),
                    ),
                  ),
                  ...MealPreset.values.where((p) => p != MealPreset.custom).map((preset) {
                    final isSelected = currentSetting.preset == preset;
                    return ListTile(
                      title: Text(preset.displayName),
                      subtitle: Text(preset.description, style: const TextStyle(fontSize: 12)),
                      trailing: isSelected
                          ? Icon(Icons.check, color: Theme.of(context).colorScheme.primary)
                          : null,
                      onTap: () {
                        controller.setMealPreset(mealType, preset);
                      },
                    );
                  }),
                  ListTile(
                    title: const Text('カスタム'),
                    subtitle: const Text('品数を細かく設定', style: TextStyle(fontSize: 12)),
                    trailing: currentSetting.preset == MealPreset.custom
                        ? Icon(Icons.check, color: Theme.of(context).colorScheme.primary)
                        : const Icon(Icons.chevron_right),
                    onTap: () {
                      Navigator.pop(context);
                      _showCustomSettingsDialog(context, controller, mealType, mealLabel, currentSetting);
                    },
                  ),
                ],
                const SizedBox(height: 16),
              ],
            ),
          );
        },
      ),
    );
  }

  void _showCustomSettingsDialog(
    BuildContext context,
    GenerateModalController controller,
    String mealType,
    String mealLabel,
    MealSetting currentSetting,
  ) {
    final categories = currentSetting.customCategories ??
        mealPresets[currentSetting.preset] ??
        const MealCategoryConstraints();

    showDialog(
      context: context,
      builder: (context) => _CustomSettingsDialog(
        mealType: mealType,
        mealLabel: mealLabel,
        initialCategories: categories,
        onSave: (newCategories) {
          controller.setMealCategoryConstraint(mealType, '主食', newCategories.staple.min, newCategories.staple.max);
          controller.setMealCategoryConstraint(mealType, '主菜', newCategories.main.min, newCategories.main.max);
          controller.setMealCategoryConstraint(mealType, '副菜', newCategories.side.min, newCategories.side.max);
          controller.setMealCategoryConstraint(mealType, '汁物', newCategories.soup.min, newCategories.soup.max);
          controller.setMealCategoryConstraint(mealType, 'デザート', newCategories.dessert.min, newCategories.dessert.max);
        },
      ),
    );
  }

  Widget _buildModalOption(
    BuildContext context,
    String title,
    String? subtitle,
    bool isSelected,
    VoidCallback onTap,
  ) {
    return ListTile(
      title: Text(title),
      subtitle: subtitle != null ? Text(subtitle, style: const TextStyle(fontSize: 12)) : null,
      trailing: isSelected
          ? Icon(Icons.check, color: Theme.of(context).colorScheme.primary)
          : null,
      onTap: onTap,
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
