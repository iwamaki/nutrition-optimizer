import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:share_plus/share_plus.dart';
import '../providers/shopping_provider.dart';
import '../../domain/entities/menu_plan.dart';

/// 買い物リスト画面（Riverpod版）
class ShoppingScreen extends ConsumerWidget {
  const ShoppingScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final shoppingState = ref.watch(shoppingNotifierProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('買い物リスト'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          if (shoppingState.items.isNotEmpty)
            Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.share),
                  onPressed: () => _shareList(context, shoppingState),
                  tooltip: '共有',
                ),
                PopupMenuButton<String>(
                  onSelected: (value) {
                    if (value == 'check_all') {
                      ref.read(shoppingNotifierProvider.notifier).checkAll();
                    } else if (value == 'uncheck_all') {
                      ref.read(shoppingNotifierProvider.notifier).uncheckAll();
                    }
                  },
                  itemBuilder: (context) => [
                    const PopupMenuItem(
                      value: 'check_all',
                      child: Row(
                        children: [
                          Icon(Icons.check_box),
                          SizedBox(width: 8),
                          Text('すべてチェック'),
                        ],
                      ),
                    ),
                    const PopupMenuItem(
                      value: 'uncheck_all',
                      child: Row(
                        children: [
                          Icon(Icons.check_box_outline_blank),
                          SizedBox(width: 8),
                          Text('すべて解除'),
                        ],
                      ),
                    ),
                  ],
                ),
              ],
            ),
        ],
      ),
      body: shoppingState.items.isEmpty
          ? _buildEmptyState(context)
          : Column(
              children: [
                // ヘッダー情報
                _buildHeader(context, shoppingState),
                const Divider(height: 1),
                // リスト
                Expanded(
                  child: _buildShoppingList(context, ref, shoppingState),
                ),
              ],
            ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.shopping_cart_outlined,
            size: 80,
            color: Theme.of(context).colorScheme.outline,
          ),
          const SizedBox(height: 16),
          Text(
            '買い物リストがありません',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 8),
          Text(
            '献立を生成すると自動で作成されます',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(context).colorScheme.outline,
                ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(BuildContext context, ShoppingState shoppingState) {
    final checked = shoppingState.checkedCount;
    final total = shoppingState.items.length;
    final remaining = total - checked;

    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${shoppingState.dateRangeDisplay} ${shoppingState.people}人分',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 4),
                    // サマリー詳細
                    Text(
                      '全$total品目 / 購入済み: $checked品 / 残り: $remaining品',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Theme.of(context).colorScheme.outline,
                          ),
                    ),
                  ],
                ),
              ),
              // 進捗
              _buildProgress(context, shoppingState),
            ],
          ),
          const SizedBox(height: 8),
          // 注記
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.secondaryContainer,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  Icons.info_outline,
                  size: 14,
                  color: Theme.of(context).colorScheme.onSecondaryContainer,
                ),
                const SizedBox(width: 6),
                Text(
                  '手持ち食材を除いた不足分のみ表示',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: Theme.of(context).colorScheme.onSecondaryContainer,
                      ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProgress(BuildContext context, ShoppingState shoppingState) {
    final checked = shoppingState.checkedCount;
    final total = shoppingState.items.length;
    final progress = total > 0 ? checked / total : 0.0;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Text(
          '$checked / $total',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: Theme.of(context).colorScheme.primary,
              ),
        ),
        const SizedBox(height: 4),
        SizedBox(
          width: 100,
          child: LinearProgressIndicator(
            value: progress,
            backgroundColor:
                Theme.of(context).colorScheme.primaryContainer,
          ),
        ),
      ],
    );
  }

  Widget _buildShoppingList(
    BuildContext context,
    WidgetRef ref,
    ShoppingState shoppingState,
  ) {
    final categories = shoppingState.sortedCategories;

    return ListView.builder(
      padding: const EdgeInsets.only(bottom: 32),
      itemCount: categories.length,
      itemBuilder: (context, index) {
        final category = categories[index];
        final items = shoppingState.groupedByCategory[category] ?? [];

        return _buildCategorySection(context, ref, shoppingState, category, items);
      },
    );
  }

  Widget _buildCategorySection(
    BuildContext context,
    WidgetRef ref,
    ShoppingState shoppingState,
    String category,
    List<ShoppingItem> items,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // カテゴリヘッダー
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          color: Theme.of(context).colorScheme.surfaceContainerHighest,
          child: Row(
            children: [
              Icon(
                _getCategoryIcon(category),
                size: 18,
                color: Theme.of(context).colorScheme.primary,
              ),
              const SizedBox(width: 8),
              Text(
                category,
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      color: Theme.of(context).colorScheme.primary,
                    ),
              ),
              const Spacer(),
              Text(
                '${items.length}品目',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.outline,
                    ),
              ),
            ],
          ),
        ),
        // アイテムリスト
        ...items.map((item) => _buildShoppingItem(context, ref, shoppingState, item)),
      ],
    );
  }

  Widget _buildShoppingItem(
    BuildContext context,
    WidgetRef ref,
    ShoppingState shoppingState,
    ShoppingItem item,
  ) {
    return ListTile(
      leading: Checkbox(
        value: item.isChecked,
        onChanged: (_) {
          ref.read(shoppingNotifierProvider.notifier).toggleItemByFood(item.foodName);
        },
      ),
      title: Text(
        item.foodName,
        style: TextStyle(
          decoration: item.isChecked ? TextDecoration.lineThrough : null,
          color: item.isChecked
              ? Theme.of(context).colorScheme.outline
              : null,
        ),
      ),
      trailing: Text(
        item.amountDisplay,
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: item.isChecked
                  ? Theme.of(context).colorScheme.outline
                  : Theme.of(context).colorScheme.primary,
              fontWeight: FontWeight.bold,
            ),
      ),
      onTap: () {
        ref.read(shoppingNotifierProvider.notifier).toggleItemByFood(item.foodName);
      },
    );
  }

  IconData _getCategoryIcon(String category) {
    switch (category) {
      case '野菜類':
        return Icons.eco;
      case '果実類':
        return Icons.apple;
      case '肉類':
        return Icons.restaurant;
      case '魚介類':
        return Icons.set_meal;
      case '卵類':
        return Icons.egg;
      case '乳類':
        return Icons.local_drink;
      case '穀類':
        return Icons.grain;
      case '豆類':
        return Icons.spa;
      case '調味料及び香辛料類':
        return Icons.science;
      default:
        return Icons.shopping_basket;
    }
  }

  void _shareList(BuildContext context, ShoppingState shoppingState) {
    final text = shoppingState.toShareText();
    Share.share(text, subject: '買い物リスト');
  }
}
