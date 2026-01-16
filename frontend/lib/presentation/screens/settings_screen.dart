import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/settings_provider.dart';

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
          // 栄養目標セクション
          _buildSectionHeader(context, '栄養目標'),
          _buildOtherNutrientsSetting(context, settingsState),
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

  Widget _buildOtherNutrientsSetting(BuildContext context, SettingsState settingsState) {
    return ListTile(
      leading: const Icon(Icons.science),
      title: const Text('栄養素目標一覧'),
      subtitle: const Text('厚生労働省の食事摂取基準に基づく推奨値'),
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
                    _buildNutrientInfoRow('カロリー', '${target.caloriesMin.toInt()} - ${target.caloriesMax.toInt()} kcal'),
                    _buildNutrientInfoRow('タンパク質', '${target.proteinMin.toInt()} - ${target.proteinMax.toInt()} g'),
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
}
