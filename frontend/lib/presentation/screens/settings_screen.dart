import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/settings_provider.dart';
import '../../domain/entities/settings.dart';

/// 設定画面（Riverpod版）
class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settingsState = ref.watch(settingsNotifierProvider);

    if (settingsState.isLoading) {
      return Scaffold(
        appBar: AppBar(
          title: const Text('設定'),
          backgroundColor: Theme.of(context).colorScheme.primary,
          foregroundColor: Theme.of(context).colorScheme.onPrimary,
        ),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('設定'),
        backgroundColor: Theme.of(context).colorScheme.primary,
        foregroundColor: Theme.of(context).colorScheme.onPrimary,
      ),
      body: ListView(
        children: [
          // デフォルト設定セクション
          _buildSectionHeader(context, 'デフォルト設定'),
          _buildDaysSetting(context, ref, settingsState),
          _buildPeopleSetting(context, ref, settingsState),
          _buildVarietySetting(context, ref, settingsState),
          const Divider(),

          // 食事プリセットセクション
          _buildSectionHeader(context, '食事プリセット'),
          _buildMealPresetSettings(context, ref, settingsState),
          const Divider(),

          // 栄養目標セクション
          _buildSectionHeader(context, '栄養目標'),
          _buildCaloriesSetting(context, ref, settingsState),
          _buildProteinSetting(context, ref, settingsState),
          _buildOtherNutrientsSetting(context, settingsState),
          const Divider(),

          // アレルゲン除外セクション
          _buildSectionHeader(context, 'アレルゲン除外'),
          _buildAllergenSettings(context, ref, settingsState),
          const Divider(),

          // その他
          _buildSectionHeader(context, 'その他'),
          _buildResetButton(context, ref),
          const SizedBox(height: 32),

          // アプリ情報
          _buildAppInfo(context),
          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(BuildContext context, String title) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      child: Text(
        title,
        style: Theme.of(context).textTheme.titleSmall?.copyWith(
              color: Theme.of(context).colorScheme.primary,
            ),
      ),
    );
  }

  Widget _buildDaysSetting(BuildContext context, WidgetRef ref, SettingsState settingsState) {
    String getDaysLabel(int days) {
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

    return ListTile(
      leading: const Icon(Icons.calendar_today),
      title: const Text('デフォルト日数'),
      subtitle: Text(getDaysLabel(settingsState.defaultDays)),
      trailing: const Icon(Icons.chevron_right),
      onTap: () => _showDaysModal(context, ref, settingsState),
    );
  }

  void _showDaysModal(BuildContext context, WidgetRef ref, SettingsState settingsState) {
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
            _buildModalOption(context, '1日', '今日の献立', settingsState.defaultDays == 1, () {
              ref.read(settingsNotifierProvider.notifier).setDefaultDays(1);
              Navigator.pop(context);
            }),
            _buildModalOption(context, '3日', '週の前半・後半', settingsState.defaultDays == 3, () {
              ref.read(settingsNotifierProvider.notifier).setDefaultDays(3);
              Navigator.pop(context);
            }),
            _buildModalOption(context, '1週間', '週末にまとめて計画', settingsState.defaultDays == 7, () {
              ref.read(settingsNotifierProvider.notifier).setDefaultDays(7);
              Navigator.pop(context);
            }),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _buildPeopleSetting(BuildContext context, WidgetRef ref, SettingsState settingsState) {
    return ListTile(
      leading: const Icon(Icons.people),
      title: const Text('デフォルト人数'),
      subtitle: Text('${settingsState.defaultPeople}人'),
      trailing: const Icon(Icons.chevron_right),
      onTap: () => _showPeopleModal(context, ref, settingsState),
    );
  }

  void _showPeopleModal(BuildContext context, WidgetRef ref, SettingsState settingsState) {
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
                settingsState.defaultPeople == people,
                () {
                  ref.read(settingsNotifierProvider.notifier).setDefaultPeople(people);
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

  Widget _buildVarietySetting(BuildContext context, WidgetRef ref, SettingsState settingsState) {
    String getLabel(String level) {
      switch (level) {
        case 'small':
          return '繰り返す（作り置き向き）';
        case 'large':
          return '繰り返さない（バリエーション重視）';
        default:
          return '適度に';
      }
    }

    return ListTile(
      leading: const Icon(Icons.refresh),
      title: const Text('料理の繰り返し'),
      subtitle: Text(getLabel(settingsState.varietyLevel)),
      trailing: const Icon(Icons.chevron_right),
      onTap: () => _showVarietyDialog(context, ref, settingsState),
    );
  }

  void _showVarietyDialog(BuildContext context, WidgetRef ref, SettingsState settingsState) {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Padding(
              padding: EdgeInsets.all(16),
              child: Text('料理の繰り返し', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            ),
            ListTile(
              leading: settingsState.varietyLevel == 'small'
                  ? const Icon(Icons.check, color: Colors.green)
                  : const SizedBox(width: 24),
              title: const Text('繰り返す'),
              subtitle: const Text('同じ料理を複数日で使用（作り置き向き）'),
              onTap: () {
                ref.read(settingsNotifierProvider.notifier).setVarietyLevel('small');
                Navigator.pop(context);
              },
            ),
            ListTile(
              leading: settingsState.varietyLevel == 'normal'
                  ? const Icon(Icons.check, color: Colors.green)
                  : const SizedBox(width: 24),
              title: const Text('適度に'),
              subtitle: const Text('バランス良く繰り返し'),
              onTap: () {
                ref.read(settingsNotifierProvider.notifier).setVarietyLevel('normal');
                Navigator.pop(context);
              },
            ),
            ListTile(
              leading: settingsState.varietyLevel == 'large'
                  ? const Icon(Icons.check, color: Colors.green)
                  : const SizedBox(width: 24),
              title: const Text('繰り返さない'),
              subtitle: const Text('毎日違う料理（バリエーション重視）'),
              onTap: () {
                ref.read(settingsNotifierProvider.notifier).setVarietyLevel('large');
                Navigator.pop(context);
              },
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _buildMealPresetSettings(BuildContext context, WidgetRef ref, SettingsState settingsState) {
    final meals = [
      {'key': 'breakfast', 'label': '朝食', 'icon': Icons.wb_sunny},
      {'key': 'lunch', 'label': '昼食', 'icon': Icons.wb_cloudy},
      {'key': 'dinner', 'label': '夕食', 'icon': Icons.nights_stay},
    ];

    return Column(
      children: meals.map((meal) {
        final setting = settingsState.mealSettings[meal['key'] as String] ?? const MealSetting();
        return ListTile(
          leading: Icon(meal['icon'] as IconData),
          title: Text(meal['label'] as String),
          subtitle: Text(setting.enabled ? setting.preset.displayName : 'スキップ'),
          trailing: const Icon(Icons.chevron_right),
          onTap: () => _showMealPresetDialog(
            context,
            ref,
            meal['key'] as String,
            meal['label'] as String,
            settingsState,
          ),
        );
      }).toList(),
    );
  }

  void _showMealPresetDialog(
    BuildContext context,
    WidgetRef ref,
    String mealType,
    String mealLabel,
    SettingsState settingsState,
  ) {
    final currentSetting = settingsState.mealSettings[mealType] ?? const MealSetting();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('$mealLabel のプリセット', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  Row(
                    children: [
                      Text(currentSetting.enabled ? '有効' : 'スキップ'),
                      Switch(
                        value: currentSetting.enabled,
                        onChanged: (value) {
                          ref.read(settingsNotifierProvider.notifier).setMealEnabled(mealType, value);
                        },
                      ),
                    ],
                  ),
                ],
              ),
            ),
            ...MealPreset.values.where((p) => p != MealPreset.custom).map((preset) {
              return ListTile(
                leading: currentSetting.preset == preset
                    ? const Icon(Icons.check, color: Colors.green)
                    : const SizedBox(width: 24),
                title: Text(preset.displayName),
                subtitle: Text(preset.description),
                enabled: currentSetting.enabled,
                onTap: currentSetting.enabled
                    ? () {
                        ref.read(settingsNotifierProvider.notifier).setMealPreset(mealType, preset);
                        Navigator.pop(context);
                      }
                    : null,
              );
            }),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _buildCaloriesSetting(BuildContext context, WidgetRef ref, SettingsState settingsState) {
    final target = settingsState.nutrientTarget;

    return ListTile(
      leading: const Icon(Icons.local_fire_department),
      title: const Text('カロリー目標'),
      subtitle: Text(
          '${target.caloriesMin.toInt()} - ${target.caloriesMax.toInt()} kcal'),
      trailing: const Icon(Icons.chevron_right),
      onTap: () => _showCaloriesDialog(context, ref, settingsState),
    );
  }

  void _showCaloriesDialog(BuildContext context, WidgetRef ref, SettingsState settingsState) {
    final target = settingsState.nutrientTarget;
    var minValue = target.caloriesMin;
    var maxValue = target.caloriesMax;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text('カロリー目標'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
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
                },
              ),
              const SizedBox(height: 16),
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
                },
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('キャンセル'),
            ),
            FilledButton(
              onPressed: () {
                ref.read(settingsNotifierProvider.notifier).setCaloriesRange(minValue, maxValue);
                Navigator.pop(context);
              },
              child: const Text('保存'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProteinSetting(BuildContext context, WidgetRef ref, SettingsState settingsState) {
    final target = settingsState.nutrientTarget;

    return ListTile(
      leading: const Icon(Icons.fitness_center),
      title: const Text('タンパク質目標'),
      subtitle: Text(
          '${target.proteinMin.toInt()} - ${target.proteinMax.toInt()} g'),
      trailing: const Icon(Icons.chevron_right),
      onTap: () => _showProteinDialog(context, ref, settingsState),
    );
  }

  void _showProteinDialog(BuildContext context, WidgetRef ref, SettingsState settingsState) {
    final target = settingsState.nutrientTarget;
    var minValue = target.proteinMin;
    var maxValue = target.proteinMax;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text('タンパク質目標'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
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
                },
              ),
              const SizedBox(height: 16),
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
                },
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('キャンセル'),
            ),
            FilledButton(
              onPressed: () {
                ref.read(settingsNotifierProvider.notifier).setProteinRange(minValue, maxValue);
                Navigator.pop(context);
              },
              child: const Text('保存'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOtherNutrientsSetting(BuildContext context, SettingsState settingsState) {
    return ListTile(
      leading: const Icon(Icons.science),
      title: const Text('その他栄養素'),
      subtitle: const Text('脂質・炭水化物・食物繊維など'),
      trailing: const Icon(Icons.chevron_right),
      onTap: () => _showOtherNutrientsDialog(context, settingsState),
    );
  }

  void _showOtherNutrientsDialog(BuildContext context, SettingsState settingsState) {
    final target = settingsState.nutrientTarget;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.85,
        minChildSize: 0.5,
        maxChildSize: 0.95,
        expand: false,
        builder: (context, scrollController) => SafeArea(
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    const Expanded(
                      child: Text(
                        '栄養素目標一覧',
                        style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                    ),
                    TextButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('閉じる'),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: ListView(
                  controller: scrollController,
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  children: [
                    // 三大栄養素
                    _buildNutrientSection(context, '三大栄養素'),
                    _buildNutrientInfoRow('脂質', '${target.fatMin.toInt()} - ${target.fatMax.toInt()} g'),
                    _buildNutrientInfoRow('炭水化物', '${target.carbohydrateMin.toInt()} - ${target.carbohydrateMax.toInt()} g'),
                    _buildNutrientInfoRow('食物繊維', '${target.fiberMin.toInt()} g以上'),

                    const SizedBox(height: 16),
                    // ミネラル
                    _buildNutrientSection(context, 'ミネラル'),
                    _buildNutrientInfoRow('ナトリウム', '${target.sodiumMax.toInt()} mg以下'),
                    _buildNutrientInfoRow('カリウム', '${target.potassiumMin.toInt()} mg以上'),
                    _buildNutrientInfoRow('カルシウム', '${target.calciumMin.toInt()} mg以上'),
                    _buildNutrientInfoRow('マグネシウム', '${target.magnesiumMin.toInt()} mg以上'),
                    _buildNutrientInfoRow('鉄', '${target.ironMin} mg以上'),
                    _buildNutrientInfoRow('亜鉛', '${target.zincMin.toInt()} mg以上'),

                    const SizedBox(height: 16),
                    // 脂溶性ビタミン
                    _buildNutrientSection(context, '脂溶性ビタミン'),
                    _buildNutrientInfoRow('ビタミンA', '${target.vitaminAMin.toInt()} μgRAE以上'),
                    _buildNutrientInfoRow('ビタミンD', '${target.vitaminDMin} μg以上'),
                    _buildNutrientInfoRow('ビタミンE', '${target.vitaminEMin} mg以上'),
                    _buildNutrientInfoRow('ビタミンK', '${target.vitaminKMin.toInt()} μg以上'),

                    const SizedBox(height: 16),
                    // 水溶性ビタミン
                    _buildNutrientSection(context, '水溶性ビタミン'),
                    _buildNutrientInfoRow('ビタミンB1', '${target.vitaminB1Min} mg以上'),
                    _buildNutrientInfoRow('ビタミンB2', '${target.vitaminB2Min} mg以上'),
                    _buildNutrientInfoRow('ビタミンB6', '${target.vitaminB6Min} mg以上'),
                    _buildNutrientInfoRow('ビタミンB12', '${target.vitaminB12Min} μg以上'),
                    _buildNutrientInfoRow('ナイアシン', '${target.niacinMin} mgNE以上'),
                    _buildNutrientInfoRow('パントテン酸', '${target.pantothenicAcidMin} mg以上'),
                    _buildNutrientInfoRow('ビオチン', '${target.biotinMin.toInt()} μg以上'),
                    _buildNutrientInfoRow('葉酸', '${target.folateMin.toInt()} μg以上'),
                    _buildNutrientInfoRow('ビタミンC', '${target.vitaminCMin.toInt()} mg以上'),

                    const SizedBox(height: 24),
                    Text(
                      '※ これらの値は厚生労働省の「日本人の食事摂取基準（2020年版）」に基づく推奨値です。',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Theme.of(context).colorScheme.outline,
                          ),
                    ),
                    const SizedBox(height: 32),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildNutrientSection(BuildContext context, String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        title,
        style: Theme.of(context).textTheme.titleSmall?.copyWith(
              color: Theme.of(context).colorScheme.primary,
            ),
      ),
    );
  }

  Widget _buildNutrientInfoRow(String name, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(name),
          Text(value, style: const TextStyle(fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildAllergenSettings(BuildContext context, WidgetRef ref, SettingsState settingsState) {
    final count = settingsState.excludedAllergens.length;
    final displayText = count == 0
        ? 'なし'
        : settingsState.excludedAllergens.map((a) => a.displayName).join(', ');

    return ListTile(
      leading: const Icon(Icons.warning_amber),
      title: const Text('除外するアレルゲン'),
      subtitle: Text(
        displayText,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (count > 0)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.errorContainer,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                '$count件',
                style: TextStyle(
                  fontSize: 12,
                  color: Theme.of(context).colorScheme.onErrorContainer,
                ),
              ),
            ),
          const SizedBox(width: 4),
          const Icon(Icons.chevron_right),
        ],
      ),
      onTap: () => _showAllergenModal(context, ref),
    );
  }

  void _showAllergenModal(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => Consumer(
        builder: (context, ref, _) {
          final settingsState = ref.watch(settingsNotifierProvider);
          return DraggableScrollableSheet(
            initialChildSize: 0.7,
            minChildSize: 0.4,
            maxChildSize: 0.9,
            expand: false,
            builder: (context, scrollController) => SafeArea(
              child: Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        const Expanded(
                          child: Text(
                            'アレルゲン除外',
                            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                          ),
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
                      '選択したアレルゲンを含む食材が使われた料理を除外します',
                      style: TextStyle(fontSize: 13, color: Colors.grey),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Expanded(
                    child: ListView(
                      controller: scrollController,
                      children: [
                        // 特定原材料8品目
                        _buildAllergenSectionHeader(context, '特定原材料 8品目'),
                        ...Allergen.requiredAllergens.map((allergen) {
                          final isSelected = settingsState.excludedAllergens.contains(allergen);
                          return CheckboxListTile(
                            title: Text(allergen.displayName),
                            value: isSelected,
                            activeColor: Theme.of(context).colorScheme.error,
                            onChanged: (_) {
                              ref.read(settingsNotifierProvider.notifier).toggleAllergen(allergen);
                            },
                          );
                        }),
                        const SizedBox(height: 16),
                        // 準特定原材料20品目
                        _buildAllergenSectionHeader(context, '準特定原材料 20品目'),
                        ...Allergen.recommendedAllergens.map((allergen) {
                          final isSelected = settingsState.excludedAllergens.contains(allergen);
                          return CheckboxListTile(
                            title: Text(allergen.displayName),
                            value: isSelected,
                            activeColor: Theme.of(context).colorScheme.error,
                            onChanged: (_) {
                              ref.read(settingsNotifierProvider.notifier).toggleAllergen(allergen);
                            },
                          );
                        }),
                        const SizedBox(height: 16),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildAllergenSectionHeader(BuildContext context, String title) {
    return Container(
      color: Theme.of(context).colorScheme.surfaceContainerHighest,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Text(
        title,
        style: TextStyle(
          fontWeight: FontWeight.bold,
          color: Theme.of(context).colorScheme.primary,
        ),
      ),
    );
  }

  Widget _buildResetButton(BuildContext context, WidgetRef ref) {
    return ListTile(
      leading: const Icon(Icons.restore),
      title: const Text('設定をリセット'),
      subtitle: const Text('すべての設定を初期値に戻します'),
      onTap: () => _showResetConfirmDialog(context, ref),
    );
  }

  void _showResetConfirmDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('設定をリセット'),
        content: const Text('すべての設定を初期値に戻しますか？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('キャンセル'),
          ),
          FilledButton(
            onPressed: () {
              ref.read(settingsNotifierProvider.notifier).resetSettings();
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('設定をリセットしました')),
              );
            },
            child: const Text('リセット'),
          ),
        ],
      ),
    );
  }

  Widget _buildAppInfo(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        children: [
          Text(
            '栄養最適化メニュー',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 4),
          Text(
            'バージョン 1.0.0',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.outline,
                ),
          ),
        ],
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
