import 'dart:convert';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:http/http.dart' as http;
import '../models/food.dart';
import '../models/dish.dart';
import '../models/menu_plan.dart';
import '../models/settings.dart';

class ApiService {
  // Web: 同一オリジン（相対パス）, モバイル: localhost
  static String get baseUrl {
    if (kIsWeb) {
      return Uri.base.resolve('/api/v1').toString();
    }
    return 'http://localhost:8000/api/v1';
  }

  // ========== 食品API ==========

  Future<List<Food>> getFoods({String? category}) async {
    String url = '$baseUrl/foods';
    if (category != null) {
      url += '?category=$category';
    }

    final response = await http.get(Uri.parse(url));
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(utf8.decode(response.bodyBytes));
      return data.map((f) => Food.fromJson(f)).toList();
    } else {
      throw Exception('Failed to load foods');
    }
  }

  Future<List<Map<String, dynamic>>> searchFoods({
    String? query,
    String? category,
    int limit = 20,
  }) async {
    final params = <String, String>{};
    if (query != null && query.isNotEmpty) params['q'] = query;
    if (category != null) params['category'] = category;
    params['limit'] = limit.toString();

    final uri = Uri.parse('$baseUrl/foods/search').replace(queryParameters: params);
    final response = await http.get(uri);

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(utf8.decode(response.bodyBytes));
      return data.map((f) => f as Map<String, dynamic>).toList();
    } else {
      throw Exception('Failed to search foods');
    }
  }

  Future<List<String>> getCategories() async {
    final response = await http.get(Uri.parse('$baseUrl/categories'));
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(utf8.decode(response.bodyBytes));
      return data.map((c) => c.toString()).toList();
    } else {
      throw Exception('Failed to load categories');
    }
  }

  Future<List<String>> getFoodCategories() async {
    final response = await http.get(Uri.parse('$baseUrl/food-categories'));
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(utf8.decode(response.bodyBytes));
      return data.map((c) => c.toString()).toList();
    } else {
      throw Exception('Failed to load food categories');
    }
  }

  // ========== 料理API ==========

  Future<List<Dish>> getDishes({String? category, String? mealType}) async {
    final params = <String, String>{};
    if (category != null) params['category'] = category;
    if (mealType != null) params['meal_type'] = mealType;

    final uri = Uri.parse('$baseUrl/dishes').replace(queryParameters: params.isEmpty ? null : params);
    final response = await http.get(uri);

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(utf8.decode(response.bodyBytes));
      return data.map((d) => Dish.fromJson(d)).toList();
    } else {
      throw Exception('Failed to load dishes');
    }
  }

  Future<Dish> getDish(int dishId) async {
    final response = await http.get(Uri.parse('$baseUrl/dishes/$dishId'));

    if (response.statusCode == 200) {
      final data = json.decode(utf8.decode(response.bodyBytes));
      return Dish.fromJson(data);
    } else {
      throw Exception('Failed to load dish');
    }
  }

  Future<List<String>> getDishCategories() async {
    final response = await http.get(Uri.parse('$baseUrl/dish-categories'));
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(utf8.decode(response.bodyBytes));
      return data.map((c) => c.toString()).toList();
    } else {
      throw Exception('Failed to load dish categories');
    }
  }

  Future<RecipeDetails> generateRecipe(int dishId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/dishes/$dishId/generate-recipe'),
    );

    if (response.statusCode == 200) {
      final data = json.decode(utf8.decode(response.bodyBytes));
      return RecipeDetails.fromJson(data);
    } else {
      throw Exception('Failed to generate recipe');
    }
  }

  // ========== 最適化API ==========

  Future<MenuPlan> optimizeMenu({
    List<int> excludedFoodIds = const [],
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/optimize'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'excluded_food_ids': excludedFoodIds,
      }),
    );

    if (response.statusCode == 200) {
      final data = json.decode(utf8.decode(response.bodyBytes));
      return MenuPlan.fromJson(data);
    } else {
      throw Exception('Failed to optimize menu: ${response.body}');
    }
  }

  // UIの「献立ボリューム」をバックエンドの「作り置きレベル」に変換
  // UI: 多め=料理多い → バックエンド: small=調理回数ペナルティ低
  // UI: 少なめ=作り置き重視 → バックエンド: large=調理回数ペナルティ高
  String _invertBatchCookingLevel(String level) {
    switch (level) {
      case 'small':
        return 'large';
      case 'large':
        return 'small';
      default:
        return 'normal';
    }
  }

  Future<MultiDayMenuPlan> optimizeMultiDay({
    int days = 3,
    int people = 2,
    NutrientTarget? target,
    List<Allergen> excludedAllergens = const [],
    List<int> excludedDishIds = const [],
    String batchCookingLevel = 'normal',
    String volumeLevel = 'normal',
    String varietyLevel = 'normal',
  }) async {
    final body = {
      'days': days,
      'people': people,
      'excluded_allergens': excludedAllergens.map((a) => a.displayName).toList(),
      'excluded_dish_ids': excludedDishIds,
      'batch_cooking_level': _invertBatchCookingLevel(batchCookingLevel),
      'volume_level': volumeLevel,
      'variety_level': varietyLevel,
    };

    if (target != null) {
      body['target'] = target.toJson();
    }

    final response = await http.post(
      Uri.parse('$baseUrl/optimize/multi-day'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode(body),
    );

    if (response.statusCode == 200) {
      final data = json.decode(utf8.decode(response.bodyBytes));
      return MultiDayMenuPlan.fromJson(data);
    } else {
      throw Exception('献立の生成に失敗しました: ${response.body}');
    }
  }

  Future<MultiDayMenuPlan> refineMultiDay({
    int days = 3,
    int people = 2,
    NutrientTarget? target,
    List<int> keepDishIds = const [],
    List<int> excludeDishIds = const [],
    List<Allergen> excludedAllergens = const [],
    String batchCookingLevel = 'normal',
    String volumeLevel = 'normal',
    String varietyLevel = 'normal',
  }) async {
    final body = {
      'days': days,
      'people': people,
      'keep_dish_ids': keepDishIds,
      'exclude_dish_ids': excludeDishIds,
      'excluded_allergens': excludedAllergens.map((a) => a.displayName).toList(),
      'batch_cooking_level': _invertBatchCookingLevel(batchCookingLevel),
      'volume_level': volumeLevel,
      'variety_level': varietyLevel,
    };

    if (target != null) {
      body['target'] = target.toJson();
    }

    final response = await http.post(
      Uri.parse('$baseUrl/optimize/multi-day/refine'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode(body),
    );

    if (response.statusCode == 200) {
      final data = json.decode(utf8.decode(response.bodyBytes));
      return MultiDayMenuPlan.fromJson(data);
    } else {
      throw Exception('献立の調整に失敗しました: ${response.body}');
    }
  }

  // ========== アレルゲンAPI ==========

  Future<List<Map<String, String>>> getAllergens() async {
    final response = await http.get(Uri.parse('$baseUrl/allergens'));

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(utf8.decode(response.bodyBytes));
      return data.map((a) => {
        'value': a['value'].toString(),
        'name': a['name'].toString(),
      }).toList();
    } else {
      throw Exception('Failed to load allergens');
    }
  }

  // ========== 設定API ==========

  Future<UserPreferences> getPreferences() async {
    final response = await http.get(Uri.parse('$baseUrl/preferences'));

    if (response.statusCode == 200) {
      final data = json.decode(utf8.decode(response.bodyBytes));
      return UserPreferences.fromJson(data);
    } else {
      throw Exception('Failed to load preferences');
    }
  }

  Future<UserPreferences> updatePreferences(UserPreferences prefs) async {
    final response = await http.put(
      Uri.parse('$baseUrl/preferences'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode(prefs.toJson()),
    );

    if (response.statusCode == 200) {
      final data = json.decode(utf8.decode(response.bodyBytes));
      return UserPreferences.fromJson(data);
    } else {
      throw Exception('Failed to update preferences');
    }
  }

  // ========== ヘルスチェック ==========

  Future<bool> healthCheck() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/health'))
          .timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  Future<Map<String, dynamic>> getHealthStatus() async {
    final response = await http
        .get(Uri.parse('$baseUrl/health'))
        .timeout(const Duration(seconds: 5));

    if (response.statusCode == 200) {
      return json.decode(utf8.decode(response.bodyBytes));
    } else {
      throw Exception('Health check failed');
    }
  }
}
