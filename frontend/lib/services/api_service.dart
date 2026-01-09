import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/food.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:8000/api/v1';

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

  Future<List<String>> getCategories() async {
    final response = await http.get(Uri.parse('$baseUrl/categories'));
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(utf8.decode(response.bodyBytes));
      return data.map((c) => c.toString()).toList();
    } else {
      throw Exception('Failed to load categories');
    }
  }

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
}
