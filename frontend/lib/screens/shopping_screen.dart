import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:share_plus/share_plus.dart';
import '../providers/shopping_provider.dart';
import '../models/menu_plan.dart';

/// 買い物リスト画面
class ShoppingScreen extends StatelessWidget {
  const ShoppingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('買い物リスト'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          Consumer<ShoppingProvider>(
            builder: (context, shopping, child) {
              if (shopping.items.isEmpty) return const SizedBox.shrink();
              return Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.share),
                    onPressed: () => _shareList(context, shopping),
                    tooltip: '共有',
                  ),
                  PopupMenuButton<String>(
                    onSelected: (value) {
                      if (value == 'check_all') {
                        shopping.checkAll();
                      } else if (value == 'uncheck_all') {
                        shopping.uncheckAll();
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
              );
            },
          ),
        ],
      ),
      body: Consumer<ShoppingProvider>(
        builder: (context, shopping, child) {
          if (shopping.items.isEmpty) {
            return _buildEmptyState(context);
          }

          return Column(
            children: [
              // ヘッダー情報
              _buildHeader(context, shopping),
              const Divider(height: 1),
              // リスト
              Expanded(
                child: _buildShoppingList(context, shopping),
              ),
            ],
          );
        },
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

  Widget _buildHeader(BuildContext context, ShoppingProvider shopping) {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${shopping.days}日分・${shopping.people}人分',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 4),
                Text(
                  '${shopping.items.length}品目',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Theme.of(context).colorScheme.outline,
                      ),
                ),
              ],
            ),
          ),
          // 進捗
          _buildProgress(context, shopping),
        ],
      ),
    );
  }

  Widget _buildProgress(BuildContext context, ShoppingProvider shopping) {
    final checked = shopping.checkedCount;
    final total = shopping.items.length;
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

  Widget _buildShoppingList(BuildContext context, ShoppingProvider shopping) {
    final categories = shopping.sortedCategories;

    return ListView.builder(
      padding: const EdgeInsets.only(bottom: 32),
      itemCount: categories.length,
      itemBuilder: (context, index) {
        final category = categories[index];
        final items = shopping.groupedByCategory[category] ?? [];

        return _buildCategorySection(context, shopping, category, items);
      },
    );
  }

  Widget _buildCategorySection(
    BuildContext context,
    ShoppingProvider shopping,
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
        ...items.map((item) => _buildShoppingItem(context, shopping, item)),
      ],
    );
  }

  Widget _buildShoppingItem(
    BuildContext context,
    ShoppingProvider shopping,
    ShoppingItem item,
  ) {
    return ListTile(
      leading: Checkbox(
        value: item.isChecked,
        onChanged: (_) => shopping.toggleItem(item),
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
      onTap: () => shopping.toggleItem(item),
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

  void _shareList(BuildContext context, ShoppingProvider shopping) {
    final text = shopping.toShareText();
    Share.share(text, subject: '買い物リスト');
  }
}
