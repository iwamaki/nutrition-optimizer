import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/menu_provider.dart';
import '../../domain/entities/dish.dart';
import '../../domain/entities/menu_plan.dart';
import '../modals/dish_detail_modal.dart';

/// 献立カレンダー画面（Riverpod版）
class CalendarScreen extends ConsumerStatefulWidget {
  const CalendarScreen({super.key});

  @override
  ConsumerState<CalendarScreen> createState() => _CalendarScreenState();
}

class _CalendarScreenState extends ConsumerState<CalendarScreen> {
  final DateTime _startDate = DateTime.now();

  // ドラッグ中の情報
  _DragData? _dragData;

  // スクロールコントローラー
  final ScrollController _horizontalScrollController = ScrollController();
  final ScrollController _verticalScrollController = ScrollController();

  // 自動スクロール用の設定
  static const double _scrollEdgeThreshold = 50.0; // 端からの距離
  static const double _scrollSpeed = 8.0; // スクロール速度

  @override
  void dispose() {
    _horizontalScrollController.dispose();
    _verticalScrollController.dispose();
    super.dispose();
  }

  /// ドラッグ中の自動スクロール処理
  void _handleDragAutoScroll(Offset globalPosition) {
    if (_dragData == null) return;

    final renderBox = context.findRenderObject() as RenderBox?;
    if (renderBox == null) return;

    final localPosition = renderBox.globalToLocal(globalPosition);
    final size = renderBox.size;

    // 横方向のスクロール
    if (_horizontalScrollController.hasClients) {
      if (localPosition.dx < _scrollEdgeThreshold) {
        // 左端に近い → 左にスクロール
        final newOffset = (_horizontalScrollController.offset - _scrollSpeed)
            .clamp(0.0, _horizontalScrollController.position.maxScrollExtent);
        _horizontalScrollController.jumpTo(newOffset);
      } else if (localPosition.dx > size.width - _scrollEdgeThreshold) {
        // 右端に近い → 右にスクロール
        final newOffset = (_horizontalScrollController.offset + _scrollSpeed)
            .clamp(0.0, _horizontalScrollController.position.maxScrollExtent);
        _horizontalScrollController.jumpTo(newOffset);
      }
    }

    // 縦方向のスクロール
    if (_verticalScrollController.hasClients) {
      // AppBarとヒントの高さを考慮（約100px）
      final topOffset = 100.0;
      if (localPosition.dy < topOffset + _scrollEdgeThreshold) {
        // 上端に近い → 上にスクロール
        final newOffset = (_verticalScrollController.offset - _scrollSpeed)
            .clamp(0.0, _verticalScrollController.position.maxScrollExtent);
        _verticalScrollController.jumpTo(newOffset);
      } else if (localPosition.dy > size.height - _scrollEdgeThreshold) {
        // 下端に近い → 下にスクロール
        final newOffset = (_verticalScrollController.offset + _scrollSpeed)
            .clamp(0.0, _verticalScrollController.position.maxScrollExtent);
        _verticalScrollController.jumpTo(newOffset);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final menuState = ref.watch(menuNotifierProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('献立カレンダー'),
        backgroundColor: Theme.of(context).colorScheme.primary,
        foregroundColor: Theme.of(context).colorScheme.onPrimary,
      ),
      body: _buildBody(context, menuState),
    );
  }

  Widget _buildBody(BuildContext context, MenuState menuState) {
    if (!menuState.hasPlan) {
      return _buildEmptyState(context);
    }

    final plan = menuState.currentPlan!;
    return Column(
      children: [
        // ヒント
        _buildHint(),
        const Divider(height: 1),
        // 献立リスト
        Expanded(
          child: _buildWeekView(context, plan),
        ),
      ],
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

  Widget _buildHint() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Text(
        '長押し→ドラッグで移動',
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.outline,
            ),
        textAlign: TextAlign.center,
      ),
    );
  }

  // ========== 週表示（横スクロール + 縦スクロール） ==========
  Widget _buildWeekView(BuildContext context, MultiDayMenuPlan plan) {
    // 画面幅に応じてカラム幅を決定
    final screenWidth = MediaQuery.of(context).size.width;
    final columnWidth = (screenWidth / 2.5).clamp(180.0, 280.0);

    return Listener(
      onPointerMove: (event) {
        // ドラッグ中なら自動スクロール処理
        if (_dragData != null) {
          _handleDragAutoScroll(event.position);
        }
      },
      child: LayoutBuilder(
        builder: (context, constraints) {
          return SingleChildScrollView(
            controller: _verticalScrollController,
            scrollDirection: Axis.vertical,
            child: SingleChildScrollView(
              controller: _horizontalScrollController,
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: ConstrainedBox(
                // 最小サイズを画面サイズに設定（空き領域でもスクロール可能に）
                constraints: BoxConstraints(
                  minWidth: constraints.maxWidth - 16, // パディング分を引く
                ),
                child: Row(
                  // 左詰めにする
                  mainAxisAlignment: MainAxisAlignment.start,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: plan.dailyPlans.map((dayPlan) {
                    return SizedBox(
                      width: columnWidth,
                      child: _buildDayColumn(context, dayPlan),
                    );
                  }).toList(),
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildDayColumn(BuildContext context, DailyMealAssignment dayPlan) {
    final date = _startDate.add(Duration(days: dayPlan.day - 1));
    // 全栄養素の平均達成率を計算（ホーム画面と同じロジック）
    final achievementRate = dayPlan.achievementRate;
    final achievement = achievementRate.isNotEmpty
        ? achievementRate.values.reduce((a, b) => a + b) / achievementRate.length
        : 0.0;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
      elevation: 2,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // 日付ヘッダー
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: _getDayHeaderColor(dayPlan.day),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
            ),
            child: Column(
              children: [
                Text(
                  '${date.month}/${date.day}',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: _getDayHeaderTextColor(dayPlan.day),
                      ),
                ),
                Text(
                  _getWeekdayShort(date),
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: _getDayHeaderTextColor(dayPlan.day).withValues(alpha: 0.8),
                      ),
                ),
                const SizedBox(height: 4),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: _getAchievementColor(achievement).withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    '${achievement.toInt()}%',
                    style: TextStyle(
                      fontSize: 11,
                      color: _getAchievementColor(achievement),
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          ),
          // 食事セクション
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildMealSection(context, dayPlan, MealType.breakfast, '朝食'),
                _buildMealSection(context, dayPlan, MealType.lunch, '昼食'),
                _buildMealSection(context, dayPlan, MealType.dinner, '夕食'),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMealSection(
    BuildContext context,
    DailyMealAssignment dayPlan,
    MealType mealType,
    String mealLabel,
  ) {
    final dishes = dayPlan.getMealDishes(mealType);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 食事タイプヘッダー
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          margin: const EdgeInsets.only(top: 8),
          decoration: BoxDecoration(
            color: _getMealColor(mealType).withValues(alpha: 0.1),
          ),
          child: Row(
            children: [
              Text(
                _getMealEmoji(mealType),
                style: const TextStyle(fontSize: 14),
              ),
              const SizedBox(width: 4),
              Text(
                mealLabel,
                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: _getMealColor(mealType),
                    ),
              ),
            ],
          ),
        ),
        // 料理リスト
        if (dishes.isEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Text(
              '未設定',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.outline,
                    fontStyle: FontStyle.italic,
                  ),
            ),
          )
        else
          ...dishes.asMap().entries.map((entry) {
            return _buildDraggableMealCardCompact(
              context,
              dayPlan.day,
              mealType,
              entry.key,
              entry.value,
            );
          }),
      ],
    );
  }

  Widget _buildDraggableMealCardCompact(
    BuildContext context,
    int day,
    MealType mealType,
    int index,
    DishPortion portion,
  ) {
    final dragData = _DragData(day: day, mealType: mealType, index: index, portion: portion);
    final isDragging = _dragData?.portion.dish.id == portion.dish.id;

    return DragTarget<_DragData>(
      onWillAcceptWithDetails: (details) {
        return details.data.portion.dish.id != portion.dish.id;
      },
      onAcceptWithDetails: (details) {
        ref.read(menuNotifierProvider.notifier).moveDish(
          fromDay: details.data.day,
          fromMeal: details.data.mealType,
          fromIndex: details.data.index,
          toDay: day,
          toMeal: mealType,
          toIndex: index,
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
              width: 200,
              child: _DraggingCard(portion: portion, mealType: mealType),
            ),
          ),
          childWhenDragging: Opacity(
            opacity: 0.3,
            child: _CompactMealCard(
              portion: portion,
              isDropTarget: false,
              onTap: () => _showDishDetail(context, portion),
            ),
          ),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(6),
              border: isDropTarget
                  ? Border.all(color: Theme.of(context).colorScheme.primary, width: 2)
                  : null,
              color: isDropTarget
                  ? Theme.of(context).colorScheme.primary.withValues(alpha: 0.1)
                  : null,
            ),
            child: _CompactMealCard(
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

  String _getMealEmoji(MealType mealType) {
    switch (mealType) {
      case MealType.breakfast:
        return '🌅';
      case MealType.lunch:
        return '☀️';
      case MealType.dinner:
        return '🌙';
    }
  }

  Color _getMealColor(MealType mealType) {
    switch (mealType) {
      case MealType.breakfast:
        return const Color(0xFFFF9800); // オレンジ
      case MealType.lunch:
        return const Color(0xFF2196F3); // 青
      case MealType.dinner:
        return const Color(0xFF673AB7); // 紫
    }
  }

  // ========== ヘルパー ==========
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
      builder: (context) => DishDetailModal(
        dish: portion.dish,
        servings: portion.servings,
      ),
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

/// ドラッグ中のフィードバックカード
class _DraggingCard extends StatelessWidget {
  final DishPortion portion;
  final MealType mealType;

  const _DraggingCard({required this.portion, required this.mealType});

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Card(
      color: colorScheme.primaryContainer,
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
                    '${_getMealEmoji(mealType)} ${portion.dish.name}',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: colorScheme.onPrimaryContainer,
                    ),
                  ),
                  Text(
                    '${portion.calories.toInt()} kcal ← ドラッグ中',
                    style: TextStyle(
                      fontSize: 12,
                      color: colorScheme.onPrimaryContainer.withValues(alpha: 0.8),
                    ),
                  ),
                ],
              ),
            ),
            Icon(Icons.drag_handle, color: colorScheme.primary),
          ],
        ),
      ),
    );
  }

  String _getMealEmoji(MealType mealType) {
    switch (mealType) {
      case MealType.breakfast:
        return '🌅';
      case MealType.lunch:
        return '☀️';
      case MealType.dinner:
        return '🌙';
    }
  }
}

/// コンパクトな料理カード（横スクロールレイアウト用）
class _CompactMealCard extends StatelessWidget {
  final DishPortion portion;
  final bool isDropTarget;
  final bool isDragging;
  final VoidCallback onTap;

  const _CompactMealCard({
    required this.portion,
    required this.onTap,
    this.isDropTarget = false,
    this.isDragging = false,
  });

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Card(
      margin: EdgeInsets.zero,
      elevation: isDropTarget ? 2 : 0,
      color: isDropTarget
          ? colorScheme.primaryContainer
          : isDragging
              ? Colors.grey.shade200
              : colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(6),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
          child: Row(
            children: [
              // カテゴリ色インジケーター
              Container(
                width: 3,
                height: 28,
                decoration: BoxDecoration(
                  color: _getCategoryColor(portion.dish.category),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(width: 8),
              // 料理情報
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      portion.dish.name,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            fontWeight: FontWeight.w500,
                          ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    Text(
                      '${portion.calories.toInt()} kcal',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            fontSize: 10,
                            color: colorScheme.outline,
                          ),
                    ),
                  ],
                ),
              ),
              // ドラッグハンドル
              Icon(
                Icons.drag_indicator,
                size: 16,
                color: isDropTarget
                    ? colorScheme.primary
                    : colorScheme.outline.withValues(alpha: 0.4),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color _getCategoryColor(String category) {
    switch (category) {
      case '主食':
        return const Color(0xFFFF9800);
      case '主菜':
        return const Color(0xFFE91E63);
      case '副菜':
        return const Color(0xFF4CAF50);
      case '汁物':
        return const Color(0xFF2196F3);
      default:
        return Colors.grey;
    }
  }
}
