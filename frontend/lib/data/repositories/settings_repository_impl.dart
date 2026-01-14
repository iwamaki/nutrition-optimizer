import 'dart:convert';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../domain/entities/settings.dart';
import '../../domain/repositories/settings_repository.dart';
import '../datasources/api_service.dart';
import 'menu_repository_impl.dart';

part 'settings_repository_impl.g.dart';

/// 設定リポジトリの実装
class SettingsRepositoryImpl implements SettingsRepository {
  final ApiService _apiService;
  static const String _localSettingsKey = 'local_settings';

  SettingsRepositoryImpl(this._apiService);

  @override
  Future<UserPreferences> getPreferences() {
    return _apiService.getPreferences();
  }

  @override
  Future<UserPreferences> updatePreferences(UserPreferences prefs) {
    return _apiService.updatePreferences(prefs);
  }

  @override
  Future<LocalSettings> loadLocalSettings() async {
    final prefs = await SharedPreferences.getInstance();
    final jsonStr = prefs.getString(_localSettingsKey);
    if (jsonStr == null) {
      return const LocalSettings();
    }
    try {
      final json = jsonDecode(jsonStr) as Map<String, dynamic>;
      return LocalSettings.fromJson(json);
    } catch (e) {
      return const LocalSettings();
    }
  }

  @override
  Future<void> saveLocalSettings(LocalSettings settings) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_localSettingsKey, jsonEncode(settings.toJson()));
  }

  @override
  Future<bool> healthCheck() {
    return _apiService.healthCheck();
  }

  @override
  Future<Map<String, dynamic>> getHealthStatus() {
    return _apiService.getHealthStatus();
  }
}

/// SettingsRepository Provider
@riverpod
SettingsRepository settingsRepository(SettingsRepositoryRef ref) {
  return SettingsRepositoryImpl(ref.watch(apiServiceProvider));
}
