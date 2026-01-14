import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/settings_provider.dart';
import '../models/settings.dart';

/// 設定画面
class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('設定'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Consumer<SettingsProvider>(
        builder: (context, settings, child) {
          if (settings.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          return ListView(
            children: [
              // デフォルト設定セクション
              _buildSectionHeader(context, 'デフォルト設定'),
              _buildDaysSetting(context, settings),
              _buildPeopleSetting(context, settings),
              _buildBatchCookingSetting(context, settings),
              const Divider(),

              // 栄養目標セクション
              _buildSectionHeader(context, '栄養目標'),
              _buildCaloriesSetting(context, settings),
              _buildProteinSetting(context, settings),
              _buildOtherNutrientsSetting(context, settings),
              const Divider(),

              // アレルゲン除外セクション
              _buildSectionHeader(context, 'アレルゲン除外'),
              _buildAllergenSettings(context, settings),
              const Divider(),

              // その他
              _buildSectionHeader(context, 'その他'),
              _buildResetButton(context, settings),
              const SizedBox(height: 32),

              // アプリ情報
              _buildAppInfo(context),
              const SizedBox(height: 32),
            ],
          );
        },
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

  Widget _buildDaysSetting(BuildContext context, SettingsProvider settings) {
    return ListTile(
      leading: const Icon(Icons.calendar_today),
      title: const Text('デフォルト日数'),
      subtitle: Text('${settings.defaultDays}日分'),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          IconButton(
            icon: const Icon(Icons.remove_circle_outline),
            onPressed: settings.defaultDays > 1
                ? () => settings.setDefaultDays(settings.defaultDays - 1)
                : null,
          ),
          Text(
            '${settings.defaultDays}',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          IconButton(
            icon: const Icon(Icons.add_circle_outline),
            onPressed: settings.defaultDays < 7
                ? () => settings.setDefaultDays(settings.defaultDays + 1)
                : null,
          ),
        ],
      ),
    );
  }

  Widget _buildPeopleSetting(BuildContext context, SettingsProvider settings) {
    return ListTile(
      leading: const Icon(Icons.people),
      title: const Text('デフォルト人数'),
      subtitle: Text('${settings.defaultPeople}人分'),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          IconButton(
            icon: const Icon(Icons.remove_circle_outline),
            onPressed: settings.defaultPeople > 1
                ? () => settings.setDefaultPeople(settings.defaultPeople - 1)
                : null,
          ),
          Text(
            '${settings.defaultPeople}',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          IconButton(
            icon: const Icon(Icons.add_circle_outline),
            onPressed: settings.defaultPeople < 6
                ? () => settings.setDefaultPeople(settings.defaultPeople + 1)
                : null,
          ),
        ],
      ),
    );
  }

  Widget _buildBatchCookingSetting(
      BuildContext context, SettingsProvider settings) {
    return SwitchListTile(
      secondary: const Icon(Icons.kitchen),
      title: const Text('作り置き優先'),
      subtitle: const Text('調理回数を減らして効率化'),
      value: settings.preferBatchCooking,
      onChanged: settings.setPreferBatchCooking,
    );
  }

  Widget _buildCaloriesSetting(
      BuildContext context, SettingsProvider settings) {
    final target = settings.nutrientTarget;

    return ListTile(
      leading: const Icon(Icons.local_fire_department),
      title: const Text('カロリー目標'),
      subtitle: Text(
          '${target.caloriesMin.toInt()} - ${target.caloriesMax.toInt()} kcal'),
      trailing: const Icon(Icons.chevron_right),
      onTap: () => _showCaloriesDialog(context, settings),
    );
  }

  void _showCaloriesDialog(BuildContext context, SettingsProvider settings) {
    final target = settings.nutrientTarget;
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
                settings.setCaloriesRange(minValue, maxValue);
                Navigator.pop(context);
              },
              child: const Text('保存'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProteinSetting(
      BuildContext context, SettingsProvider settings) {
    final target = settings.nutrientTarget;

    return ListTile(
      leading: const Icon(Icons.fitness_center),
      title: const Text('タンパク質目標'),
      subtitle: Text(
          '${target.proteinMin.toInt()} - ${target.proteinMax.toInt()} g'),
      trailing: const Icon(Icons.chevron_right),
      onTap: () => _showProteinDialog(context, settings),
    );
  }

  void _showProteinDialog(BuildContext context, SettingsProvider settings) {
    final target = settings.nutrientTarget;
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
                settings.setProteinRange(minValue, maxValue);
                Navigator.pop(context);
              },
              child: const Text('保存'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOtherNutrientsSetting(
      BuildContext context, SettingsProvider settings) {
    return ListTile(
      leading: const Icon(Icons.science),
      title: const Text('その他栄養素'),
      subtitle: const Text('脂質・炭水化物・食物繊維など'),
      trailing: const Icon(Icons.chevron_right),
      onTap: () => _showOtherNutrientsDialog(context, settings),
    );
  }

  void _showOtherNutrientsDialog(
      BuildContext context, SettingsProvider settings) {
    final target = settings.nutrientTarget;

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('その他栄養素目標'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildNutrientInfoRow('脂質', '${target.fatMin.toInt()} - ${target.fatMax.toInt()} g'),
              _buildNutrientInfoRow('炭水化物', '${target.carbohydrateMin.toInt()} - ${target.carbohydrateMax.toInt()} g'),
              _buildNutrientInfoRow('食物繊維', '${target.fiberMin.toInt()} g以上'),
              _buildNutrientInfoRow('ナトリウム', '${target.sodiumMax.toInt()} mg以下'),
              _buildNutrientInfoRow('カルシウム', '${target.calciumMin.toInt()} mg以上'),
              _buildNutrientInfoRow('鉄', '${target.ironMin} mg以上'),
              _buildNutrientInfoRow('ビタミンA', '${target.vitaminAMin.toInt()} μgRAE以上'),
              _buildNutrientInfoRow('ビタミンC', '${target.vitaminCMin.toInt()} mg以上'),
              _buildNutrientInfoRow('ビタミンD', '${target.vitaminDMin} μg以上'),
              const SizedBox(height: 16),
              Text(
                '※ これらの値は厚生労働省の「日本人の食事摂取基準」に基づく推奨値です。',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.outline,
                    ),
              ),
            ],
          ),
        ),
        actions: [
          FilledButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('閉じる'),
          ),
        ],
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

  Widget _buildAllergenSettings(
      BuildContext context, SettingsProvider settings) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Wrap(
        spacing: 8,
        runSpacing: 8,
        children: Allergen.values.map((allergen) {
          final isSelected = settings.excludedAllergens.contains(allergen);
          return FilterChip(
            label: Text(allergen.displayName),
            selected: isSelected,
            onSelected: (_) => settings.toggleAllergen(allergen),
            avatar: isSelected
                ? const Icon(Icons.block, size: 18)
                : const Icon(Icons.check_circle_outline, size: 18),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildResetButton(BuildContext context, SettingsProvider settings) {
    return ListTile(
      leading: const Icon(Icons.restore),
      title: const Text('設定をリセット'),
      subtitle: const Text('すべての設定を初期値に戻します'),
      onTap: () => _showResetConfirmDialog(context, settings),
    );
  }

  void _showResetConfirmDialog(
      BuildContext context, SettingsProvider settings) {
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
              settings.resetSettings();
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
}
