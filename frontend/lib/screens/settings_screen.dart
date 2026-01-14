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
