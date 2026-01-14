import '../entities/food.dart';
import '../entities/dish.dart';

/// 食品・料理リポジトリのインターフェース
abstract class FoodRepository {
  /// 食品一覧を取得
  Future<List<Food>> getFoods({String? category});

  /// 食品を検索
  Future<List<Map<String, dynamic>>> searchFoods({
    String? query,
    String? category,
    int limit = 20,
  });

  /// 食品カテゴリ一覧を取得
  Future<List<String>> getFoodCategories();

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
