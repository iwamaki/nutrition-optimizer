import 'package:flutter/material.dart';
import '../models/food.dart';

class MealCard extends StatelessWidget {
  final Meal meal;

  const MealCard({super.key, required this.meal});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 食材リスト
            ...meal.foods.map((fp) => _buildFoodItem(fp)),
            if (meal.foods.isEmpty)
              const Text('食材がありません', style: TextStyle(color: Colors.grey)),
            const Divider(),
            // カロリー合計
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                Text(
                  '合計: ${meal.totalCalories.toStringAsFixed(0)} kcal',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 4),
            // PFCバランス
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                _buildMacro('P', meal.totalProtein, Colors.red),
                const SizedBox(width: 12),
                _buildMacro('F', meal.totalFat, Colors.yellow.shade700),
                const SizedBox(width: 12),
                _buildMacro('C', meal.totalCarbohydrate, Colors.blue),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFoodItem(FoodPortion fp) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          _getCategoryIcon(fp.food.category),
          const SizedBox(width: 8),
          Expanded(
            child: Text(fp.food.name),
          ),
          Text(
            '${fp.amount.toStringAsFixed(0)}g',
            style: const TextStyle(color: Colors.grey),
          ),
          const SizedBox(width: 8),
          Text(
            '${(fp.food.calories * fp.amount / 100).toStringAsFixed(0)} kcal',
            style: const TextStyle(fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }

  Widget _buildMacro(String label, double value, Color color) {
    return Row(
      children: [
        Container(
          width: 16,
          height: 16,
          decoration: BoxDecoration(
            color: color.withAlpha((0.2 * 255).toInt()),
            borderRadius: BorderRadius.circular(4),
          ),
          child: Center(
            child: Text(
              label,
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
          ),
        ),
        const SizedBox(width: 4),
        Text(
          '${value.toStringAsFixed(1)}g',
          style: const TextStyle(fontSize: 12),
        ),
      ],
    );
  }

  Widget _getCategoryIcon(String category) {
    IconData icon;
    Color color;

    switch (category) {
      case '穀類':
        icon = Icons.rice_bowl;
        color = Colors.brown;
        break;
      case '肉類':
        icon = Icons.set_meal;
        color = Colors.red;
        break;
      case '魚介類':
        icon = Icons.water;
        color = Colors.blue;
        break;
      case '野菜類':
        icon = Icons.eco;
        color = Colors.green;
        break;
      case '卵類':
        icon = Icons.egg;
        color = Colors.orange;
        break;
      case '乳製品':
        icon = Icons.local_drink;
        color = Colors.lightBlue;
        break;
      case '豆類':
        icon = Icons.grain;
        color = Colors.amber;
        break;
      case 'きのこ類':
        icon = Icons.nature;
        color = Colors.brown.shade300;
        break;
      case '果物類':
        icon = Icons.apple;
        color = Colors.pink;
        break;
      case '海藻類':
        icon = Icons.waves;
        color = Colors.teal;
        break;
      default:
        icon = Icons.restaurant;
        color = Colors.grey;
    }

    return Icon(icon, size: 20, color: color);
  }
}
