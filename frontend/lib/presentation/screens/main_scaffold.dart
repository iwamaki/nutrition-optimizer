import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/shopping_provider.dart';
import 'home_screen.dart';
import 'calendar_screen.dart';
import 'shopping_screen.dart';
import 'settings_screen.dart';

/// メインスキャフォールド（タブナビゲーション）- Riverpod版
class MainScaffold extends ConsumerStatefulWidget {
  const MainScaffold({super.key});

  @override
  ConsumerState<MainScaffold> createState() => _MainScaffoldState();
}

class _MainScaffoldState extends ConsumerState<MainScaffold> {
  int _currentIndex = 0;

  final List<Widget> _screens = const [
    HomeScreen(),
    CalendarScreen(),
    ShoppingScreen(),
    SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final shoppingState = ref.watch(shoppingNotifierProvider);

    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        destinations: [
          NavigationDestination(
            icon: const Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home, color: colorScheme.primary),
            label: 'ホーム',
          ),
          NavigationDestination(
            icon: const Icon(Icons.calendar_month_outlined),
            selectedIcon: Icon(Icons.calendar_month, color: colorScheme.primary),
            label: '週間',
          ),
          NavigationDestination(
            icon: _buildShoppingIcon(shoppingState.uncheckedCount),
            selectedIcon: Icon(Icons.shopping_cart, color: colorScheme.primary),
            label: '買い物',
          ),
          NavigationDestination(
            icon: const Icon(Icons.settings_outlined),
            selectedIcon: Icon(Icons.settings, color: colorScheme.primary),
            label: '設定',
          ),
        ],
      ),
    );
  }

  Widget _buildShoppingIcon(int uncheckedCount) {
    if (uncheckedCount > 0) {
      return Badge(
        label: Text('$uncheckedCount'),
        child: const Icon(Icons.shopping_cart_outlined),
      );
    }
    return const Icon(Icons.shopping_cart_outlined);
  }
}
