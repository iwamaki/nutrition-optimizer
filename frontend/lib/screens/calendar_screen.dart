import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/menu_provider.dart';
import '../models/dish.dart';
import '../models/menu_plan.dart';
import '../widgets/meal_card_new.dart';

/// 献立カレンダー画面
class CalendarScreen extends StatefulWidget {
  const CalendarScreen({super.key});

  @override
  State<CalendarScreen> createState() => _CalendarScreenState();
}

class _CalendarScreenState extends State<CalendarScreen> {
  int _selectedDay = 1;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('週間献立'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Consumer<MenuProvider>(
        builder: (context, menuProvider, child) {
          if (!menuProvider.hasPlan) {
            return _buildEmptyState(context);
          }

          final plan = menuProvider.currentPlan!;
          return Column(
            children: [
              // 日付セレクター
              _buildDaySelector(plan),
              const Divider(height: 1),
              // 選択された日の献立
              Expanded(
                child: _buildDayPlan(plan, _selectedDay),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.calendar_month_outlined,
            size: 80,
            color: Theme.of(context).colorScheme.outline,
          ),
          const SizedBox(height: 16),
          Text(
            '献立がありません',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 8),
          Text(
            'ホーム画面から献立を生成してください',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(context).colorScheme.outline,
                ),
          ),
        ],
      ),
    );
  }

  Widget _buildDaySelector(MultiDayMenuPlan plan) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Row(
          children: List.generate(plan.days, (index) {
            final day = index + 1;
            final isSelected = day == _selectedDay;
            final dayPlan = plan.dailyPlans.firstWhere(
              (p) => p.day == day,
              orElse: () => plan.dailyPlans.first,
            );
            final achievement = dayPlan.achievementRate['calories'] ?? 0;

            return Padding(
              padding: const EdgeInsets.only(right: 8),
              child: _DayChip(
                day: day,
                isSelected: isSelected,
                achievement: achievement,
                onTap: () {
                  setState(() {
                    _selectedDay = day;
                  });
                },
              ),
            );
          }),
        ),
      ),
    );
  }

  Widget _buildDayPlan(MultiDayMenuPlan plan, int day) {
    final dayPlan = plan.dailyPlans.firstWhere(
      (p) => p.day == day,
      orElse: () => plan.dailyPlans.first,
    );

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 栄養達成率サマリー
          _buildAchievementSummary(dayPlan),
          const SizedBox(height: 16),

          // 朝食
          _buildMealSection('朝食', Icons.wb_sunny_outlined, dayPlan.breakfast),
          const SizedBox(height: 16),

          // 昼食
          _buildMealSection('昼食', Icons.wb_cloudy_outlined, dayPlan.lunch),
          const SizedBox(height: 16),

          // 夕食
          _buildMealSection('夕食', Icons.nightlight_outlined, dayPlan.dinner),
          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildAchievementSummary(DailyMealAssignment dayPlan) {
    final calories = dayPlan.achievementRate['calories'] ?? 0;
    final protein = dayPlan.achievementRate['protein'] ?? 0;
    final fat = dayPlan.achievementRate['fat'] ?? 0;
    final carbs = dayPlan.achievementRate['carbohydrate'] ?? 0;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '$_selectedDay日目の栄養達成率',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildNutrientBadge('カロリー', calories, Colors.orange),
                _buildNutrientBadge('タンパク質', protein, Colors.red),
                _buildNutrientBadge('脂質', fat, Colors.amber),
                _buildNutrientBadge('炭水化物', carbs, Colors.blue),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNutrientBadge(String label, double rate, Color color) {
    return Column(
      children: [
        Stack(
          alignment: Alignment.center,
          children: [
            SizedBox(
              width: 50,
              height: 50,
              child: CircularProgressIndicator(
                value: (rate / 100).clamp(0, 1),
                backgroundColor: color.withValues(alpha: 0.2),
                valueColor: AlwaysStoppedAnimation(color),
                strokeWidth: 4,
              ),
            ),
            Text(
              '${rate.toInt()}%',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        Text(label, style: const TextStyle(fontSize: 11)),
      ],
    );
  }

  Widget _buildMealSection(
    String title,
    IconData icon,
    List<DishPortion> dishes,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, size: 20),
            const SizedBox(width: 8),
            Text(
              title,
              style: Theme.of(context).textTheme.titleMedium,
            ),
          ],
        ),
        const SizedBox(height: 8),
        if (dishes.isEmpty)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                '料理がありません',
                style: TextStyle(
                  color: Theme.of(context).colorScheme.outline,
                ),
              ),
            ),
          )
        else
          ...dishes.map((portion) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: MealCardNew(portion: portion),
              )),
      ],
    );
  }
}

/// 日付チップ
class _DayChip extends StatelessWidget {
  final int day;
  final bool isSelected;
  final double achievement;
  final VoidCallback onTap;

  const _DayChip({
    required this.day,
    required this.isSelected,
    required this.achievement,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    Color getAchievementColor() {
      if (achievement >= 90) return Colors.green;
      if (achievement >= 70) return Colors.orange;
      return Colors.red;
    }

    return Material(
      color: isSelected ? colorScheme.primaryContainer : colorScheme.surface,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: isSelected
                  ? colorScheme.primary
                  : colorScheme.outline.withValues(alpha: 0.3),
            ),
          ),
          child: Column(
            children: [
              Text(
                '$day日目',
                style: TextStyle(
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                  color: isSelected ? colorScheme.primary : null,
                ),
              ),
              const SizedBox(height: 4),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: getAchievementColor().withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  '${achievement.toInt()}%',
                  style: TextStyle(
                    fontSize: 11,
                    color: getAchievementColor(),
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
