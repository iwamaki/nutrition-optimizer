import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../domain/entities/dish.dart';
import '../../../providers/settings_provider.dart';
import '../generate_modal_controller.dart';

/// 料理カテゴリ（主菜と主食・主菜のみ選択可能）
/// 副菜・汁物・デザートは自動最適化に任せる
const dishCategories = [
  {'name': '主菜', 'colorValue': 0xFFFFEBEE, 'textColorValue': 0xFFC62828},
  {'name': '主食・主菜', 'colorValue': 0xFFFFF3E0, 'textColorValue': 0xFFE65100},
];

/// Step1: お気に入り料理
class StepFavorites extends ConsumerStatefulWidget {
  final ScrollController scrollController;

  const StepFavorites({
    super.key,
    required this.scrollController,
  });

  @override
  ConsumerState<StepFavorites> createState() => _StepFavoritesState();
}

class _StepFavoritesState extends ConsumerState<StepFavorites> {
  final TextEditingController _dishSearchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    // お気に入り料理と全料理リストを読み込み
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final favoriteIds = ref.read(settingsNotifierProvider).favoriteDishIds;
      final controller = ref.read(generateModalControllerProvider.notifier);
      controller.loadFavoriteDishes(favoriteIds);
      controller.loadAllDishes();
    });
  }

  @override
  void dispose() {
    _dishSearchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(generateModalControllerProvider);
    final controller = ref.read(generateModalControllerProvider.notifier);

    return ListView(
      controller: widget.scrollController,
      padding: const EdgeInsets.all(16),
      children: [
        // 料理を追加セクション
        _buildDishSelectionCard(context, state, controller),
        const SizedBox(height: 16),
        const Divider(),
        const SizedBox(height: 16),
        // お気に入り料理セクション
        _buildInfoCard(context),
        const SizedBox(height: 16),
        _buildFavoritesList(context, state),
        // お気に入り料理がある場合のみ表示
        if (state.favoriteDishes.any((d) =>
            d.category != '主食' // 主食以外
        )) ...[
          const SizedBox(height: 16),
          _buildGuaranteeOption(context, state, controller),
        ],
      ],
    );
  }

  /// 料理選択カード
  Widget _buildDishSelectionCard(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
  ) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.restaurant, size: 20),
                const SizedBox(width: 8),
                Text(
                  '料理を追加',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                if (state.specifiedDishes.isNotEmpty) ...[
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.primary,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      '${state.specifiedDishes.length}件選択中',
                      style: Theme.of(context).textTheme.labelSmall?.copyWith(
                            color: Theme.of(context).colorScheme.onPrimary,
                          ),
                    ),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 8),
            Text(
              '選んだ料理は必ず献立に含まれます',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.outline,
                  ),
            ),
            const SizedBox(height: 12),
            _buildDishSearchBar(context, state, controller),
            const SizedBox(height: 12),
            if (state.isLoadingDishes)
              const Center(
                child: Padding(
                  padding: EdgeInsets.all(32),
                  child: CircularProgressIndicator(),
                ),
              )
            else
              _buildDishList(context, state, controller),
          ],
        ),
      ),
    );
  }

  /// 料理検索バー（主菜検索）
  Widget _buildDishSearchBar(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
  ) {
    return TextField(
      controller: _dishSearchController,
      decoration: InputDecoration(
        hintText: '料理を検索...',
        prefixIcon: const Icon(Icons.search, size: 20),
        filled: true,
        fillColor: Theme.of(context).colorScheme.surfaceContainerHighest,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
        isDense: true,
        suffixIcon: state.dishSearchQuery.isNotEmpty
            ? IconButton(
                icon: const Icon(Icons.clear, size: 20),
                onPressed: () {
                  _dishSearchController.clear();
                  controller.clearDishSearch();
                },
              )
            : null,
      ),
      onChanged: (value) {
        controller.searchDishes(value);
      },
    );
  }

  /// 料理リスト（主食以外を表示）
  Widget _buildDishList(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
  ) {
    // 主食以外をフィルタリング（主食はStep1で設定するため除外）
    final allowedCategories = dishCategories.map((c) => c['name'] as String).toSet();
    final allMainDishes = state.allDishes.where((d) => allowedCategories.contains(d.category)).toList();
    final searchedMainDishes = state.dishSearchResults.where((d) => allowedCategories.contains(d.category)).toList();

    final hasFilter = state.dishSearchQuery.isNotEmpty || state.selectedDishCategory != null;
    final dishes = hasFilter ? searchedMainDishes : allMainDishes;

    if (dishes.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(32),
        child: Column(
          children: [
            Icon(
              Icons.search_off,
              size: 48,
              color: Theme.of(context).colorScheme.outline,
            ),
            const SizedBox(height: 8),
            Text(
              hasFilter ? '該当する料理が見つかりません' : '料理データがありません',
              style: TextStyle(
                color: Theme.of(context).colorScheme.outline,
              ),
            ),
          ],
        ),
      );
    }

    // 選択済みIDのセット
    final selectedIds = state.specifiedDishes.map((d) => d.id).toSet();

    // カテゴリ別にグループ化
    if (!hasFilter) {
      // フィルターなしの場合はカテゴリ別に表示
      return _buildDishListByCategory(context, dishes, selectedIds, controller);
    }

    // フィルターありの場合はフラットリスト
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 4, bottom: 8),
          child: Text(
            '検索結果（${dishes.length}件）',
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: Theme.of(context).colorScheme.outline,
                ),
          ),
        ),
        ...dishes.map((dish) => _buildDishListItem(
              context,
              dish,
              selectedIds.contains(dish.id),
              () => controller.toggleSpecifiedDish(dish),
            )),
      ],
    );
  }

  /// カテゴリ別の料理リスト
  Widget _buildDishListByCategory(
    BuildContext context,
    List<Dish> dishes,
    Set<int> selectedIds,
    GenerateModalController controller,
  ) {
    // カテゴリ別にグループ化
    final dishesByCategory = <String, List<Dish>>{};
    for (final dish in dishes) {
      dishesByCategory.putIfAbsent(dish.category, () => []);
      dishesByCategory[dish.category]!.add(dish);
    }

    // カテゴリ順にソート
    final categoryOrder = dishCategories.map((c) => c['name'] as String).toList();
    final sortedCategories = dishesByCategory.keys.toList()
      ..sort((a, b) {
        final indexA = categoryOrder.indexOf(a);
        final indexB = categoryOrder.indexOf(b);
        if (indexA == -1 && indexB == -1) return a.compareTo(b);
        if (indexA == -1) return 1;
        if (indexB == -1) return -1;
        return indexA.compareTo(indexB);
      });

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: sortedCategories.expand((category) {
        final categoryDishes = dishesByCategory[category]!;
        final categoryData = dishCategories.firstWhere(
          (c) => c['name'] == category,
          orElse: () => {'name': category, 'colorValue': 0xFFECEFF1, 'textColorValue': 0xFF455A64},
        );
        final color = Color(categoryData['colorValue'] as int);
        final textColor = Color(categoryData['textColorValue'] as int);

        return [
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              '$category（${categoryDishes.length}件）',
              style: Theme.of(context).textTheme.labelLarge?.copyWith(
                    color: textColor,
                    fontWeight: FontWeight.bold,
                  ),
            ),
          ),
          const SizedBox(height: 8),
          ...categoryDishes.map((dish) => _buildDishListItem(
                context,
                dish,
                selectedIds.contains(dish.id),
                () => controller.toggleSpecifiedDish(dish),
              )),
        ];
      }).toList(),
    );
  }

  /// 料理リストの1アイテム
  Widget _buildDishListItem(
    BuildContext context,
    Dish dish,
    bool isSelected,
    VoidCallback onTap,
  ) {
    final categoryColor = _getCategoryColor(dish.category);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        margin: const EdgeInsets.only(bottom: 4),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: isSelected
              ? Theme.of(context).colorScheme.primaryContainer
              : Theme.of(context).colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: isSelected
                ? Theme.of(context).colorScheme.primary
                : Colors.transparent,
            width: 2,
          ),
        ),
        child: Row(
          children: [
            // 選択チェック
            Icon(
              isSelected ? Icons.check_circle : Icons.circle_outlined,
              size: 20,
              color: isSelected
                  ? Theme.of(context).colorScheme.primary
                  : Theme.of(context).colorScheme.outline,
            ),
            const SizedBox(width: 12),
            // カテゴリタグ
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: categoryColor.withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                dish.category,
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: categoryColor,
                      fontWeight: FontWeight.bold,
                    ),
              ),
            ),
            const SizedBox(width: 8),
            // 料理名
            Expanded(
              child: Text(
                dish.name,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                    ),
              ),
            ),
            // カロリー
            Text(
              '${dish.calories.toStringAsFixed(0)} kcal',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.outline,
                  ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoCard(BuildContext context) {
    return Card(
      color: Theme.of(context).colorScheme.primaryContainer,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(
              Icons.info_outline,
              color: Theme.of(context).colorScheme.onPrimaryContainer,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                'お気に入りに登録した料理は優先的に献立に選ばれます。料理詳細画面のハートボタンから登録できます。',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.onPrimaryContainer,
                    ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFavoritesList(BuildContext context, GenerateModalState state) {
    if (state.isLoadingFavorites) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            children: [
              const CircularProgressIndicator(),
              const SizedBox(height: 16),
              Text(
                'お気に入り料理を読み込み中...',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ],
          ),
        ),
      );
    }

    // 主食以外をフィルタリング
    final allowedCategories = dishCategories.map((c) => c['name'] as String).toSet();
    final favoriteDishesFiltered = state.favoriteDishes.where((d) => allowedCategories.contains(d.category)).toList();

    if (favoriteDishesFiltered.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            children: [
              Icon(
                Icons.favorite_border,
                size: 48,
                color: Theme.of(context).colorScheme.outline,
              ),
              const SizedBox(height: 16),
              Text(
                'お気に入り料理がありません',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: Theme.of(context).colorScheme.outline,
                    ),
              ),
              const SizedBox(height: 8),
              Text(
                '料理詳細画面でハートボタンをタップすると、お気に入りに登録できます',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.outline,
                    ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.favorite, size: 20, color: Colors.red),
                const SizedBox(width: 8),
                Text(
                  'お気に入り料理 (${favoriteDishesFiltered.length}件)',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
              ],
            ),
            const SizedBox(height: 12),
            ...favoriteDishesFiltered.map((dish) => _buildDishItem(context, dish)),
          ],
        ),
      ),
    );
  }

  Widget _buildDishItem(BuildContext context, dynamic dish) {
    final categoryColor = _getCategoryColor(dish.category);

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: categoryColor.withValues(alpha: 0.2),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              dish.category,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: categoryColor,
                    fontWeight: FontWeight.bold,
                  ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              dish.name,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
          Text(
            '${dish.calories.toStringAsFixed(0)} kcal',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.outline,
                ),
          ),
        ],
      ),
    );
  }

  Color _getCategoryColor(String category) {
    switch (category) {
      case '主食':
        return Colors.amber.shade700;
      case '主菜':
        return Colors.red.shade700;
      case '主食・主菜':
        return Colors.orange.shade700;
      case '副菜':
        return Colors.green.shade700;
      case '汁物':
        return Colors.blue.shade700;
      case 'デザート':
        return Colors.pink.shade700;
      default:
        return Colors.grey;
    }
  }

  Widget _buildGuaranteeOption(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
  ) {
    final allowedCategories = dishCategories.map((c) => c['name'] as String).toSet();
    final favoriteCount = state.favoriteDishes.where((d) => allowedCategories.contains(d.category)).length;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.lock, size: 20),
                const SizedBox(width: 8),
                Text('献立への組み込み', style: Theme.of(context).textTheme.titleSmall),
              ],
            ),
            const SizedBox(height: 12),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('お気に入り料理を確実に献立に入れる'),
              subtitle: Text(
                state.guaranteeFavorites
                    ? '上記のお気に入り料理は必ず献立に含まれます'
                    : '優先的に選ばれますが、栄養バランスにより選ばれない場合があります',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.outline,
                    ),
              ),
              value: state.guaranteeFavorites,
              onChanged: (value) => controller.setGuaranteeFavorites(value),
            ),
            if (state.guaranteeFavorites && favoriteCount > state.days * 3) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.orange.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.orange.shade200),
                ),
                child: Row(
                  children: [
                    Icon(Icons.warning_amber, color: Colors.orange.shade700, size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'お気に入り料理が$favoriteCount件あり、${state.days}日分の献立（${state.days * 3}食）に収まりきらない可能性があります',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Colors.orange.shade700,
                            ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
