import 'package:flutter/material.dart';

/// 栄養達成率プログレスバー
class NutrientProgressBar extends StatelessWidget {
  final String label;
  final double value;
  final Color color;
  final double? targetValue;

  const NutrientProgressBar({
    super.key,
    required this.label,
    required this.value,
    required this.color,
    this.targetValue,
  });

  @override
  Widget build(BuildContext context) {
    final progress = (value / 100).clamp(0.0, 1.2);
    final isOver = value > 100;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: Theme.of(context).textTheme.bodySmall,
            ),
            Text(
              '${value.toInt()}%',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: _getValueColor(value),
                    fontWeight: FontWeight.bold,
                  ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        Stack(
          children: [
            // 背景バー
            Container(
              height: 8,
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(4),
              ),
            ),
            // 進捗バー
            FractionallySizedBox(
              widthFactor: progress.clamp(0.0, 1.0),
              child: Container(
                height: 8,
                decoration: BoxDecoration(
                  color: isOver ? Colors.orange : color,
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
            ),
            // 100%ライン
            Positioned(
              left: 0,
              right: 0,
              child: FractionallySizedBox(
                alignment: Alignment.centerLeft,
                widthFactor: 1.0,
                child: Container(
                  alignment: Alignment.centerRight,
                  child: Container(
                    width: 2,
                    height: 8,
                    color: Theme.of(context).colorScheme.outline.withValues(alpha: 0.3),
                  ),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Color _getValueColor(double value) {
    if (value >= 90 && value <= 110) return Colors.green;
    if (value >= 70) return Colors.orange;
    return Colors.red;
  }
}

/// 栄養素サークルインジケーター
class NutrientCircle extends StatelessWidget {
  final String label;
  final double value;
  final Color color;
  final double size;

  const NutrientCircle({
    super.key,
    required this.label,
    required this.value,
    required this.color,
    this.size = 60,
  });

  @override
  Widget build(BuildContext context) {
    final progress = (value / 100).clamp(0.0, 1.0);

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: size,
          height: size,
          child: Stack(
            alignment: Alignment.center,
            children: [
              CircularProgressIndicator(
                value: progress,
                backgroundColor: color.withValues(alpha: 0.2),
                valueColor: AlwaysStoppedAnimation(color),
                strokeWidth: 6,
              ),
              Text(
                '${value.toInt()}%',
                style: TextStyle(
                  fontSize: size / 4,
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall,
        ),
      ],
    );
  }
}
