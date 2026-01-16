import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/menu_provider.dart';
import '../providers/settings_provider.dart';
import '../providers/shopping_provider.dart';
import '../../domain/entities/dish.dart';
import '../../domain/entities/menu_plan.dart';
import '../../core/constants/nutrients.dart';
import '../widgets/meal_card_new.dart';
import '../widgets/nutrient_progress_bar.dart';
import '../modals/generate/generate_modal.dart';
import '../modals/dish_detail_modal.dart';

/// ホーム画面（Riverpod版）
class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  int _selectedPeriod = 0; // 0: 今日, 1: 週間, 2: 月間

  @override
  Widget build(BuildContext context) {
    final menuState = ref.watch(menuNotifierProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('今日の献立'),
        backgroundColor: Theme.of(context).colorScheme.primary,
        foregroundColor: Theme.of(context).colorScheme.onPrimary,
      ),
      body: _buildBody(context, menuState),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: menuState.isLoading
            ? null
            : () => _showGenerateModal(context),
        icon: const Icon(Icons.auto_awesome),
        label: Text(menuState.hasPlan ? '再生成' : '献立を生成'),
        backgroundColor: Theme.of(context).colorScheme.primary,
        foregroundColor: Theme.of(context).colorScheme.onPrimary,
      ),
    );
  }

  Widget _buildBody(BuildContext context, MenuState menuState) {
    if (menuState.isLoading) {
      return _buildLoadingState();
    }

    if (menuState.error != null) {
      return _buildErrorState(context, menuState);
    }

    if (!menuState.hasPlan) {
      return _buildEmptyState(context);
    }

    return _buildContent(context, menuState);
  }

  Widget _buildLoadingState() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(),
          SizedBox(height: 16),
          Text('献立を最適化中...'),
        ],
      ),
    );
  }

  Widget _buildErrorState(BuildContext context, MenuState menuState) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            Text(
              'エラーが発生しました',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(
              menuState.error!,
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Theme.of(context).colorScheme.outline,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'バックエンドが起動しているか確認してください',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () {
                ref.read(menuNotifierProvider.notifier).clearError();
              },
              icon: const Icon(Icons.close),
              label: const Text('閉じる'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.restaurant_menu,
            size: 100,
            color: Theme.of(context).colorScheme.outline.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 24),
          Text(
            '献立がありません',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 8),
          Text(
            '下のボタンから献立を生成してください',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(context).colorScheme.outline,
                ),
          ),
          const SizedBox(height: 80), // FAB用のスペース
        ],
      ),
    );
  }

  Widget _buildContent(BuildContext context, MenuState menuState) {
    final plan = menuState.currentPlan!;
    final todayPlan = menuState.todayPlan;

    return RefreshIndicator(
      onRefresh: () async {
        final settingsState = ref.read(settingsNotifierProvider);
        await ref.read(menuNotifierProvider.notifier).generatePlan(
              target: settingsState.nutrientTarget,
            );
        final newMenuState = ref.read(menuNotifierProvider);
        if (newMenuState.currentPlan != null) {
          ref.read(shoppingNotifierProvider.notifier).updateFromPlan(
                newMenuState.currentPlan!,
              );
        }
      },
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 今日の献立（上部に配置）
            if (todayPlan != null) ...[
              _buildMealSection(
                context,
                '朝食',
                Icons.wb_sunny,
                todayPlan.breakfast,
              ),
              const SizedBox(height: 16),
              _buildMealSection(
                context,
                '昼食',
                Icons.wb_cloudy,
                todayPlan.lunch,
              ),
              const SizedBox(height: 16),
              _buildMealSection(
                context,
                '夕食',
                Icons.nightlight_round,
                todayPlan.dinner,
              ),
              const SizedBox(height: 24),
            ],

            // 期間切替 & 栄養達成率（下部に配置、スクロールで表示）
            _buildPeriodToggle(),
            const SizedBox(height: 16),
            _buildNutrientProgress(plan, todayPlan),
            const SizedBox(height: 80), // FAB用のスペース
          ],
        ),
      ),
    );
  }

  Widget _buildPeriodToggle() {
    return Row(
      children: [
        Expanded(
          child: SegmentedButton<int>(
            segments: const [
              ButtonSegment(value: 0, label: Text('今日')),
              ButtonSegment(value: 1, label: Text('週間')),
            ],
            selected: {_selectedPeriod},
            onSelectionChanged: (selected) {
              setState(() {
                _selectedPeriod = selected.first;
              });
            },
          ),
        ),
      ],
    );
  }

  Widget _buildNutrientProgress(
    MultiDayMenuPlan plan,
    DailyMealAssignment? todayPlan,
  ) {
    final achievement = _selectedPeriod == 0
        ? todayPlan?.achievementRate ?? {}
        : plan.overallAchievement;

    final periodLabel = _selectedPeriod == 0
        ? '今日の栄養達成率'
        : '${plan.days}日間の栄養達成率';

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
                  periodLabel,
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                _buildOverallBadge(achievement),
              ],
            ),
            const SizedBox(height: 16),

            // エネルギー・三大栄養素
            _buildNutrientSectionHeader('エネルギー・三大栄養素'),
            const SizedBox(height: 8),
            _buildNutrientBars(basicNutrients, achievement),
            const SizedBox(height: 16),

            // ミネラル
            _buildNutrientSectionHeader('ミネラル'),
            const SizedBox(height: 8),
            _buildNutrientBars(mineralNutrients, achievement),
            const SizedBox(height: 16),

            // ビタミン
            _buildNutrientSectionHeader('ビタミン'),
            const SizedBox(height: 8),
            _buildNutrientBars(vitaminNutrients, achievement),
            const SizedBox(height: 16),

            // 出典表示
            const Divider(),
            const SizedBox(height: 8),
            Text(
              '栄養素データ: $nutrientDataSource',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.outline,
                    fontSize: 10,
                  ),
            ),
            const SizedBox(height: 2),
            Text(
              '栄養摂取基準: $nutrientStandardSource',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.outline,
                    fontSize: 10,
                  ),
            ),
          ],
        ),
      ),
    );
  }

  /// 栄養素リストからプログレスバーを生成
  Widget _buildNutrientBars(
    List<NutrientDefinition> nutrients,
    Map<String, double> achievement,
  ) {
    return Column(
      children: nutrients.asMap().entries.map((entry) {
        final idx = entry.key;
        final nutrient = entry.value;
        return Column(
          children: [
            if (idx > 0) const SizedBox(height: 8),
            NutrientProgressBar.fromDefinition(
              definition: nutrient,
              value: achievement[nutrient.key] ?? 0,
            ),
          ],
        );
      }).toList(),
    );
  }

  Widget _buildNutrientSectionHeader(String title) {
    return Text(
      title,
      style: Theme.of(context).textTheme.labelMedium?.copyWith(
            color: Theme.of(context).colorScheme.primary,
            fontWeight: FontWeight.bold,
          ),
    );
  }

  Widget _buildOverallBadge(Map<String, double> achievement) {
    if (achievement.isEmpty) return const SizedBox.shrink();

    final avg = achievement.values.reduce((a, b) => a + b) / achievement.length;
    final color = avg >= 90
        ? Colors.green
        : avg >= 70
            ? Colors.orange
            : Colors.red;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.2),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(
        '${avg.toInt()}%',
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _buildMealSection(
    BuildContext context,
    String title,
    IconData icon,
    List<DishPortion> dishes,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, size: 20, color: Theme.of(context).colorScheme.primary),
            const SizedBox(width: 8),
            Text(
              title,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const Spacer(),
            if (dishes.isNotEmpty)
              Text(
                '${_calculateMealCalories(dishes).toInt()} kcal',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.outline,
                    ),
              ),
          ],
        ),
        const SizedBox(height: 8),
        if (dishes.isEmpty)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Center(
                child: Text(
                  '料理がありません',
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.outline,
                  ),
                ),
              ),
            ),
          )
        else
          ...dishes.map((portion) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: MealCardNew(
                  portion: portion,
                  onTap: () => _showDishDetail(context, portion),
                ),
              )),
      ],
    );
  }

  double _calculateMealCalories(List<DishPortion> dishes) {
    return dishes.fold(0.0, (sum, p) => sum + p.calories);
  }

  void _showGenerateModal(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (context) => const GenerateModalNew(),
    );
  }

  void _showDishDetail(BuildContext context, DishPortion portion) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (context) => DishDetailModal(dish: portion.dish),
    );
  }
}
