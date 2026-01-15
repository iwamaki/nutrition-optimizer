import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../providers/settings_provider.dart';
import '../generate_modal_controller.dart';

/// Step2: 手持ち食材
class StepOwnedFoods extends ConsumerStatefulWidget {
  final ScrollController scrollController;

  const StepOwnedFoods({
    super.key,
    required this.scrollController,
  });

  @override
  ConsumerState<StepOwnedFoods> createState() => _StepOwnedFoodsState();
}

class _StepOwnedFoodsState extends ConsumerState<StepOwnedFoods> {
  final TextEditingController _searchController = TextEditingController();
  String? _selectedCategory;
  bool _hasSearched = false;

  @override
  void initState() {
    super.initState();
    // 基本食材リストをAPIから読み込み
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(generateModalControllerProvider.notifier).loadIngredients();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(generateModalControllerProvider);
    final controller = ref.read(generateModalControllerProvider.notifier);

    // テキスト検索中かどうか（検索クエリがある場合のみ）
    final isTextSearching = state.searchQuery.isNotEmpty && _hasSearched;

    return ListView(
      controller: widget.scrollController,
      padding: const EdgeInsets.all(12),
      children: [
        _buildExplanationCard(context),
        const SizedBox(height: 12),
        _buildSearchBarWithCategory(context, state, controller),
        const SizedBox(height: 12),
        if (state.isSearching || state.isLoadingIngredients)
          const Padding(
            padding: EdgeInsets.all(32),
            child: Center(child: CircularProgressIndicator()),
          )
        else if (isTextSearching)
          _buildSearchResults(context, state, controller)
        else
          _buildCategorizedIngredients(context, state, controller),
      ],
    );
  }

  Widget _buildExplanationCard(BuildContext context) {
    return Card(
      color: const Color(0xFFE8F5E9),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            const Icon(Icons.home, color: Color(0xFF2E7D32)),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '家にある食材を選択',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          color: const Color(0xFF2E7D32),
                        ),
                  ),
                  Text(
                    '→ 買い物リストから除外されます',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Theme.of(context).colorScheme.outline,
                        ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '長押しでお気に入り登録',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Theme.of(context).colorScheme.outline,
                          fontStyle: FontStyle.italic,
                        ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSearchBarWithCategory(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
  ) {
    return Row(
      children: [
        // カテゴリドロップダウン
        Container(
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.surfaceContainerHighest,
            borderRadius: BorderRadius.circular(12),
          ),
          child: PopupMenuButton<String?>(
            initialValue: _selectedCategory,
            onSelected: (category) {
              setState(() {
                _selectedCategory = category;
                // カテゴリ選択はローカルでフィルタリング（API検索は使わない）
              });
            },
            itemBuilder: (context) => [
              const PopupMenuItem<String?>(
                value: null,
                child: Text('全て'),
              ),
              ...ingredientCategories.map((cat) => PopupMenuItem<String>(
                value: cat['name'] as String,
                child: Text(cat['name'] as String),
              )),
            ],
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.filter_list,
                    size: 20,
                    color: _selectedCategory != null
                        ? Theme.of(context).colorScheme.primary
                        : Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    _selectedCategory ?? '分類',
                    style: TextStyle(
                      color: _selectedCategory != null
                          ? Theme.of(context).colorScheme.primary
                          : Theme.of(context).colorScheme.onSurfaceVariant,
                      fontWeight: _selectedCategory != null
                          ? FontWeight.bold
                          : FontWeight.normal,
                    ),
                  ),
                  Icon(
                    Icons.arrow_drop_down,
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(width: 8),
        // 検索バー
        Expanded(
          child: TextField(
            controller: _searchController,
            decoration: InputDecoration(
              hintText: '食材を検索...',
              prefixIcon: const Icon(Icons.search, size: 20),
              filled: true,
              fillColor: Theme.of(context).colorScheme.surfaceContainerHighest,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide.none,
              ),
              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
              isDense: true,
              suffixIcon: (state.searchQuery.isNotEmpty || _selectedCategory != null)
                  ? IconButton(
                      icon: const Icon(Icons.clear, size: 20),
                      onPressed: () {
                        _searchController.clear();
                        setState(() {
                          _selectedCategory = null;
                          _hasSearched = false;
                        });
                        controller.clearSearch();
                      },
                    )
                  : null,
            ),
            onChanged: (value) {
              setState(() {
                _hasSearched = true;
              });
              controller.searchIngredients(value);
            },
            onSubmitted: (value) {
              setState(() {
                _hasSearched = true;
              });
              controller.searchIngredients(value);
            },
          ),
        ),
      ],
    );
  }

  Widget _buildSearchResults(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
  ) {
    if (state.searchResults.isEmpty) {
      // 検索結果なし
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
              '該当する食材が見つかりません',
              style: TextStyle(
                color: Theme.of(context).colorScheme.outline,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              '別のキーワードで検索してください',
              style: TextStyle(
                fontSize: 12,
                color: Theme.of(context).colorScheme.outline,
              ),
            ),
          ],
        ),
      );
    }

    // 重複排除: 同じnameの食材は最初の1つだけ表示
    // （文科省データには同じ素材の調理後バリエーションが複数存在するため）
    final uniqueFoods = <String, Map<String, dynamic>>{};
    for (final food in state.searchResults) {
      final name = food['name'] as String? ?? '';
      if (name.isNotEmpty && !uniqueFoods.containsKey(name)) {
        uniqueFoods[name] = {
          'id': food['id'],
          'name': name,
          'emoji': _getEmojiForFood(name),
          'category': food['category'] ?? '',
        };
      }
    }
    // 五十音順でソート
    final foodsList = uniqueFoods.values.toList()
      ..sort((a, b) => (a['name'] as String).compareTo(b['name'] as String));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 4, bottom: 8),
          child: Text(
            '検索結果（${foodsList.length}件）',
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: Theme.of(context).colorScheme.outline,
                ),
          ),
        ),
        _buildIngredientGrid(
          context,
          foodsList,
          state,
          controller,
        ),
      ],
    );
  }

  String _getEmojiForFood(String name) {
    // 食品名から絵文字を推測
    if (name.contains('卵')) return '🥚';
    if (name.contains('玉ねぎ') || name.contains('たまねぎ')) return '🧅';
    if (name.contains('にんじん') || name.contains('人参')) return '🥕';
    if (name.contains('豚')) return '🐷';
    if (name.contains('鶏') || name.contains('とり')) return '🐔';
    if (name.contains('牛')) return '🐄';
    if (name.contains('牛乳') || name.contains('ミルク')) return '🥛';
    if (name.contains('キャベツ')) return '🥬';
    if (name.contains('豆腐')) return '🧈';
    if (name.contains('魚') || name.contains('さば') || name.contains('さけ') || name.contains('鮭')) return '🐟';
    if (name.contains('えび') || name.contains('海老')) return '🦐';
    if (name.contains('いか') || name.contains('たこ')) return '🦑';
    if (name.contains('トマト')) return '🍅';
    if (name.contains('じゃがいも') || name.contains('ポテト')) return '🥔';
    if (name.contains('きゅうり')) return '🥒';
    if (name.contains('なす')) return '🍆';
    if (name.contains('ピーマン') || name.contains('パプリカ')) return '🫑';
    if (name.contains('大根')) return '🥬';
    if (name.contains('ほうれん草') || name.contains('小松菜')) return '🥬';
    if (name.contains('ねぎ') || name.contains('葱')) return '🧅';
    if (name.contains('にんにく') || name.contains('ニンニク')) return '🧄';
    if (name.contains('きのこ') || name.contains('しめじ') || name.contains('しいたけ')) return '🍄';
    if (name.contains('米') || name.contains('ごはん')) return '🍚';
    if (name.contains('パン')) return '🍞';
    if (name.contains('パスタ') || name.contains('麺')) return '🍝';
    return '🍽️';
  }

  /// カテゴリ別にセクション分けして表示（お気に入りが一番上）
  Widget _buildCategorizedIngredients(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
  ) {
    final settingsState = ref.watch(settingsNotifierProvider);
    final favoriteIds = settingsState.favoriteIngredientIds;

    // カテゴリでフィルタリング
    final filteredIngredients = _selectedCategory != null
        ? state.ingredients.where((i) => i['category'] == _selectedCategory).toList()
        : state.ingredients;

    // お気に入り食材を抽出
    final favoriteIngredients = filteredIngredients
        .where((i) => favoriteIds.contains(i['id']))
        .toList()
      ..sort((a, b) => (a['name'] as String? ?? '').compareTo(b['name'] as String? ?? ''));

    // カテゴリ別にグループ化（お気に入りも含める＝コピー表示）
    final ingredientsByCategory = <String, List<Map<String, dynamic>>>{};
    for (final ingredient in filteredIngredients) {
      final category = ingredient['category'] as String? ?? 'その他';
      ingredientsByCategory.putIfAbsent(category, () => []);
      ingredientsByCategory[category]!.add(ingredient);
    }

    // 各カテゴリ内で五十音順ソート
    for (final list in ingredientsByCategory.values) {
      list.sort((a, b) => (a['name'] as String? ?? '').compareTo(b['name'] as String? ?? ''));
    }

    // カテゴリの表示順序（ingredientCategoriesの順序に従う）
    final categoryOrder = ingredientCategories.map((c) => c['name'] as String).toList();
    final sortedCategories = ingredientsByCategory.keys.toList()
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
      children: [
        // お気に入りセクション（一番上）
        if (favoriteIngredients.isNotEmpty) ...[
          _buildCategorySection(
            context,
            'お気に入り',
            favoriteIngredients,
            state,
            controller,
            color: const Color(0xFFFFF3E0),
            textColor: const Color(0xFFFF9800),
            icon: Icons.star,
          ),
          const SizedBox(height: 16),
        ],
        // カテゴリ別セクション
        ...sortedCategories.expand((category) {
          final ingredients = ingredientsByCategory[category]!;
          if (ingredients.isEmpty) return <Widget>[];

          final categoryData = ingredientCategories.firstWhere(
            (c) => c['name'] == category,
            orElse: () => {'name': category, 'colorValue': 0xFFECEFF1, 'textColorValue': 0xFF455A64},
          );
          final color = Color(categoryData['colorValue'] as int);
          final textColor = Color(categoryData['textColorValue'] as int);

          return [
            _buildCategorySection(
              context,
              category,
              ingredients,
              state,
              controller,
              color: color,
              textColor: textColor,
            ),
            const SizedBox(height: 16),
          ];
        }),
      ],
    );
  }

  /// カテゴリセクションを構築
  Widget _buildCategorySection(
    BuildContext context,
    String categoryName,
    List<Map<String, dynamic>> ingredients,
    GenerateModalState state,
    GenerateModalController controller, {
    required Color color,
    required Color textColor,
    IconData? icon,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (icon != null) ...[
                Icon(icon, size: 16, color: textColor),
                const SizedBox(width: 4),
              ],
              Text(
                '$categoryName（${ingredients.length}件）',
                style: Theme.of(context).textTheme.labelLarge?.copyWith(
                      color: textColor,
                      fontWeight: FontWeight.bold,
                    ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        _buildIngredientGrid(context, ingredients, state, controller),
      ],
    );
  }

  Widget _buildIngredientGrid(
    BuildContext context,
    List<Map<String, dynamic>> ingredients,
    GenerateModalState state,
    GenerateModalController controller,
  ) {
    final settingsState = ref.watch(settingsNotifierProvider);
    final favoriteIds = settingsState.favoriteIngredientIds;

    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 4,
        mainAxisSpacing: 4,
        crossAxisSpacing: 4,
        childAspectRatio: 0.85,
      ),
      itemCount: ingredients.length,
      itemBuilder: (context, index) {
        final ingredient = ingredients[index];
        final ingredientId = ingredient['id'] as int;
        final isSelected = state.ownedIngredientIds.contains(ingredientId);
        final isFavorite = favoriteIds.contains(ingredientId);
        final emoji = ingredient['emoji'] ?? _getEmojiForFood(ingredient['name'] ?? '');
        final name = ingredient['name'] ?? '';

        return GestureDetector(
          onTap: () => controller.toggleIngredient(ingredientId),
          onLongPress: () {
            HapticFeedback.mediumImpact();
            ref.read(settingsNotifierProvider.notifier).toggleFavoriteIngredient(ingredientId);
            final willBeFavorite = !isFavorite;
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(
                  willBeFavorite ? '$name をお気に入りに追加しました' : '$name をお気に入りから削除しました',
                ),
                duration: const Duration(seconds: 1),
                behavior: SnackBarBehavior.floating,
              ),
            );
          },
          child: Container(
            decoration: BoxDecoration(
              color: isSelected
                  ? const Color(0xFFE8F5E9)
                  : Theme.of(context).colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(8),
              border: isSelected
                  ? Border.all(color: const Color(0xFF4CAF50), width: 2)
                  : null,
            ),
            child: Stack(
              children: [
                Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        emoji,
                        style: const TextStyle(fontSize: 28),
                      ),
                      const SizedBox(height: 2),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 4),
                        child: Text(
                          name,
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                            color: isSelected
                                ? const Color(0xFF2E7D32)
                                : Theme.of(context).colorScheme.onSurface,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          textAlign: TextAlign.center,
                        ),
                      ),
                    ],
                  ),
                ),
                // 選択中チェックマーク（右上）
                if (isSelected)
                  Positioned(
                    top: 4,
                    right: 4,
                    child: Container(
                      width: 16,
                      height: 16,
                      decoration: const BoxDecoration(
                        color: Color(0xFF4CAF50),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.check,
                        size: 12,
                        color: Colors.white,
                      ),
                    ),
                  ),
                // お気に入りスター（左上）
                if (isFavorite)
                  Positioned(
                    top: 4,
                    left: 4,
                    child: Icon(
                      Icons.star,
                      size: 16,
                      color: Colors.orange.shade600,
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}
