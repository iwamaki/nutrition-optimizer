import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../models/food.dart';
import '../services/api_service.dart';
import '../widgets/meal_card.dart';
import '../widgets/nutrient_chart.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService _apiService = ApiService();
  MenuPlan? _menuPlan;
  bool _isLoading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _generateMenu();
  }

  Future<void> _generateMenu() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final plan = await _apiService.optimizeMenu();
      setState(() {
        _menuPlan = plan;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('今日のメニュー'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _isLoading ? null : _generateMenu,
            tooltip: '再生成',
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('メニューを最適化中...'),
          ],
        ),
      );
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            Text('エラーが発生しました', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32),
              child: Text(
                _error!,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.grey),
              ),
            ),
            const SizedBox(height: 16),
            const Text(
              'バックエンドが起動しているか確認してください\ncd backend && uvicorn app.main:app --reload',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: _generateMenu,
              icon: const Icon(Icons.refresh),
              label: const Text('再試行'),
            ),
          ],
        ),
      );
    }

    if (_menuPlan == null) {
      return const Center(child: Text('メニューがありません'));
    }

    return RefreshIndicator(
      onRefresh: _generateMenu,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 栄養サマリーカード
            _buildSummaryCard(),
            const SizedBox(height: 16),

            // 栄養達成率チャート
            NutrientChart(achievementRate: _menuPlan!.achievementRate),
            const SizedBox(height: 24),

            // 各食事
            Text('朝食', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            MealCard(meal: _menuPlan!.breakfast),
            const SizedBox(height: 16),

            Text('昼食', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            MealCard(meal: _menuPlan!.lunch),
            const SizedBox(height: 16),

            Text('夕食', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            MealCard(meal: _menuPlan!.dinner),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryCard() {
    final plan = _menuPlan!;
    return Card(
      elevation: 4,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '1日の栄養サマリー',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const Divider(),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildNutrientStat(
                  'カロリー',
                  '${plan.totalNutrients['calories']?.toStringAsFixed(0) ?? 0}',
                  'kcal',
                  Colors.orange,
                ),
                _buildNutrientStat(
                  'タンパク質',
                  '${plan.totalNutrients['protein']?.toStringAsFixed(1) ?? 0}',
                  'g',
                  Colors.red,
                ),
                _buildNutrientStat(
                  '脂質',
                  '${plan.totalNutrients['fat']?.toStringAsFixed(1) ?? 0}',
                  'g',
                  Colors.yellow.shade700,
                ),
                _buildNutrientStat(
                  '炭水化物',
                  '${plan.totalNutrients['carbohydrate']?.toStringAsFixed(1) ?? 0}',
                  'g',
                  Colors.blue,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNutrientStat(
    String label,
    String value,
    String unit,
    Color color,
  ) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        Text(unit, style: const TextStyle(fontSize: 12, color: Colors.grey)),
        const SizedBox(height: 4),
        Text(label, style: const TextStyle(fontSize: 12)),
      ],
    );
  }
}
