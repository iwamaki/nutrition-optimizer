import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

class NutrientChart extends StatelessWidget {
  final Map<String, double> achievementRate;

  const NutrientChart({super.key, required this.achievementRate});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '栄養バランス（目標達成率 %）',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 16),
            SizedBox(
              height: 200,
              child: _buildBarChart(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBarChart() {
    final nutrients = [
      ('カロリー', 'calories', Colors.orange),
      ('タンパク質', 'protein', Colors.red),
      ('脂質', 'fat', Colors.yellow.shade700),
      ('炭水化物', 'carbohydrate', Colors.blue),
    ];

    return BarChart(
      BarChartData(
        alignment: BarChartAlignment.spaceAround,
        maxY: 150,
        barTouchData: BarTouchData(
          touchTooltipData: BarTouchTooltipData(
            getTooltipItem: (group, groupIndex, rod, rodIndex) {
              return BarTooltipItem(
                '${nutrients[groupIndex].$1}\n${rod.toY.toStringAsFixed(1)}%',
                const TextStyle(color: Colors.white),
              );
            },
          ),
        ),
        titlesData: FlTitlesData(
          show: true,
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) {
                final index = value.toInt();
                if (index >= 0 && index < nutrients.length) {
                  return Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      nutrients[index].$1,
                      style: const TextStyle(fontSize: 11),
                    ),
                  );
                }
                return const Text('');
              },
              reservedSize: 32,
            ),
          ),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) {
                if (value % 50 == 0) {
                  return Text(
                    '${value.toInt()}%',
                    style: const TextStyle(fontSize: 10),
                  );
                }
                return const Text('');
              },
              reservedSize: 40,
            ),
          ),
          topTitles: const AxisTitles(
            sideTitles: SideTitles(showTitles: false),
          ),
          rightTitles: const AxisTitles(
            sideTitles: SideTitles(showTitles: false),
          ),
        ),
        gridData: FlGridData(
          show: true,
          horizontalInterval: 50,
          drawVerticalLine: false,
          getDrawingHorizontalLine: (value) {
            if (value == 100) {
              return FlLine(
                color: Colors.green,
                strokeWidth: 2,
                dashArray: [5, 5],
              );
            }
            return FlLine(
              color: Colors.grey.withAlpha((0.2 * 255).toInt()),
              strokeWidth: 1,
            );
          },
        ),
        borderData: FlBorderData(show: false),
        barGroups: List.generate(nutrients.length, (index) {
          final nutrient = nutrients[index];
          final value = achievementRate[nutrient.$2] ?? 0;
          return BarChartGroupData(
            x: index,
            barRods: [
              BarChartRodData(
                toY: value.clamp(0, 150),
                color: _getBarColor(value, nutrient.$3),
                width: 40,
                borderRadius: const BorderRadius.vertical(
                  top: Radius.circular(4),
                ),
              ),
            ],
          );
        }),
      ),
    );
  }

  Color _getBarColor(double value, Color baseColor) {
    if (value < 80) {
      return Colors.red.shade300;
    } else if (value > 120) {
      return Colors.orange.shade300;
    }
    return baseColor;
  }
}
