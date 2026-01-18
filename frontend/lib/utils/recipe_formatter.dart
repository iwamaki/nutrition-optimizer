import '../domain/entities/dish.dart';

/// レシピの手順に含まれるプレースホルダーを置換するユーティリティ
class RecipeFormatter {
  /// レシピの手順文字列内のプレースホルダーを置換
  ///
  /// プレースホルダー形式: {{ingredient:食材名}}
  /// 例: "{{ingredient:木綿豆腐}}は1cm角に切る" → "木綿豆腐60gは1cm角に切る"（2人前の場合）
  static String formatStep(
    String step,
    List<DishIngredient> ingredients,
    double servings,
  ) {
    final pattern = RegExp(r'\{\{ingredient:([^}]+)\}\}');

    return step.replaceAllMapped(pattern, (match) {
      final name = match.group(1)!;
      final ing = _findIngredient(ingredients, name);

      if (ing == null) {
        // 食材が見つからない場合は名前だけ返す
        return name;
      }

      final scaledAmount = ing.amount * servings;
      return '$name${_formatAmount(scaledAmount)}';
    });
  }

  /// 食材リストから名前で検索
  static DishIngredient? _findIngredient(
    List<DishIngredient> ingredients,
    String name,
  ) {
    // 完全一致を優先
    for (final ing in ingredients) {
      if (ing.foodName == name) {
        return ing;
      }
    }

    // 部分一致
    for (final ing in ingredients) {
      if (ing.foodName?.contains(name) == true || name.contains(ing.foodName ?? '')) {
        return ing;
      }
    }

    return null;
  }

  /// 分量を表示用にフォーマット
  static String _formatAmount(double amount) {
    if (amount >= 1000) {
      return '${(amount / 1000).toStringAsFixed(1)}kg';
    }
    return '${amount.toStringAsFixed(0)}g';
  }

  /// 複数の手順を一括で変換
  static List<String> formatSteps(
    List<String> steps,
    List<DishIngredient> ingredients,
    double servings,
  ) {
    return steps.map((step) => formatStep(step, ingredients, servings)).toList();
  }
}
