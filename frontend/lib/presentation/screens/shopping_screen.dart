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
          if (shoppingState.ownedItems.isNotEmpty)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.tertiaryContainer,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.home,
                    size: 14,
                    color: Theme.of(context).colorScheme.onTertiaryContainer,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    '手持ち食材 ${shoppingState.ownedItems.length}品目（下部に表示）',
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: Theme.of(context).colorScheme.onTertiaryContainer,
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
    final toBuyGroups = shoppingState.toBuyGroupedByCategory;
    final ownedGroups = shoppingState.ownedGroupedByCategory;

    // カテゴリ順でソート
    List<String> sortCategories(Iterable<String> cats) {
      final list = cats.toList();
      list.sort((a, b) {
        final indexA = ShoppingState.categoryOrder.indexOf(a);
        final indexB = ShoppingState.categoryOrder.indexOf(b);
        if (indexA == -1 && indexB == -1) return a.compareTo(b);
        if (indexA == -1) return 1;
        if (indexB == -1) return -1;
        return indexA.compareTo(indexB);
      });
      return list;
    }

    final toBuyCategories = sortCategories(toBuyGroups.keys);
    final ownedCategories = sortCategories(ownedGroups.keys);

    return ListView(
      padding: const EdgeInsets.only(bottom: 32),
      children: [
        // 購入必須セクション
        if (toBuyCategories.isNotEmpty) ...[
          ...toBuyCategories.map((category) {
            final items = toBuyGroups[category] ?? [];
            return _buildCategorySection(context, ref, shoppingState, category, items);
          }),
        ],
        // 手持ち食材セクション
        if (ownedCategories.isNotEmpty) ...[
          _buildOwnedSectionHeader(context, shoppingState.ownedItems.length),
          ...ownedCategories.map((category) {
            final items = ownedGroups[category] ?? [];
            return _buildCategorySection(
              context, ref, shoppingState, category, items,
              isOwnedSection: true,
            );
          }),
        ],
      ],
    );
  }

  Widget _buildOwnedSectionHeader(BuildContext context, int count) {
    return Container(
      margin: const EdgeInsets.only(top: 16),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.tertiaryContainer.withValues(alpha: 0.3),
        border: Border(
          top: BorderSide(
            color: Theme.of(context).colorScheme.outline.withValues(alpha: 0.2),
            width: 1,
          ),
        ),
      ),
      child: Row(
        children: [
          Icon(
            Icons.home,
            size: 20,
            color: Theme.of(context).colorScheme.tertiary,
          ),
          const SizedBox(width: 8),
          Text(
            '手持ち食材（在庫確認用）',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  color: Theme.of(context).colorScheme.tertiary,
                  fontWeight: FontWeight.bold,
                ),
          ),
          const Spacer(),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.tertiary.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              '$count品目',
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: Theme.of(context).colorScheme.tertiary,
                  ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCategorySection(
    BuildContext context,
    WidgetRef ref,
    ShoppingState shoppingState,
    String category,
    List<ShoppingItem> items, {
    bool isOwnedSection = false,
  }) {
    final headerColor = isOwnedSection
        ? Theme.of(context).colorScheme.tertiaryContainer.withValues(alpha: 0.5)
        : Theme.of(context).colorScheme.surfaceContainerHighest;
    final iconColor = isOwnedSection
        ? Theme.of(context).colorScheme.tertiary
        : Theme.of(context).colorScheme.primary;
    final textColor = isOwnedSection
        ? Theme.of(context).colorScheme.tertiary
        : Theme.of(context).colorScheme.primary;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // カテゴリヘッダー
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          color: headerColor,
          child: Row(
            children: [
              Icon(
                _getCategoryIcon(category),
                size: 18,
                color: iconColor,
              ),
              const SizedBox(width: 8),
              Text(
                category,
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      color: textColor,
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
        ...items.map((item) => _buildShoppingItem(
          context, ref, shoppingState, item,
          isOwnedSection: isOwnedSection,
        )),
      ],
    );
  }

  Widget _buildShoppingItem(
    BuildContext context,
    WidgetRef ref,
    ShoppingState shoppingState,
    ShoppingItem item, {
    bool isOwnedSection = false,
  }) {
    // 手持ち食材は薄いスタイル
    final isOwned = item.isOwned || isOwnedSection;
    final baseColor = isOwned
        ? Theme.of(context).colorScheme.outline
        : null;
    final amountColor = isOwned
        ? Theme.of(context).colorScheme.tertiary
        : Theme.of(context).colorScheme.primary;

    return ListTile(
      leading: Checkbox(
        value: item.isChecked,
        onChanged: (_) {
          ref.read(shoppingNotifierProvider.notifier).toggleItemByFood(item.foodName);
        },
        activeColor: isOwned ? Theme.of(context).colorScheme.tertiary : null,
      ),
      title: Row(
        children: [
          if (isOwned && !isOwnedSection)
            Padding(
              padding: const EdgeInsets.only(right: 6),
              child: Icon(
                Icons.home,
                size: 16,
                color: Theme.of(context).colorScheme.tertiary,
              ),
            ),
          Expanded(
            child: Text(
              item.foodName,
              style: TextStyle(
                decoration: item.isChecked ? TextDecoration.lineThrough : null,
                color: item.isChecked
                    ? Theme.of(context).colorScheme.outline
                    : baseColor,
              ),
            ),
          ),
        ],
      ),
      trailing: Text(
        item.amountDisplay,
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: item.isChecked
                  ? Theme.of(context).colorScheme.outline
                  : amountColor,
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
