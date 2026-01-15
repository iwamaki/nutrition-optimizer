import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../providers/settings_provider.dart';
import '../generate_modal_controller.dart';

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
  @override
  void initState() {
    super.initState();
    // お気に入り料理を読み込み
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final favoriteIds = ref.read(settingsNotifierProvider).favoriteDishIds;
      ref.read(generateModalControllerProvider.notifier).loadFavoriteDishes(favoriteIds);
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(generateModalControllerProvider);
    final controller = ref.read(generateModalControllerProvider.notifier);

    return ListView(
      controller: widget.scrollController,
      padding: const EdgeInsets.all(16),
      children: [
        _buildInfoCard(context),
        const SizedBox(height: 16),
        _buildFavoritesList(context, state),
        if (state.favoriteDishes.isNotEmpty) ...[
          const SizedBox(height: 16),
          _buildGuaranteeOption(context, state, controller),
        ],
      ],
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

    if (state.favoriteDishes.isEmpty) {
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
                  'お気に入り料理 (${state.favoriteDishes.length}件)',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
              ],
            ),
            const SizedBox(height: 12),
            ...state.favoriteDishes.map((dish) => _buildDishItem(context, dish)),
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
            if (state.guaranteeFavorites && state.favoriteDishes.length > state.days * 3) ...[
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
                        'お気に入りが${state.favoriteDishes.length}件あり、${state.days}日分の献立（${state.days * 3}食）に収まりきらない可能性があります',
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
