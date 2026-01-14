import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/menu_provider.dart';
import '../models/dish.dart';
import '../models/menu_plan.dart';
import '../modals/dish_detail_modal.dart';

/// 献立カレンダー画面
class CalendarScreen extends StatefulWidget {
  const CalendarScreen({super.key});

  @override
  State<CalendarScreen> createState() => _CalendarScreenState();
}

class _CalendarScreenState extends State<CalendarScreen> {
  bool _isWeekView = true; // true: 週表示, false: 月表示
  final DateTime _startDate = DateTime.now();

  // ドラッグ中の情報
  _DragData? _dragData;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('献立カレンダー'),
        backgroundColor: const Color(0xFF2196F3),
        foregroundColor: Colors.white,
      ),
      body: Consumer<MenuProvider>(
        builder: (context, menuProvider, child) {
          if (!menuProvider.hasPlan) {
            return _buildEmptyState(context);
          }

          final plan = menuProvider.currentPlan!;
          return Column(
            children: [
              // 週/月表示トグル
              _buildViewToggle(),
              // ヒント
              _buildHint(),
              const Divider(height: 1),
              // 献立リスト
              Expanded(
                child: _isWeekView
                    ? _buildWeekView(context, plan, menuProvider)
                    : _buildMonthView(context, plan, menuProvider),
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

  Widget _buildViewToggle() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          Expanded(
            child: SegmentedButton<bool>(
              segments: const [
                ButtonSegment(value: true, label: Text('週表示')),
                ButtonSegment(value: false, label: Text('月表示')),
              ],
              selected: {_isWeekView},
              onSelectionChanged: (selected) {
                setState(() {
                  _isWeekView = selected.first;
                });
              },
              style: ButtonStyle(
                backgroundColor: WidgetStateProperty.resolveWith((states) {
                  if (states.contains(WidgetState.selected)) {
                    return const Color(0xFF2196F3);
                  }
                  return null;
                }),
                foregroundColor: WidgetStateProperty.resolveWith((states) {
                  if (states.contains(WidgetState.selected)) {
                    return Colors.white;
                  }
                  return null;
                }),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHint() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Text(
        '長押し→ドラッグで入れ替え',
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.outline,
            ),
        textAlign: TextAlign.center,
      ),
    );
  }

  // ========== 週表示 ==========
  Widget _buildWeekView(
    BuildContext context,
    MultiDayMenuPlan plan,
    MenuProvider menuProvider,
  ) {
    return ListView.builder(
      padding: const EdgeInsets.only(bottom: 32),
      itemCount: plan.days,
      itemBuilder: (context, index) {
        final dayPlan = plan.dailyPlans[index];
        return _buildDaySection(context, dayPlan, menuProvider);
      },
    );
  }

  Widget _buildDaySection(
    BuildContext context,
    DailyMealAssignment dayPlan,
    MenuProvider menuProvider,
  ) {
    final date = _startDate.add(Duration(days: dayPlan.day - 1));
    final dateStr = _formatDate(date);
    final achievement = dayPlan.achievementRate['calories'] ?? 0;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 日付ヘッダー
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          color: _getDayHeaderColor(dayPlan.day),
          child: Row(
            children: [
              Text(
                dateStr,
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: _getDayHeaderTextColor(dayPlan.day),
                    ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: _getAchievementColor(achievement).withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  '${achievement.toInt()}%',
                  style: TextStyle(
                    fontSize: 12,
                    color: _getAchievementColor(achievement),
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
        ),
        // 食事カード
        _buildMealCards(context, dayPlan, MealType.breakfast, '朝食', menuProvider),
        _buildMealCards(context, dayPlan, MealType.lunch, '昼食', menuProvider),
        _buildMealCards(context, dayPlan, MealType.dinner, '夕食', menuProvider),
        const SizedBox(height: 8),
      ],
    );
  }

  Widget _buildMealCards(
    BuildContext context,
    DailyMealAssignment dayPlan,
    MealType mealType,
    String mealLabel,
    MenuProvider menuProvider,
  ) {
    final dishes = dayPlan.getMealDishes(mealType);
    if (dishes.isEmpty) return const SizedBox.shrink();

    return Column(
      children: dishes.asMap().entries.map((entry) {
        final index = entry.key;
        final portion = entry.value;
        return _buildDraggableMealCard(
          context,
          dayPlan.day,
          mealType,
          index,
          portion,
          menuProvider,
        );
      }).toList(),
    );
  }

  Widget _buildDraggableMealCard(
    BuildContext context,
    int day,
    MealType mealType,
    int index,
    DishPortion portion,
    MenuProvider menuProvider,
  ) {
    final dragData = _DragData(day: day, mealType: mealType, index: index, portion: portion);
    final isDragging = _dragData?.portion.dish.id == portion.dish.id;

    return DragTarget<_DragData>(
      onWillAcceptWithDetails: (details) {
        return details.data.portion.dish.id != portion.dish.id;
      },
      onAcceptWithDetails: (details) {
        // 入れ替え実行
        menuProvider.swapDishes(
          day1: details.data.day,
          meal1: details.data.mealType,
          index1: details.data.index,
          day2: day,
          meal2: mealType,
          index2: index,
        );
        setState(() {
          _dragData = null;
        });
      },
      builder: (context, candidateData, rejectedData) {
        final isDropTarget = candidateData.isNotEmpty;

        return LongPressDraggable<_DragData>(
          data: dragData,
          onDragStarted: () {
            setState(() {
              _dragData = dragData;
            });
          },
          onDragEnd: (_) {
            setState(() {
              _dragData = null;
            });
          },
          feedback: Material(
            elevation: 8,
            borderRadius: BorderRadius.circular(8),
            child: SizedBox(
              width: MediaQuery.of(context).size.width - 48,
              child: _DraggingCard(portion: portion),
            ),
          ),
          childWhenDragging: Opacity(
            opacity: 0.3,
            child: _MealCardWithHandle(
              portion: portion,
              isDropTarget: false,
              onTap: () => _showDishDetail(context, portion),
            ),
          ),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(8),
              border: isDropTarget
                  ? Border.all(color: const Color(0xFF2196F3), width: 2)
                  : null,
              color: isDropTarget
                  ? const Color(0xFF2196F3).withValues(alpha: 0.1)
                  : null,
            ),
            child: _MealCardWithHandle(
              portion: portion,
              isDropTarget: isDropTarget,
              isDragging: isDragging,
              onTap: () => _showDishDetail(context, portion),
            ),
          ),
        );
      },
    );
  }

  // ========== 月表示（簡易版） ==========
  Widget _buildMonthView(
    BuildContext context,
    MultiDayMenuPlan plan,
    MenuProvider menuProvider,
  ) {
    return GridView.builder(
      padding: const EdgeInsets.all(16),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 7,
        mainAxisSpacing: 8,
        crossAxisSpacing: 8,
        childAspectRatio: 0.8,
      ),
      itemCount: plan.days,
      itemBuilder: (context, index) {
        final dayPlan = plan.dailyPlans[index];
        final date = _startDate.add(Duration(days: dayPlan.day - 1));
        final achievement = dayPlan.achievementRate['calories'] ?? 0;

        return InkWell(
          onTap: () {
            setState(() {
              _isWeekView = true;
            });
          },
          borderRadius: BorderRadius.circular(8),
          child: Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(8),
              color: Theme.of(context).colorScheme.surfaceContainerHighest,
              border: Border.all(
                color: _getAchievementColor(achievement).withValues(alpha: 0.5),
              ),
            ),
            padding: const EdgeInsets.all(4),
            child: Column(
              children: [
                Text(
                  '${date.day}',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                Text(
                  _getWeekdayShort(date),
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                  decoration: BoxDecoration(
                    color: _getAchievementColor(achievement).withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    '${achievement.toInt()}%',
                    style: TextStyle(
                      fontSize: 10,
                      color: _getAchievementColor(achievement),
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  // ========== ヘルパー ==========
  String _formatDate(DateTime date) {
    final weekdays = ['月', '火', '水', '木', '金', '土', '日'];
    final weekday = weekdays[date.weekday - 1];
    return '${date.month}月${date.day}日（$weekday）';
  }

  String _getWeekdayShort(DateTime date) {
    final weekdays = ['月', '火', '水', '木', '金', '土', '日'];
    return weekdays[date.weekday - 1];
  }

  Color _getDayHeaderColor(int day) {
    final colors = [
      const Color(0xFFE3F2FD), // 青
      const Color(0xFFFFF3E0), // オレンジ
      const Color(0xFFE8F5E9), // 緑
      const Color(0xFFFCE4EC), // ピンク
      const Color(0xFFF3E5F5), // 紫
      const Color(0xFFE0F7FA), // シアン
      const Color(0xFFFFFDE7), // 黄
    ];
    return colors[(day - 1) % colors.length];
  }

  Color _getDayHeaderTextColor(int day) {
    final colors = [
      const Color(0xFF1565C0),
      const Color(0xFFE65100),
      const Color(0xFF2E7D32),
      const Color(0xFFC2185B),
      const Color(0xFF7B1FA2),
      const Color(0xFF00838F),
      const Color(0xFFF57F17),
    ];
    return colors[(day - 1) % colors.length];
  }

  Color _getAchievementColor(double value) {
    if (value >= 90) return Colors.green;
    if (value >= 70) return Colors.orange;
    return Colors.red;
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

/// ドラッグデータ
class _DragData {
  final int day;
  final MealType mealType;
  final int index;
  final DishPortion portion;

  _DragData({
    required this.day,
    required this.mealType,
    required this.index,
    required this.portion,
  });
}

/// ドラッグハンドル付きの料理カード
class _MealCardWithHandle extends StatelessWidget {
  final DishPortion portion;
  final bool isDropTarget;
  final bool isDragging;
  final VoidCallback onTap;

  const _MealCardWithHandle({
    required this.portion,
    required this.onTap,
    this.isDropTarget = false,
    this.isDragging = false,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.zero,
      color: isDropTarget
          ? const Color(0xFFE3F2FD)
          : isDragging
              ? Colors.grey.shade200
              : null,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          child: Row(
            children: [
              // 料理情報
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${_getMealEmoji(portion.dish.mealTypes.firstOrNull ?? 'dinner')} ${portion.dish.name}',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                    Text(
                      '${portion.calories.toInt()} kcal',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Theme.of(context).colorScheme.outline,
                          ),
                    ),
                  ],
                ),
              ),
              // ドラッグハンドル
              Icon(
                Icons.drag_handle,
                color: isDropTarget
                    ? const Color(0xFF2196F3)
                    : Theme.of(context).colorScheme.outline.withValues(alpha: 0.5),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _getMealEmoji(String mealType) {
    switch (mealType) {
      case 'breakfast':
        return '🌅';
      case 'lunch':
        return '☀️';
      case 'dinner':
        return '🌙';
      default:
        return '🍽️';
    }
  }
}

/// ドラッグ中のフィードバックカード
class _DraggingCard extends StatelessWidget {
  final DishPortion portion;

  const _DraggingCard({required this.portion});

  @override
  Widget build(BuildContext context) {
    return Card(
      color: const Color(0xFFE3F2FD),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    '🌙 ${portion.dish.name}',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  Text(
                    '${portion.calories.toInt()} kcal ← ドラッグ中',
                    style: const TextStyle(
                      fontSize: 12,
                      color: Color(0xFF1565C0),
                    ),
                  ),
                ],
              ),
            ),
            const Icon(Icons.drag_handle, color: Color(0xFF2196F3)),
          ],
        ),
      ),
    );
  }
}
