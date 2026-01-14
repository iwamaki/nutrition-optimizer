import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../domain/entities/food.dart';
import '../../domain/entities/dish.dart';
import '../../domain/repositories/food_repository.dart';
import '../datasources/api_service.dart';
import 'menu_repository_impl.dart';

part 'food_repository_impl.g.dart';

/// 食品・料理リポジトリの実装
class FoodRepositoryImpl implements FoodRepository {
  final ApiService _apiService;

  FoodRepositoryImpl(this._apiService);

  @override
  Future<List<Food>> getFoods({String? category}) {
    return _apiService.getFoods(category: category);
  }

  @override
  Future<List<Map<String, dynamic>>> searchFoods({
    String? query,
    String? category,
    int limit = 20,
  }) {
    return _apiService.searchFoods(
      query: query,
      category: category,
      limit: limit,
    );
  }

  @override
  Future<List<String>> getFoodCategories() {
    return _apiService.getFoodCategories();
  }

  @override
  Future<List<Dish>> getDishes({String? category, String? mealType}) {
    return _apiService.getDishes(category: category, mealType: mealType);
  }

  @override
  Future<Dish> getDish(int dishId) {
    return _apiService.getDish(dishId);
  }

  @override
  Future<List<String>> getDishCategories() {
    return _apiService.getDishCategories();
  }

  @override
  Future<RecipeDetails> generateRecipe(int dishId) {
    return _apiService.generateRecipe(dishId);
  }

  @override
  Future<List<Map<String, String>>> getAllergens() {
    return _apiService.getAllergens();
  }
}

/// FoodRepository Provider
@riverpod
FoodRepository foodRepository(FoodRepositoryRef ref) {
  return FoodRepositoryImpl(ref.watch(apiServiceProvider));
}
