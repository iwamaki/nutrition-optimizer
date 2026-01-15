import 'package:riverpod_annotation/riverpod_annotation.dart';
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
  Future<List<Map<String, dynamic>>> getIngredients({String? category}) {
    return _apiService.getIngredients(category: category);
  }

  @override
  Future<List<String>> getIngredientCategories() {
    return _apiService.getIngredientCategories();
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
