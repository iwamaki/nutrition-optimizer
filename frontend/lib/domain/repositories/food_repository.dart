import '../entities/dish.dart';

/// 食品・料理リポジトリのインターフェース
abstract class FoodRepository {
  /// 基本食材一覧を取得（正規化された食材マスタ）
  Future<List<Map<String, dynamic>>> getIngredients({String? category});

  /// 基本食材カテゴリ一覧を取得
  Future<List<String>> getIngredientCategories();

  /// 料理一覧を取得
  Future<List<Dish>> getDishes({String? category, String? mealType});

  /// 料理詳細を取得
  Future<Dish> getDish(int dishId);

  /// 料理カテゴリ一覧を取得
  Future<List<String>> getDishCategories();

  /// レシピ詳細を生成（Gemini API）
  Future<RecipeDetails> generateRecipe(int dishId);

  /// アレルゲン一覧を取得
  Future<List<Map<String, String>>> getAllergens();
}
