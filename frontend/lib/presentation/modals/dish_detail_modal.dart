import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../domain/entities/dish.dart';
import '../../utils/recipe_formatter.dart';
import '../providers/settings_provider.dart';
import '../../data/datasources/api_service.dart';

/// 料理詳細モーダル（Riverpod版）
class DishDetailModal extends ConsumerStatefulWidget {
  final Dish dish;
  final double servings;

  const DishDetailModal({
    super.key,
    required this.dish,
    this.servings = 1.0,
  });

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
    final isFavorite = ref.watch(settingsNotifierProvider).isFavorite(widget.dish.id);

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
          const SizedBox(width: 8),
          IconButton(
            icon: Icon(
              isFavorite ? Icons.favorite : Icons.favorite_border,
              color: Colors.white,
            ),
            onPressed: () {
              ref.read(settingsNotifierProvider.notifier).toggleFavoriteDish(widget.dish.id);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(
                    isFavorite
                        ? '${widget.dish.name}をお気に入りから削除しました'
                        : '${widget.dish.name}をお気に入りに追加しました',
                  ),
                  duration: const Duration(seconds: 1),
                ),
              );
            },
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
    final servings = widget.servings;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(
                  '材料',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                if (servings != 1.0) ...[
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.primaryContainer,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      '${servings.toStringAsFixed(servings % 1 == 0 ? 0 : 1)}人前',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Theme.of(context).colorScheme.onPrimaryContainer,
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                  ),
                ],
              ],
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
                          _formatScaledAmount(ing, servings),
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

  /// 人数に応じてスケールした分量を表示形式に変換
  String _formatScaledAmount(DishIngredient ing, double servings) {
    final scaledAmount = ing.amount * servings;

    // 単位がg, kg, ml, Lの場合は重量のみ
    if (ing.unit == 'g' || ing.unit == 'kg' || ing.unit == 'ml' || ing.unit == 'L') {
      if (scaledAmount >= 1000) {
        return '${(scaledAmount / 1000).toStringAsFixed(1)}kg';
      }
      return '${scaledAmount.toStringAsFixed(0)}${ing.unit}';
    }

    // それ以外は「2本 (300g)」のような形式
    final gramDisplay = scaledAmount >= 1000
        ? '${(scaledAmount / 1000).toStringAsFixed(1)}kg'
        : '${scaledAmount.toStringAsFixed(0)}g';

    // displayAmountも人数倍にする（"1" -> "2"など）
    String scaledDisplayAmount = ing.displayAmount;
    if (ing.displayAmount.isNotEmpty) {
      final numMatch = RegExp(r'^(\d+(?:\.\d+)?)(.*)$').firstMatch(ing.displayAmount);
      if (numMatch != null) {
        final num = double.tryParse(numMatch.group(1)!) ?? 1;
        final suffix = numMatch.group(2) ?? '';
        final scaledNum = num * servings;
        scaledDisplayAmount = '${scaledNum.toStringAsFixed(scaledNum % 1 == 0 ? 0 : 1)}$suffix';
      }
    }

    return '$scaledDisplayAmount${ing.unit} ($gramDisplay)';
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
              ...steps.asMap().entries.map((entry) {
                // プレースホルダーを人数に応じた分量に置換
                final formattedStep = RecipeFormatter.formatStep(
                  entry.value,
                  widget.dish.ingredients,
                  widget.servings,
                );
                return Padding(
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
                        Expanded(child: Text(formattedStep)),
                      ],
                    ),
                  );
              }),
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
