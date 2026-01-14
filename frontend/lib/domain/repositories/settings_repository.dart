import '../entities/settings.dart';

/// 設定リポジトリのインターフェース
abstract class SettingsRepository {
  /// ユーザー設定を取得（API）
  Future<UserPreferences> getPreferences();

  /// ユーザー設定を更新（API）
  Future<UserPreferences> updatePreferences(UserPreferences prefs);

  /// ローカル設定を読み込み
  Future<LocalSettings> loadLocalSettings();

  /// ローカル設定を保存
  Future<void> saveLocalSettings(LocalSettings settings);

  /// ヘルスチェック
  Future<bool> healthCheck();

  /// ヘルスステータスを取得
  Future<Map<String, dynamic>> getHealthStatus();
}

/// ローカルに保存する設定
class LocalSettings {
  final int defaultDays;
  final int defaultPeople;
  final Set<Allergen> excludedAllergens;
  final NutrientTarget nutrientTarget;

  const LocalSettings({
    this.defaultDays = 3,
    this.defaultPeople = 2,
    this.excludedAllergens = const {},
    this.nutrientTarget = const NutrientTarget(),
  });

  LocalSettings copyWith({
    int? defaultDays,
    int? defaultPeople,
    Set<Allergen>? excludedAllergens,
    NutrientTarget? nutrientTarget,
  }) {
    return LocalSettings(
      defaultDays: defaultDays ?? this.defaultDays,
      defaultPeople: defaultPeople ?? this.defaultPeople,
      excludedAllergens: excludedAllergens ?? this.excludedAllergens,
      nutrientTarget: nutrientTarget ?? this.nutrientTarget,
    );
  }

  Map<String, dynamic> toJson() => {
        'defaultDays': defaultDays,
        'defaultPeople': defaultPeople,
        'excludedAllergens':
            excludedAllergens.map((a) => a.name).toList(),
        'nutrientTarget': nutrientTarget.toJson(),
      };

  factory LocalSettings.fromJson(Map<String, dynamic> json) {
    return LocalSettings(
      defaultDays: json['defaultDays'] ?? 3,
      defaultPeople: json['defaultPeople'] ?? 2,
      excludedAllergens: (json['excludedAllergens'] as List<dynamic>?)
              ?.map((e) => Allergen.values.firstWhere(
                    (a) => a.name == e,
                    orElse: () => Allergen.egg,
                  ))
              .toSet() ??
          {},
      nutrientTarget: json['nutrientTarget'] != null
          ? NutrientTarget.fromJson(json['nutrientTarget'])
          : const NutrientTarget(),
    );
  }
}
