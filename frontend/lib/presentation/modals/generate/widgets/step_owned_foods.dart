import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
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

  @override
  void dispose() {
    _searchController.dispose();
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
        _buildExplanationCard(context),
        const SizedBox(height: 16),
        _buildSearchBar(context, state, controller),
        const SizedBox(height: 16),
        if (state.isSearching)
          const Center(child: CircularProgressIndicator())
        else if (state.searchResults.isNotEmpty) ...[
          _buildSearchResults(context, state, controller),
          const SizedBox(height: 16),
        ],
        _buildFrequentFoods(context, state, controller),
        const SizedBox(height: 16),
        _buildCategoryButtons(context, controller),
        const SizedBox(height: 16),
        if (state.ownedFoodIds.isNotEmpty)
          _buildSelectedCount(context, state, controller),
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
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSearchBar(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
  ) {
    return TextField(
      controller: _searchController,
      decoration: InputDecoration(
        hintText: '🔍 食材を検索...',
        filled: true,
        fillColor: Theme.of(context).colorScheme.surfaceContainerHighest,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(24),
          borderSide: BorderSide.none,
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        suffixIcon: state.searchQuery.isNotEmpty
            ? IconButton(
                icon: const Icon(Icons.clear),
                onPressed: () {
                  _searchController.clear();
                  controller.clearSearch();
                },
              )
            : null,
      ),
      onChanged: (value) {
        controller.searchFoods(value);
      },
    );
  }

  Widget _buildSearchResults(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '検索結果',
          style: Theme.of(context).textTheme.titleSmall,
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: state.searchResults.map((food) {
            final isSelected = state.ownedFoodIds.contains(food['id']);
            return FilterChip(
              label: Text(food['name'] ?? ''),
              selected: isSelected,
              selectedColor: const Color(0xFFE8F5E9),
              onSelected: (_) => controller.toggleFood(food['id'] as int),
            );
          }).toList(),
        ),
      ],
    );
  }

  Widget _buildFrequentFoods(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '⭐ よく使う',
          style: Theme.of(context).textTheme.titleSmall,
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: frequentFoods.map((food) {
            final isSelected = state.ownedFoodIds.contains(food['id']);
            return FilterChip(
              label: Text('${food['emoji']}${food['name']}'),
              selected: isSelected,
              selectedColor: const Color(0xFFE8F5E9),
              onSelected: (_) => controller.toggleFood(food['id'] as int),
            );
          }).toList(),
        ),
      ],
    );
  }

  Widget _buildCategoryButtons(
    BuildContext context,
    GenerateModalController controller,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '📁 カテゴリから探す',
          style: Theme.of(context).textTheme.titleSmall,
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: foodCategories.map((cat) {
            return ActionChip(
              label: Text(cat['name'] as String),
              backgroundColor: Color(cat['colorValue'] as int),
              labelStyle: TextStyle(color: Color(cat['textColorValue'] as int)),
              onPressed: () {
                controller.searchFoodsByCategory(cat['name'] as String);
                _searchController.text = cat['name'] as String;
              },
            );
          }).toList(),
        ),
      ],
    );
  }

  Widget _buildSelectedCount(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
  ) {
    return Card(
      color: const Color(0xFFE8F5E9),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            const Icon(Icons.check, color: Color(0xFF2E7D32), size: 20),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                '選択中: ${state.ownedFoodIds.length}品目',
                style: const TextStyle(color: Color(0xFF2E7D32)),
              ),
            ),
            TextButton(
              onPressed: controller.clearOwnedFoods,
              child: const Text('クリア'),
            ),
          ],
        ),
      ),
    );
  }
}
