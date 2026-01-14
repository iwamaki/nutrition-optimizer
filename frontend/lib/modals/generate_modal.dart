import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/menu_provider.dart';
import '../providers/settings_provider.dart';
import '../providers/shopping_provider.dart';
import '../models/dish.dart';
import '../models/settings.dart';
import '../models/menu_plan.dart';
import '../widgets/nutrient_progress_bar.dart';

/// 献立生成モーダル（3ステップウィザード）
class GenerateModal extends StatefulWidget {
  const GenerateModal({super.key});

  @override
  State<GenerateModal> createState() => _GenerateModalState();
}

class _GenerateModalState extends State<GenerateModal> {
  int _currentStep = 0;

  // Step1: 設定
  late int _days;
  late int _people;
  late Set<Allergen> _excludedAllergens;
  late bool _preferBatchCooking;

  // Step3: 生成結果
  MultiDayMenuPlan? _generatedPlan;
  bool _isGenerating = false;
  String? _error;

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
    final titles = ['設定', '食材選択', '献立確認'];
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
          _buildStepDot(0, '設定'),
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

  // ========== Step 1: 設定 ==========
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
                Text('期間', style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: 12),
                Row(
                  children: List.generate(7, (index) {
                    final day = index + 1;
                    final isSelected = _days == day;
                    return Expanded(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 2),
                        child: ChoiceChip(
                          label: Text('$day'),
                          selected: isSelected,
                          onSelected: (_) => setState(() => _days = day),
                        ),
                      ),
                    );
                  }),
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
                Text('人数', style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: 12),
                Row(
                  children: List.generate(6, (index) {
                    final people = index + 1;
                    final isSelected = _people == people;
                    return Expanded(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 2),
                        child: ChoiceChip(
                          label: Text('$people'),
                          selected: isSelected,
                          onSelected: (_) => setState(() => _people = people),
                        ),
                      ),
                    );
                  }),
                ),
                const SizedBox(height: 4),
                Text(
                  '$_people人分で計算',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Theme.of(context).colorScheme.outline,
                      ),
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
                Text(
                  'アレルゲン除外',
                  style: Theme.of(context).textTheme.titleSmall,
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
            title: const Text('作り置き優先'),
            subtitle: const Text('調理回数を減らして効率化'),
            value: _preferBatchCooking,
            onChanged: (value) => setState(() => _preferBatchCooking = value),
          ),
        ),
      ],
    );
  }

  // ========== Step 2: 食材選択（簡略版） ==========
  Widget _buildStep2Ingredients(ScrollController scrollController) {
    return ListView(
      controller: scrollController,
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              children: [
                Icon(
                  Icons.kitchen,
                  size: 64,
                  color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.5),
                ),
                const SizedBox(height: 16),
                Text(
                  '手持ち食材の選択',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Text(
                  '現在は全ての食材を使用して最適化します。\n手持ち食材の指定機能は今後追加予定です。',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Theme.of(context).colorScheme.outline,
                      ),
                ),
                const SizedBox(height: 24),
                FilledButton.tonal(
                  onPressed: null,
                  child: const Text('食材を検索（準備中）'),
                ),
              ],
            ),
          ),
        ),
      ],
    );
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
            Text('エラーが発生しました'),
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
        // 栄養達成率サマリー
        _buildAchievementCard(plan),
        const SizedBox(height: 16),

        // 日別献立
        ...plan.dailyPlans.map((dayPlan) => _buildDayCard(dayPlan)),

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
              label: '脂質',
              value: plan.overallAchievement['fat'] ?? 0,
              color: Colors.amber,
            ),
            const SizedBox(height: 8),
            NutrientProgressBar(
              label: '炭水化物',
              value: plan.overallAchievement['carbohydrate'] ?? 0,
              color: Colors.blue,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDayCard(DailyMealAssignment dayPlan) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ExpansionTile(
        title: Text('${dayPlan.day}日目'),
        subtitle: Text(
          '${dayPlan.totalCalories.toInt()} kcal',
          style: TextStyle(color: Theme.of(context).colorScheme.outline),
        ),
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: _getAchievementColor(dayPlan.achievementRate['calories'] ?? 0)
                .withValues(alpha: 0.2),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(
            '${(dayPlan.achievementRate['calories'] ?? 0).toInt()}%',
            style: TextStyle(
              fontSize: 12,
              color: _getAchievementColor(dayPlan.achievementRate['calories'] ?? 0),
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildMealList('朝食', dayPlan.breakfast),
                const SizedBox(height: 8),
                _buildMealList('昼食', dayPlan.lunch),
                const SizedBox(height: 8),
                _buildMealList('夕食', dayPlan.dinner),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMealList(String title, List<DishPortion> dishes) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: Theme.of(context).textTheme.labelMedium?.copyWith(
                color: Theme.of(context).colorScheme.primary,
              ),
        ),
        const SizedBox(height: 4),
        if (dishes.isEmpty)
          Text(
            '料理なし',
            style: TextStyle(color: Theme.of(context).colorScheme.outline),
          )
        else
          ...dishes.map((p) => Padding(
                padding: const EdgeInsets.only(left: 8, top: 2),
                child: Text('・${p.dish.name}'),
              )),
      ],
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
                child: const Text('戻る'),
              ),
            ),
          if (_currentStep > 0) const SizedBox(width: 16),
          Expanded(
            flex: 2,
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
        return '次へ';
      case 1:
        return '献立を生成';
      case 2:
        return _generatedPlan != null ? '確定' : '生成';
      default:
        return '次へ';
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
