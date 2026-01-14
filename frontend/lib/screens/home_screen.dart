import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/menu_provider.dart';
import '../providers/settings_provider.dart';
import '../providers/shopping_provider.dart';
import '../models/dish.dart';
import '../models/menu_plan.dart';
import '../widgets/meal_card_new.dart';
import '../widgets/nutrient_progress_bar.dart';
import '../modals/generate_modal.dart';
import '../modals/dish_detail_modal.dart';

/// ホーム画面
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedPeriod = 0; // 0: 今日, 1: 週間, 2: 月間

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('今日の献立'),
        backgroundColor: Theme.of(context).colorScheme.primary,
        foregroundColor: Theme.of(context).colorScheme.onPrimary,
      ),
      body: Consumer<MenuProvider>(
        builder: (context, menuProvider, child) {
          if (menuProvider.isLoading) {
            return _buildLoadingState();
          }

          if (menuProvider.error != null) {
            return _buildErrorState(context, menuProvider);
          }

          if (!menuProvider.hasPlan) {
            return _buildEmptyState(context);
          }

          return _buildContent(context, menuProvider);
        },
      ),
      floatingActionButton: Consumer<MenuProvider>(
        builder: (context, menuProvider, child) {
          return FloatingActionButton.extended(
            onPressed: menuProvider.isLoading
                ? null
                : () => _showGenerateModal(context),
            icon: const Icon(Icons.auto_awesome),
            label: Text(menuProvider.hasPlan ? '再生成' : '献立を生成'),
            backgroundColor: Theme.of(context).colorScheme.primary,
            foregroundColor: Theme.of(context).colorScheme.onPrimary,
          );
        },
      ),
    );
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

  Widget _buildErrorState(BuildContext context, MenuProvider menuProvider) {
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
              menuProvider.error!,
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
                menuProvider.clearError();
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

  Widget _buildContent(BuildContext context, MenuProvider menuProvider) {
    final plan = menuProvider.currentPlan!;
    final todayPlan = menuProvider.todayPlan;

    return RefreshIndicator(
      onRefresh: () async {
        final settings = context.read<SettingsProvider>();
        await menuProvider.generatePlan(target: settings.nutrientTarget);
        if (menuProvider.currentPlan != null) {
          context.read<ShoppingProvider>().updateFromPlan(menuProvider.currentPlan!);
        }
      },
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 期間切替 & 栄養達成率
            _buildPeriodToggle(),
            const SizedBox(height: 16),

            // 栄養達成率バー
            _buildNutrientProgress(plan, todayPlan),
            const SizedBox(height: 24),

            // 今日の献立
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
            ],
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
                  _selectedPeriod == 0 ? '今日の栄養達成率' : '${plan.days}日間の栄養達成率',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                _buildOverallBadge(achievement),
              ],
            ),
            const SizedBox(height: 16),
            NutrientProgressBar(
              label: 'カロリー',
              value: achievement['calories'] ?? 0,
              color: Colors.orange,
            ),
            const SizedBox(height: 8),
            NutrientProgressBar(
              label: 'タンパク質',
              value: achievement['protein'] ?? 0,
              color: Colors.red,
            ),
            const SizedBox(height: 8),
            NutrientProgressBar(
              label: '脂質',
              value: achievement['fat'] ?? 0,
              color: Colors.amber,
            ),
            const SizedBox(height: 8),
            NutrientProgressBar(
              label: '炭水化物',
              value: achievement['carbohydrate'] ?? 0,
              color: Colors.blue,
            ),
            const SizedBox(height: 8),
            NutrientProgressBar(
              label: '食物繊維',
              value: achievement['fiber'] ?? 0,
              color: Colors.green,
            ),
          ],
        ),
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
      builder: (context) => const GenerateModal(),
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
