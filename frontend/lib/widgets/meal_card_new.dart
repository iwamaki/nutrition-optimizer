import 'package:flutter/material.dart';
import '../models/dish.dart';

/// 料理カード（新デザイン）
class MealCardNew extends StatelessWidget {
  final DishPortion portion;
  final VoidCallback? onTap;
  final VoidCallback? onExclude;

  const MealCardNew({
    super.key,
    required this.portion,
    this.onTap,
    this.onExclude,
  });

  @override
  Widget build(BuildContext context) {
    final dish = portion.dish;
    final colorScheme = Theme.of(context).colorScheme;

    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              // カテゴリアイコン
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: _getCategoryColor(dish.category).withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(
                  _getCategoryIcon(dish.category),
                  color: _getCategoryColor(dish.category),
                ),
              ),
              const SizedBox(width: 12),
              // 料理情報
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      dish.name,
                      style: Theme.of(context).textTheme.titleSmall,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        _buildChip(
                          context,
                          dish.categoryDisplay,
                          _getCategoryColor(dish.category),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          '${dish.calories.toInt()} kcal',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: colorScheme.outline,
                              ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              // 栄養素ミニバー
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  _buildMiniNutrient('P', dish.protein, Colors.red),
                  const SizedBox(height: 2),
                  _buildMiniNutrient('F', dish.fat, Colors.amber),
                  const SizedBox(height: 2),
                  _buildMiniNutrient('C', dish.carbohydrate, Colors.blue),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildChip(BuildContext context, String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.2),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 10,
          color: color,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _buildMiniNutrient(String label, double value, Color color) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          label,
          style: TextStyle(
            fontSize: 10,
            color: color,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(width: 4),
        Text(
          '${value.toInt()}g',
          style: const TextStyle(fontSize: 10),
        ),
      ],
    );
  }

  Color _getCategoryColor(String category) {
    switch (category) {
      case '主食':
        return Colors.brown;
      case '主菜':
        return Colors.red;
      case '副菜':
        return Colors.green;
      case '汁物':
        return Colors.blue;
      case 'デザート':
        return Colors.pink;
      default:
        return Colors.grey;
    }
  }

  IconData _getCategoryIcon(String category) {
    switch (category) {
      case '主食':
        return Icons.rice_bowl;
      case '主菜':
        return Icons.restaurant;
      case '副菜':
        return Icons.eco;
      case '汁物':
        return Icons.soup_kitchen;
      case 'デザート':
        return Icons.cake;
      default:
        return Icons.fastfood;
    }
  }
}

/// 料理カードリスト
class MealCardList extends StatelessWidget {
  final List<DishPortion> dishes;
  final void Function(DishPortion)? onDishTap;

  const MealCardList({
    super.key,
    required this.dishes,
    this.onDishTap,
  });

  @override
  Widget build(BuildContext context) {
    if (dishes.isEmpty) {
      return Card(
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
      );
    }

    return Column(
      children: dishes
          .map((dish) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: MealCardNew(
                  portion: dish,
                  onTap: onDishTap != null ? () => onDishTap!(dish) : null,
                ),
              ))
          .toList(),
    );
  }
}
