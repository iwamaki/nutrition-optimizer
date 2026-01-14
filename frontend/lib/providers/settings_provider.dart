import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/settings.dart';

/// 設定状態管理Provider
class SettingsProvider extends ChangeNotifier {
  AppSettings _settings = AppSettings();
  bool _isLoading = false;

  AppSettings get settings => _settings;
  bool get isLoading => _isLoading;

  // 便利なgetters
  int get defaultDays => _settings.defaultDays;
  int get defaultPeople => _settings.defaultPeople;
  Set<Allergen> get excludedAllergens => _settings.excludedAllergens;
  NutrientTarget get nutrientTarget => _settings.nutrientTarget;
  bool get preferBatchCooking => _settings.preferBatchCooking;

  /// 設定を読み込み
  Future<void> loadSettings() async {
    _isLoading = true;
    notifyListeners();

    try {
      final prefs = await SharedPreferences.getInstance();

      final days = prefs.getInt('defaultDays') ?? 3;
      final people = prefs.getInt('defaultPeople') ?? 2;
      final batchCooking = prefs.getBool('preferBatchCooking') ?? false;

      // アレルゲン
      final allergenList = prefs.getStringList('excludedAllergens') ?? [];
      final allergens = allergenList
          .map((a) => Allergen.fromApiValue(a))
          .whereType<Allergen>()
          .toSet();

      // カロリー目標
      final caloriesMin = prefs.getDouble('caloriesMin') ?? 1800;
      final caloriesMax = prefs.getDouble('caloriesMax') ?? 2200;

      _settings = AppSettings(
        defaultDays: days,
        defaultPeople: people,
        excludedAllergens: allergens,
        preferBatchCooking: batchCooking,
        nutrientTarget: NutrientTarget(
          caloriesMin: caloriesMin,
          caloriesMax: caloriesMax,
        ),
      );
    } catch (e) {
      // デフォルト値を使用
      _settings = AppSettings();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// 設定を保存
  Future<void> _saveSettings() async {
    try {
      final prefs = await SharedPreferences.getInstance();

      await prefs.setInt('defaultDays', _settings.defaultDays);
      await prefs.setInt('defaultPeople', _settings.defaultPeople);
      await prefs.setBool('preferBatchCooking', _settings.preferBatchCooking);
      await prefs.setStringList(
        'excludedAllergens',
        _settings.excludedAllergens.map((a) => a.displayName).toList(),
      );
      await prefs.setDouble('caloriesMin', _settings.nutrientTarget.caloriesMin);
      await prefs.setDouble('caloriesMax', _settings.nutrientTarget.caloriesMax);
    } catch (e) {
      // 保存失敗を無視
    }
  }

  /// デフォルト日数を設定
  Future<void> setDefaultDays(int days) async {
    _settings = _settings.copyWith(defaultDays: days.clamp(1, 7));
    notifyListeners();
    await _saveSettings();
  }

  /// デフォルト人数を設定
  Future<void> setDefaultPeople(int people) async {
    _settings = _settings.copyWith(defaultPeople: people.clamp(1, 6));
    notifyListeners();
    await _saveSettings();
  }

  /// アレルゲンを切り替え
  Future<void> toggleAllergen(Allergen allergen) async {
    final current = Set<Allergen>.from(_settings.excludedAllergens);
    if (current.contains(allergen)) {
      current.remove(allergen);
    } else {
      current.add(allergen);
    }
    _settings = _settings.copyWith(excludedAllergens: current);
    notifyListeners();
    await _saveSettings();
  }

  /// アレルゲンを設定
  Future<void> setExcludedAllergens(Set<Allergen> allergens) async {
    _settings = _settings.copyWith(excludedAllergens: allergens);
    notifyListeners();
    await _saveSettings();
  }

  /// 作り置き優先を設定
  Future<void> setPreferBatchCooking(bool value) async {
    _settings = _settings.copyWith(preferBatchCooking: value);
    notifyListeners();
    await _saveSettings();
  }

  /// カロリー範囲を設定
  Future<void> setCaloriesRange(double min, double max) async {
    _settings = _settings.copyWith(
      nutrientTarget: _settings.nutrientTarget.copyWith(
        caloriesMin: min,
        caloriesMax: max,
      ),
    );
    notifyListeners();
    await _saveSettings();
  }

  /// 設定をリセット
  Future<void> resetSettings() async {
    _settings = AppSettings();
    notifyListeners();
    await _saveSettings();
  }
}
