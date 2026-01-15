import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../domain/entities/dish.dart';
import '../providers/menu_provider.dart';
import '../../data/datasources/api_service.dart';

/// 料理詳細モーダル（Riverpod版）
class DishDetailModal extends ConsumerStatefulWidget {
  final Dish dish;

  const DishDetailModal({super.key, required this.dish});

  @override
  ConsumerState<DishDetailModal> createState() => _DishDetailModalState();
}

class _DishDetailModalState extends ConsumerState<DishDetailModal> {
  RecipeDetails? _recipeDetails;
  bool _isLoadingRecipe = false;

  @override
  void initState() {
    super.initState();
    _recipeDetails = widget.dish.recipeDetails;
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.7,
      minChildSize: 0.4,
      maxChildSize: 0.95,
      expand: false,
      builder: (context, scrollController) {
        return Container(
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.surface,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
          ),
          child: Column(
            children: [
              // ヘッダー
              _buildHeader(context),
              // コンテンツ
              Expanded(
                child: ListView(
                  controller: scrollController,
                  padding: const EdgeInsets.all(16),
                  children: [
                    // 基本情報
                    _buildBasicInfo(),
                    const SizedBox(height: 16),

                    // 栄養素
                    _buildNutrients(),
                    const SizedBox(height: 16),

                    // 材料
                    _buildIngredients(),
                    const SizedBox(height: 16),

                    // 作り方
                    _buildRecipeSteps(),
                    const SizedBox(height: 24),

                    // アクションボタン
                    _buildActionButtons(),
                    const SizedBox(height: 16),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _getCategoryColor(widget.dish.category),
        borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
      ),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.close),
            color: Colors.white,
            onPressed: () => Navigator.pop(context),
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.dish.name,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                ),
                Text(
                  widget.dish.categoryDisplay,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.white.withValues(alpha: 0.8),
                      ),
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.2),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Text(
              '${widget.dish.calories.toInt()} kcal',
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBasicInfo() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _buildInfoItem(
              Icons.people,
              '${widget.dish.minServings}-${widget.dish.maxServings}人前',
              '調理人数',
            ),
            _buildInfoItem(
              Icons.calendar_today,
              '${widget.dish.storageDays}日',
              '保存日数',
            ),
            if (_recipeDetails?.cookTime != null)
              _buildInfoItem(
                Icons.timer,
                '${_recipeDetails!.cookTime}分',
                '調理時間',
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoItem(IconData icon, String value, String label) {
    return Column(
      children: [
        Icon(icon, color: Theme.of(context).colorScheme.primary),
        const SizedBox(height: 4),
        Text(
          value,
          style: Theme.of(context).textTheme.titleSmall,
        ),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.outline,
              ),
        ),
      ],
    );
  }

  Widget _buildNutrients() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '栄養素（1人前）',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildNutrientBadge('P', widget.dish.protein, Colors.red, 'タンパク質'),
                _buildNutrientBadge('F', widget.dish.fat, Colors.amber, '脂質'),
                _buildNutrientBadge('C', widget.dish.carbohydrate, Colors.blue, '炭水化物'),
                _buildNutrientBadge('繊維', widget.dish.fiber, Colors.green, '食物繊維'),
              ],
            ),
            const Divider(height: 24),
            Wrap(
              spacing: 16,
              runSpacing: 8,
              children: [
                _buildMicroNutrient('カルシウム', widget.dish.calcium, 'mg'),
                _buildMicroNutrient('鉄', widget.dish.iron, 'mg'),
                _buildMicroNutrient('ビタミンA', widget.dish.vitaminA, 'μg'),
                _buildMicroNutrient('ビタミンC', widget.dish.vitaminC, 'mg'),
                _buildMicroNutrient('ビタミンD', widget.dish.vitaminD, 'μg'),
                _buildMicroNutrient('ナトリウム', widget.dish.sodium, 'mg'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNutrientBadge(String label, double value, Color color, String tooltip) {
    return Tooltip(
      message: tooltip,
      child: Column(
        children: [
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: color.withValues(alpha: 0.2),
            ),
            child: Center(
              child: Column(
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
                  Text(
                    '${value.toStringAsFixed(1)}g',
                    style: TextStyle(
                      fontSize: 12,
                      color: color,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMicroNutrient(String label, double value, String unit) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          '$label: ',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.outline,
              ),
        ),
        Text(
          '${value.toStringAsFixed(1)}$unit',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
        ),
      ],
    );
  }

  Widget _buildIngredients() {
    final ingredients = widget.dish.ingredients;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '材料',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 12),
            if (ingredients.isEmpty)
              Text(
                '材料情報がありません',
                style: TextStyle(color: Theme.of(context).colorScheme.outline),
              )
            else
              ...ingredients.map((ing) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Row(
                      children: [
                        const Icon(Icons.circle, size: 6),
                        const SizedBox(width: 8),
                        Expanded(child: Text(ing.foodName ?? '食材')),
                        Text(
                          ing.amountDisplay,
                          style: TextStyle(
                            color: Theme.of(context).colorScheme.primary,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  )),
          ],
        ),
      ),
    );
  }

  Widget _buildRecipeSteps() {
    final steps = _recipeDetails?.steps ?? [];

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
                  '作り方',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                if (steps.isEmpty && !_isLoadingRecipe)
                  TextButton.icon(
                    onPressed: _loadRecipe,
                    icon: const Icon(Icons.auto_awesome, size: 16),
                    label: const Text('AI生成'),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            if (_isLoadingRecipe)
              const Center(
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Column(
                    children: [
                      CircularProgressIndicator(),
                      SizedBox(height: 8),
                      Text('レシピを生成中...'),
                    ],
                  ),
                ),
              )
            else if (steps.isEmpty)
              Text(
                widget.dish.instructions ?? 'レシピ情報がありません',
                style: TextStyle(color: Theme.of(context).colorScheme.outline),
              )
            else
              ...steps.asMap().entries.map((entry) => Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          width: 24,
                          height: 24,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: Theme.of(context).colorScheme.primary,
                          ),
                          child: Center(
                            child: Text(
                              '${entry.key + 1}',
                              style: TextStyle(
                                color: Theme.of(context).colorScheme.onPrimary,
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(child: Text(entry.value)),
                      ],
                    ),
                  )),
            if (_recipeDetails?.tips != null) ...[
              const Divider(),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.lightbulb_outline, size: 16),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _recipeDetails!.tips!,
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildActionButtons() {
    return Row(
      children: [
        Expanded(
          child: OutlinedButton.icon(
            onPressed: () {
              ref.read(menuNotifierProvider.notifier).excludeDish(widget.dish.id);
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('${widget.dish.name}を除外しました')),
              );
            },
            icon: const Icon(Icons.block),
            label: const Text('除外'),
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: FilledButton.icon(
            onPressed: () {
              ref.read(menuNotifierProvider.notifier).keepDish(widget.dish.id);
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('${widget.dish.name}を固定しました')),
              );
            },
            icon: const Icon(Icons.favorite),
            label: const Text('固定'),
          ),
        ),
      ],
    );
  }

  Color _getCategoryColor(String category) {
    switch (category) {
      case '主食':
        return Colors.brown;
      case '主菜':
        return Colors.red.shade700;
      case '副菜':
        return Colors.green.shade700;
      case '汁物':
        return Colors.blue.shade700;
      case 'デザート':
        return Colors.pink.shade400;
      default:
        return Colors.grey;
    }
  }

  Future<void> _loadRecipe() async {
    setState(() => _isLoadingRecipe = true);

    try {
      final apiService = ApiService();
      final details = await apiService.generateRecipe(widget.dish.id);
      setState(() {
        _recipeDetails = details;
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('レシピの生成に失敗しました: $e')),
        );
      }
    } finally {
      setState(() => _isLoadingRecipe = false);
    }
  }
}
