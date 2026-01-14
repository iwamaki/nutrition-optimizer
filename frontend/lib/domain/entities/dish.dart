// 料理関連のモデル

/// レシピ詳細
class RecipeDetails {
  final int? prepTime;
  final int? cookTime;
  final int? servings;
  final List<String> steps;
  final String? tips;
  final String? variations;

  RecipeDetails({
    this.prepTime,
    this.cookTime,
    this.servings,
    this.steps = const [],
    this.tips,
    this.variations,
  });

  factory RecipeDetails.fromJson(Map<String, dynamic> json) {
    return RecipeDetails(
      prepTime: json['prep_time'],
      cookTime: json['cook_time'],
      servings: json['servings'],
      steps: (json['steps'] as List?)?.map((e) => e.toString()).toList() ?? [],
      tips: json['tips'],
      variations: json['variations'],
    );
  }
}

/// 料理の材料
class DishIngredient {
  final int foodId;
  final String? foodName;
  final double amount;
  final String cookingMethod;

  DishIngredient({
    required this.foodId,
    this.foodName,
    required this.amount,
    this.cookingMethod = '生',
  });

  factory DishIngredient.fromJson(Map<String, dynamic> json) {
    return DishIngredient(
      foodId: json['food_id'],
      foodName: json['food_name'],
      amount: (json['amount'] ?? 0).toDouble(),
      cookingMethod: json['cooking_method'] ?? '生',
    );
  }
}

/// 料理データモデル
class Dish {
  final int id;
  final String name;
  final String category;
  final List<String> mealTypes;
  final double servingSize;
  final String? description;
  final String? instructions;
  final List<DishIngredient> ingredients;
  final int storageDays;
  final int minServings;
  final int maxServings;
  final double calories;
  final double protein;
  final double fat;
  final double carbohydrate;
  final double fiber;
  final double sodium;
  final double calcium;
  final double iron;
  final double vitaminA;
  final double vitaminC;
  final double vitaminD;
  final RecipeDetails? recipeDetails;

  Dish({
    required this.id,
    required this.name,
    required this.category,
    required this.mealTypes,
    this.servingSize = 1.0,
    this.description,
    this.instructions,
    this.ingredients = const [],
    this.storageDays = 1,
    this.minServings = 1,
    this.maxServings = 4,
    this.calories = 0,
    this.protein = 0,
    this.fat = 0,
    this.carbohydrate = 0,
    this.fiber = 0,
    this.sodium = 0,
    this.calcium = 0,
    this.iron = 0,
    this.vitaminA = 0,
    this.vitaminC = 0,
    this.vitaminD = 0,
    this.recipeDetails,
  });

  factory Dish.fromJson(Map<String, dynamic> json) {
    return Dish(
      id: json['id'],
      name: json['name'],
      category: json['category'],
      mealTypes: (json['meal_types'] as List?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      servingSize: (json['serving_size'] ?? 1.0).toDouble(),
      description: json['description'],
      instructions: json['instructions'],
      ingredients: (json['ingredients'] as List?)
              ?.map((e) => DishIngredient.fromJson(e))
              .toList() ??
          [],
      storageDays: json['storage_days'] ?? 1,
      minServings: json['min_servings'] ?? 1,
      maxServings: json['max_servings'] ?? 4,
      calories: (json['calories'] ?? 0).toDouble(),
      protein: (json['protein'] ?? 0).toDouble(),
      fat: (json['fat'] ?? 0).toDouble(),
      carbohydrate: (json['carbohydrate'] ?? 0).toDouble(),
      fiber: (json['fiber'] ?? 0).toDouble(),
      sodium: (json['sodium'] ?? 0).toDouble(),
      calcium: (json['calcium'] ?? 0).toDouble(),
      iron: (json['iron'] ?? 0).toDouble(),
      vitaminA: (json['vitamin_a'] ?? 0).toDouble(),
      vitaminC: (json['vitamin_c'] ?? 0).toDouble(),
      vitaminD: (json['vitamin_d'] ?? 0).toDouble(),
      recipeDetails: json['recipe_details'] != null
          ? RecipeDetails.fromJson(json['recipe_details'])
          : null,
    );
  }

  String get categoryDisplay {
    switch (category) {
      case '主食':
        return '主食';
      case '主菜':
        return '主菜';
      case '副菜':
        return '副菜';
      case '汁物':
        return '汁物';
      case 'デザート':
        return 'デザート';
      default:
        return category;
    }
  }
}

/// 料理と分量
class DishPortion {
  final Dish dish;
  final double servings;

  DishPortion({
    required this.dish,
    this.servings = 1.0,
  });

  factory DishPortion.fromJson(Map<String, dynamic> json) {
    return DishPortion(
      dish: Dish.fromJson(json['dish']),
      servings: (json['servings'] ?? 1.0).toDouble(),
    );
  }

  double get calories => dish.calories * servings;
  double get protein => dish.protein * servings;
  double get fat => dish.fat * servings;
  double get carbohydrate => dish.carbohydrate * servings;
}
