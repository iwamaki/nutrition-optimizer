import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/settings_provider.dart';
import '../providers/shopping_provider.dart';
import 'home_screen.dart';
import 'calendar_screen.dart';
import 'shopping_screen.dart';
import 'settings_screen.dart';

/// メインスキャフォールド（タブナビゲーション）
class MainScaffold extends StatefulWidget {
  const MainScaffold({super.key});

  @override
  State<MainScaffold> createState() => _MainScaffoldState();
}

class _MainScaffoldState extends State<MainScaffold> {
  int _currentIndex = 0;

  final List<Widget> _screens = const [
    HomeScreen(),
    CalendarScreen(),
    ShoppingScreen(),
    SettingsScreen(),
  ];

  @override
  void initState() {
    super.initState();
    // 設定を読み込み
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<SettingsProvider>().loadSettings();
    });
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

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
            icon: Consumer<ShoppingProvider>(
              builder: (context, shopping, child) {
                final unchecked = shopping.uncheckedCount;
                if (unchecked > 0) {
                  return Badge(
                    label: Text('$unchecked'),
                    child: const Icon(Icons.shopping_cart_outlined),
                  );
                }
                return const Icon(Icons.shopping_cart_outlined);
              },
            ),
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
}
