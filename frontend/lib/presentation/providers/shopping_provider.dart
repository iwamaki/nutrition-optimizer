import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../domain/entities/menu_plan.dart';

part 'shopping_provider.g.dart';

/// 買い物リストの状態
class ShoppingState {
  final List<ShoppingItem> items;
  final int days;
  final int people;
  final DateTime startDate;

  ShoppingState({
    this.items = const [],
    this.days = 0,
    this.people = 0,
    DateTime? startDate,
  }) : startDate = startDate ?? DateTime.now();

  ShoppingState copyWith({
    List<ShoppingItem>? items,
    int? days,
    int? people,
    DateTime? startDate,
  }) {
    return ShoppingState(
      items: items ?? this.items,
      days: days ?? this.days,
      people: people ?? this.people,
      startDate: startDate ?? this.startDate,
    );
  }

  DateTime get endDate => startDate.add(Duration(days: days - 1));

  int get checkedCount => items.where((i) => i.isChecked).length;
  int get uncheckedCount => items.where((i) => !i.isChecked).length;
  bool get allChecked => items.isNotEmpty && checkedCount == items.length;

  Map<String, List<ShoppingItem>> get groupedByCategory {
    final groups = <String, List<ShoppingItem>>{};
    for (final item in items) {
      groups.putIfAbsent(item.category, () => []).add(item);
    }
    return groups;
  }

  Map<String, List<ShoppingItem>> get uncheckedGroupedByCategory {
    final groups = <String, List<ShoppingItem>>{};
    for (final item in items.where((i) => !i.isChecked)) {
      groups.putIfAbsent(item.category, () => []).add(item);
    }
    return groups;
  }

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

  String formatDate(DateTime date) {
    const weekdays = ['月', '火', '水', '木', '金', '土', '日'];
    final weekday = weekdays[date.weekday - 1];
    return '${date.month}/${date.day}($weekday)';
  }

  String get dateRangeDisplay {
    if (days <= 1) {
      return formatDate(startDate);
    }
    return '${formatDate(startDate)}〜${formatDate(endDate)}';
  }

  String toShareText() {
    final buffer = StringBuffer();
    buffer.writeln('買い物リスト（$dateRangeDisplay $people人分）');
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
}

/// 買い物リスト管理Notifier
@riverpod
class ShoppingNotifier extends _$ShoppingNotifier {
  @override
  ShoppingState build() => ShoppingState();

  void updateFromPlan(MultiDayMenuPlan plan, {DateTime? startDate}) {
    state = ShoppingState(
      items: List<ShoppingItem>.from(plan.shoppingList),
      days: plan.days,
      people: plan.people,
      startDate: startDate ?? DateTime.now(),
    );
  }

  void toggleItem(int index) {
    if (index < 0 || index >= state.items.length) return;

    final newItems = List<ShoppingItem>.from(state.items);
    newItems[index].isChecked = !newItems[index].isChecked;
    state = state.copyWith(items: newItems);
  }

  void toggleItemByFood(String foodName) {
    final newItems = List<ShoppingItem>.from(state.items);
    for (final item in newItems) {
      if (item.foodName == foodName) {
        item.isChecked = !item.isChecked;
        break;
      }
    }
    state = state.copyWith(items: newItems);
  }

  void checkAll() {
    final newItems = List<ShoppingItem>.from(state.items);
    for (final item in newItems) {
      item.isChecked = true;
    }
    state = state.copyWith(items: newItems);
  }

  void uncheckAll() {
    final newItems = List<ShoppingItem>.from(state.items);
    for (final item in newItems) {
      item.isChecked = false;
    }
    state = state.copyWith(items: newItems);
  }

  void clear() {
    state = ShoppingState();
  }
}
