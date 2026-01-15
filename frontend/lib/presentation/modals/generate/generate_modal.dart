import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/menu_provider.dart';
import '../../providers/settings_provider.dart';
import '../../providers/shopping_provider.dart';
import 'generate_modal_controller.dart';
import 'widgets/step_basic_settings.dart';
import 'widgets/step_favorites.dart';
import 'widgets/step_owned_foods.dart';
import 'widgets/step_confirmation.dart';

/// 献立生成モーダル（4ステップウィザード）
class GenerateModalNew extends ConsumerStatefulWidget {
  const GenerateModalNew({super.key});

  @override
  ConsumerState<GenerateModalNew> createState() => _GenerateModalNewState();
}

class _GenerateModalNewState extends ConsumerState<GenerateModalNew> {
  @override
  void initState() {
    super.initState();
    // 設定から初期値を読み込み
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final settings = ref.read(settingsNotifierProvider);
      ref.read(generateModalControllerProvider.notifier).initFromSettings(
            defaultDays: settings.defaultDays,
            defaultPeople: settings.defaultPeople,
            excludedAllergens: settings.excludedAllergens,
          );
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(generateModalControllerProvider);
    final controller = ref.read(generateModalControllerProvider.notifier);

    return DraggableScrollableSheet(
      initialChildSize: 0.9,
      minChildSize: 0.5,
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
              _buildHeader(context, state),
              _buildStepIndicator(context, state),
              const Divider(height: 1),
              Expanded(
                child: _buildStepContent(scrollController, state),
              ),
              _buildFooter(context, state, controller),
            ],
          ),
        );
      },
    );
  }

  Widget _buildHeader(BuildContext context, GenerateModalState state) {
    final titles = ['基本設定', 'お気に入り', '手持ち食材', '献立確認'];
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.primary,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
      ),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.close),
            color: Theme.of(context).colorScheme.onPrimary,
            onPressed: () => Navigator.pop(context),
          ),
          Expanded(
            child: Text(
              '献立を生成 - ${titles[state.currentStep]}',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onPrimary,
                  ),
              textAlign: TextAlign.center,
            ),
          ),
          const SizedBox(width: 48),
        ],
      ),
    );
  }

  Widget _buildStepIndicator(BuildContext context, GenerateModalState state) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          _buildStepDot(context, state, 0, '基本'),
          _buildStepLine(context, state, 0),
          _buildStepDot(context, state, 1, 'お気に入り'),
          _buildStepLine(context, state, 1),
          _buildStepDot(context, state, 2, '食材'),
          _buildStepLine(context, state, 2),
          _buildStepDot(context, state, 3, '確認'),
        ],
      ),
    );
  }

  Widget _buildStepDot(
    BuildContext context,
    GenerateModalState state,
    int step,
    String label,
  ) {
    final isActive = state.currentStep >= step;
    final isCurrent = state.currentStep == step;
    final colorScheme = Theme.of(context).colorScheme;

    return Column(
      children: [
        Container(
          width: 32,
          height: 32,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: isActive ? colorScheme.primary : colorScheme.surfaceContainerHighest,
            border: isCurrent
                ? Border.all(color: colorScheme.primary, width: 2)
                : null,
          ),
          child: Center(
            child: isActive
                ? Icon(
                    step < state.currentStep ? Icons.check : Icons.circle,
                    size: 16,
                    color: colorScheme.onPrimary,
                  )
                : Text(
                    '${step + 1}',
                    style: TextStyle(color: colorScheme.outline),
                  ),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: TextStyle(
            fontSize: 10,
            color: isActive ? colorScheme.primary : colorScheme.outline,
          ),
        ),
      ],
    );
  }

  Widget _buildStepLine(
    BuildContext context,
    GenerateModalState state,
    int afterStep,
  ) {
    final isActive = state.currentStep > afterStep;
    return Container(
      width: 40,
      height: 2,
      margin: const EdgeInsets.only(bottom: 16),
      color: isActive
          ? Theme.of(context).colorScheme.primary
          : Theme.of(context).colorScheme.outline.withValues(alpha: 0.3),
    );
  }

  Widget _buildStepContent(
    ScrollController scrollController,
    GenerateModalState state,
  ) {
    switch (state.currentStep) {
      case 0:
        return StepBasicSettings(scrollController: scrollController);
      case 1:
        return StepFavorites(scrollController: scrollController);
      case 2:
        return StepOwnedFoods(scrollController: scrollController);
      case 3:
        return StepConfirmation(
          scrollController: scrollController,
          onRetry: () {
            ref.read(generateModalControllerProvider.notifier).generatePlan(
                  target: ref.read(settingsNotifierProvider).nutrientTarget,
                );
          },
        );
      default:
        return const SizedBox.shrink();
    }
  }

  Widget _buildFooter(
    BuildContext context,
    GenerateModalState state,
    GenerateModalController controller,
  ) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.1),
            blurRadius: 4,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Row(
        children: [
          if (state.currentStep > 0)
            Expanded(
              child: OutlinedButton(
                onPressed: controller.previousStep,
                child: const Text('← 戻る'),
              ),
            ),
          if (state.currentStep > 0) const SizedBox(width: 16),
          if (state.currentStep == 3 && state.generatedPlan != null) ...[
            Expanded(
              child: OutlinedButton.icon(
                onPressed: state.isGenerating
                    ? null
                    : () => controller.regeneratePlan(
                          target: ref.read(settingsNotifierProvider).nutrientTarget,
                        ),
                icon: const Icon(Icons.refresh),
                label: const Text('再生成'),
              ),
            ),
            const SizedBox(width: 16),
          ],
          Expanded(
            flex: state.currentStep == 3 && state.generatedPlan != null ? 1 : 2,
            child: FilledButton(
              onPressed: state.isGenerating ? null : () => _handleNext(state, controller),
              child: Text(_getNextButtonLabel(state)),
            ),
          ),
        ],
      ),
    );
  }

  String _getNextButtonLabel(GenerateModalState state) {
    switch (state.currentStep) {
      case 0:
        return '次へ →';
      case 1:
        return '次へ →';
      case 2:
        return '生成 →';
      case 3:
        return state.generatedPlan != null ? '✓ 確定' : '生成';
      default:
        return '次へ →';
    }
  }

  void _handleNext(GenerateModalState state, GenerateModalController controller) {
    switch (state.currentStep) {
      case 0:
        controller.nextStep();
        break;
      case 1:
        controller.nextStep();
        break;
      case 2:
        controller.nextStep();
        break;
      case 3:
        if (state.generatedPlan != null) {
          _confirmPlan(state);
        } else {
          controller.generatePlan(
            target: ref.read(settingsNotifierProvider).nutrientTarget,
          );
        }
        break;
    }
  }

  void _confirmPlan(GenerateModalState state) {
    if (state.generatedPlan != null) {
      // 献立カレンダーに反映
      ref.read(menuNotifierProvider.notifier).setPlan(state.generatedPlan!);
      // 買い物リストに反映
      ref.read(shoppingNotifierProvider.notifier).updateFromPlan(state.generatedPlan!);
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('献立を生成しました')),
      );
    }
  }
}
