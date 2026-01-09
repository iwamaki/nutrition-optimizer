class Food {
  final int id;
  final String name;
  final String category;
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
  final double maxPortion;

  Food({
    required this.id,
    required this.name,
    required this.category,
    required this.calories,
    required this.protein,
    required this.fat,
    required this.carbohydrate,
    required this.fiber,
    required this.sodium,
    required this.calcium,
    required this.iron,
    required this.vitaminA,
    required this.vitaminC,
    required this.vitaminD,
    required this.maxPortion,
  });

  factory Food.fromJson(Map<String, dynamic> json) {
    return Food(
      id: json['id'],
      name: json['name'],
      category: json['category'],
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
      maxPortion: (json['max_portion'] ?? 300).toDouble(),
    );
  }
}

class FoodPortion {
  final Food food;
  final double amount;

  FoodPortion({required this.food, required this.amount});

  factory FoodPortion.fromJson(Map<String, dynamic> json) {
    return FoodPortion(
      food: Food.fromJson(json['food']),
      amount: (json['amount'] ?? 0).toDouble(),
    );
  }
}

class Meal {
  final String name;
  final List<FoodPortion> foods;
  final double totalCalories;
  final double totalProtein;
  final double totalFat;
  final double totalCarbohydrate;

  Meal({
    required this.name,
    required this.foods,
    required this.totalCalories,
    required this.totalProtein,
    required this.totalFat,
    required this.totalCarbohydrate,
  });

  factory Meal.fromJson(Map<String, dynamic> json) {
    return Meal(
      name: json['name'],
      foods: (json['foods'] as List)
          .map((f) => FoodPortion.fromJson(f))
          .toList(),
      totalCalories: (json['total_calories'] ?? 0).toDouble(),
      totalProtein: (json['total_protein'] ?? 0).toDouble(),
      totalFat: (json['total_fat'] ?? 0).toDouble(),
      totalCarbohydrate: (json['total_carbohydrate'] ?? 0).toDouble(),
    );
  }

  String get displayName {
    switch (name) {
      case 'breakfast':
        return '朝食';
      case 'lunch':
        return '昼食';
      case 'dinner':
        return '夕食';
      default:
        return name;
    }
  }
}

class MenuPlan {
  final Meal breakfast;
  final Meal lunch;
  final Meal dinner;
  final Map<String, double> totalNutrients;
  final Map<String, double> achievementRate;

  MenuPlan({
    required this.breakfast,
    required this.lunch,
    required this.dinner,
    required this.totalNutrients,
    required this.achievementRate,
  });

  factory MenuPlan.fromJson(Map<String, dynamic> json) {
    return MenuPlan(
      breakfast: Meal.fromJson(json['breakfast']),
      lunch: Meal.fromJson(json['lunch']),
      dinner: Meal.fromJson(json['dinner']),
      totalNutrients: Map<String, double>.from(
        (json['total_nutrients'] as Map).map(
          (k, v) => MapEntry(k.toString(), (v ?? 0).toDouble()),
        ),
      ),
      achievementRate: Map<String, double>.from(
        (json['achievement_rate'] as Map).map(
          (k, v) => MapEntry(k.toString(), (v ?? 0).toDouble()),
        ),
      ),
    );
  }

  double get totalCalories =>
      breakfast.totalCalories + lunch.totalCalories + dinner.totalCalories;
}
