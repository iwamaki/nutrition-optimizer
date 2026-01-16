import 'package:flutter/material.dart';
import '../../core/constants/nutrients.dart';

/// 栄養達成率プログレスバー（厚生労働省の指針に基づく表示）
///
/// 通常栄養素: 推奨量(100%)以上を目指す。超過はOK、上限まで安全。
/// ナトリウム: 目標量(100%)以下を目指す。減らす方向が良い。
class NutrientProgressBar extends StatelessWidget {
  final String label;
  final double value;
  final Color color;
  final double? upperLimitRatio;  // 耐容上限量（推奨量の倍率）
  final bool isUpperTarget;       // 上限方向が目標（ナトリウム等）

  const NutrientProgressBar({
    super.key,
    required this.label,
    required this.value,
    required this.color,
    this.upperLimitRatio,
    this.isUpperTarget = false,
  });

  /// NutrientDefinitionから作成
  factory NutrientProgressBar.fromDefinition({
    Key? key,
    required NutrientDefinition definition,
    required double value,
  }) {
    return NutrientProgressBar(
      key: key,
      label: definition.label,
      value: value,
      color: definition.color,
      upperLimitRatio: definition.upperLimitRatio,
      isUpperTarget: definition.isUpperTarget,
    );
  }

  @override
  Widget build(BuildContext context) {
    // 全栄養素共通: バーの右端 = 150%固定、100%ラインは2/3の位置
    // ナトリウムも同じ表示（ただし上限が100%なので、100%超で即赤）
    const maxPercent = 150.0;
    final progress = (value / maxPercent).clamp(0.0, 1.0);
    const targetLinePosition = 100.0 / maxPercent;  // 約0.667（2/3の位置）
    final displayText = '${value.toInt()}%';

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
            Row(
              children: [
                Text(
                  displayText,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: _getValueColor(value),
                        fontWeight: FontWeight.bold,
                      ),
                ),
                if (_getStatusIcon(value) != null) ...[
                  const SizedBox(width: 4),
                  Icon(
                    _getStatusIcon(value),
                    size: 14,
                    color: _getValueColor(value),
                  ),
                ],
              ],
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
                color: color.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(4),
              ),
            ),
            // 進捗バー
            FractionallySizedBox(
              widthFactor: progress,
              child: Container(
                height: 8,
                decoration: BoxDecoration(
                  color: _getBarColor(value),
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
            ),
            // 100%ライン（全栄養素共通）
            Positioned(
              left: 0,
              right: 0,
              child: FractionallySizedBox(
                alignment: Alignment.centerLeft,
                widthFactor: targetLinePosition,
                child: Container(
                  alignment: Alignment.centerRight,
                  child: Container(
                    width: 2,
                    height: 8,
                    decoration: BoxDecoration(
                      color: Colors.green.shade700,
                      borderRadius: BorderRadius.circular(1),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  /// バーの色を取得（グラデーション対応）
  ///
  /// 全栄養素共通: 不足(赤) → もう少し(オレンジ→緑) → 達成(緑) → 上限超過(赤)
  /// ナトリウムは上限が100%なので、100%超で即赤になる
  Color _getBarColor(double value) {
    // 耐容上限量を超えたかチェック
    final isOverUpperLimit = upperLimitRatio != null && value > upperLimitRatio! * 100;

    if (value < 70) {
      // 0%〜70%: 赤（不足）
      return Colors.red.shade400;
    } else if (value < 100) {
      // 70%〜100%: オレンジ → 緑（もう少し）
      final t = (value - 70) / 30;
      return Color.lerp(Colors.orange, Colors.green, t)!;
    } else if (isOverUpperLimit) {
      // 耐容上限量超過: 赤（警告）
      return Colors.red;
    } else {
      // 100%以上で上限内: 緑（達成）
      return Colors.green;
    }
  }

  /// 値の色を取得（全栄養素共通）
  Color _getValueColor(double value) {
    if (value < 70) return Colors.red;
    if (value < 100) return Colors.orange;
    // 上限超過チェック
    if (upperLimitRatio != null && value > upperLimitRatio! * 100) {
      return Colors.red;
    }
    return Colors.green;  // 達成
  }

  /// ステータスアイコンを取得（全栄養素共通）
  IconData? _getStatusIcon(double value) {
    if (value < 70) return Icons.warning_outlined;
    if (value >= 100) {
      if (upperLimitRatio != null && value > upperLimitRatio! * 100) {
        return Icons.warning_outlined;
      }
      return Icons.check_circle_outline;
    }
    return null;  // 70-100%はアイコンなし
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
