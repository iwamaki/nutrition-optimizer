class Food {
  final int id;
  final String name;
  final String category;
  final double calories;
  final double protein;
  final double fat;
  final double carbohydrate;
  final double fiber;
  // ミネラル
  final double sodium;
  final double potassium;
  final double calcium;
  final double magnesium;
  final double iron;
  final double zinc;
  // ビタミン
  final double vitaminA;
  final double vitaminD;
  final double vitaminE;
  final double vitaminK;
  final double vitaminB1;
  final double vitaminB2;
  final double vitaminB6;
  final double vitaminB12;
  final double folate;
  final double vitaminC;
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
    required this.potassium,
    required this.calcium,
    required this.magnesium,
    required this.iron,
    required this.zinc,
    required this.vitaminA,
    required this.vitaminD,
    required this.vitaminE,
    required this.vitaminK,
    required this.vitaminB1,
    required this.vitaminB2,
    required this.vitaminB6,
    required this.vitaminB12,
    required this.folate,
    required this.vitaminC,
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
      // ミネラル
      sodium: (json['sodium'] ?? 0).toDouble(),
      potassium: (json['potassium'] ?? 0).toDouble(),
      calcium: (json['calcium'] ?? 0).toDouble(),
      magnesium: (json['magnesium'] ?? 0).toDouble(),
      iron: (json['iron'] ?? 0).toDouble(),
      zinc: (json['zinc'] ?? 0).toDouble(),
      // ビタミン
      vitaminA: (json['vitamin_a'] ?? 0).toDouble(),
      vitaminD: (json['vitamin_d'] ?? 0).toDouble(),
      vitaminE: (json['vitamin_e'] ?? 0).toDouble(),
      vitaminK: (json['vitamin_k'] ?? 0).toDouble(),
      vitaminB1: (json['vitamin_b1'] ?? 0).toDouble(),
      vitaminB2: (json['vitamin_b2'] ?? 0).toDouble(),
      vitaminB6: (json['vitamin_b6'] ?? 0).toDouble(),
      vitaminB12: (json['vitamin_b12'] ?? 0).toDouble(),
      folate: (json['folate'] ?? 0).toDouble(),
      vitaminC: (json['vitamin_c'] ?? 0).toDouble(),
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
