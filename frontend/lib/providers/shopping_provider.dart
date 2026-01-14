import 'package:flutter/foundation.dart';
import '../models/menu_plan.dart';

/// 買い物リスト状態管理Provider
class ShoppingProvider extends ChangeNotifier {
  List<ShoppingItem> _items = [];
  int _days = 0;
  int _people = 0;
  DateTime _startDate = DateTime.now();

  List<ShoppingItem> get items => _items;
  int get days => _days;
  int get people => _people;
  DateTime get startDate => _startDate;
  DateTime get endDate => _startDate.add(Duration(days: _days - 1));

  /// チェック済みアイテム数
  int get checkedCount => _items.where((i) => i.isChecked).length;

  /// 未チェックアイテム数
  int get uncheckedCount => _items.where((i) => !i.isChecked).length;

  /// 全てチェック済みか
  bool get allChecked => _items.isNotEmpty && checkedCount == _items.length;

  /// カテゴリ別にグループ化
  Map<String, List<ShoppingItem>> get groupedByCategory {
    final groups = <String, List<ShoppingItem>>{};
    for (final item in _items) {
      groups.putIfAbsent(item.category, () => []).add(item);
    }
    return groups;
  }

  /// 未チェックのアイテムのみカテゴリ別にグループ化
  Map<String, List<ShoppingItem>> get uncheckedGroupedByCategory {
    final groups = <String, List<ShoppingItem>>{};
    for (final item in _items.where((i) => !i.isChecked)) {
      groups.putIfAbsent(item.category, () => []).add(item);
    }
    return groups;
  }

  /// 献立から買い物リストを更新
  void updateFromPlan(MultiDayMenuPlan plan, {DateTime? startDate}) {
    _items = plan.shoppingList;
    _days = plan.days;
    _people = plan.people;
    _startDate = startDate ?? DateTime.now();
    notifyListeners();
  }

  /// アイテムのチェック状態を切り替え
  void toggleItem(ShoppingItem item) {
    item.isChecked = !item.isChecked;
    notifyListeners();
  }

  /// 全てチェック
  void checkAll() {
    for (final item in _items) {
      item.isChecked = true;
    }
    notifyListeners();
  }

  /// 全てのチェックを外す
  void uncheckAll() {
    for (final item in _items) {
      item.isChecked = false;
    }
    notifyListeners();
  }

  /// リストをクリア
  void clear() {
    _items = [];
    _days = 0;
    _people = 0;
    _startDate = DateTime.now();
    notifyListeners();
  }

  /// 日付を「1/15(月)」形式にフォーマット
  String formatDate(DateTime date) {
    const weekdays = ['月', '火', '水', '木', '金', '土', '日'];
    final weekday = weekdays[date.weekday - 1];
    return '${date.month}/${date.day}($weekday)';
  }

  /// 日付範囲の表示用文字列
  String get dateRangeDisplay {
    if (_days <= 1) {
      return formatDate(_startDate);
    }
    return '${formatDate(_startDate)}〜${formatDate(endDate)}';
  }

  /// 共有用テキストを生成
  String toShareText() {
    final buffer = StringBuffer();
    buffer.writeln('買い物リスト（$dateRangeDisplay $_people人分）');
    buffer.writeln('');

    final groups = groupedByCategory;
    for (final category in groups.keys) {
      buffer.writeln('【$category】');
      for (final item in groups[category]!) {
        final check = item.isChecked ? '✓' : '□';
        buffer.writeln('$check ${item.foodName} ${item.amountDisplay}');
      }
      buffer.writeln('');
    }

    return buffer.toString();
  }

  /// カテゴリの表示順
  static const categoryOrder = [
    '野菜類',
    '果実類',
    '肉類',
    '魚介類',
    '卵類',
    '乳類',
    '穀類',
    '豆類',
    '調味料及び香辛料類',
    'その他',
  ];

  /// ソートされたカテゴリリスト
  List<String> get sortedCategories {
    final categories = groupedByCategory.keys.toList();
    categories.sort((a, b) {
      final indexA = categoryOrder.indexOf(a);
      final indexB = categoryOrder.indexOf(b);
      if (indexA == -1 && indexB == -1) return a.compareTo(b);
      if (indexA == -1) return 1;
      if (indexB == -1) return -1;
      return indexA.compareTo(indexB);
    });
    return categories;
  }
}
