import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../data/repositories/menu_repository_impl.dart';
import '../providers/settings_provider.dart';
import 'main_scaffold.dart';

class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen> {
  String _statusMessage = '読み込み中...';
  bool _hasError = false;

  @override
  void initState() {
    super.initState();
    _initialize();
  }

  Future<void> _initialize() async {
    try {
      // 1. スプラッシュ画像のプリキャッシュ
      _updateStatus('画像を読み込み中...');
      await precacheImage(
        const AssetImage('assets/splash_screen.png'),
        context,
      );

      // 2. Google Fonts (Noto Sans JP) のプリロード
      _updateStatus('フォントを読み込み中...');
      await _preloadFonts();

      // 3. バックエンド接続確認
      _updateStatus('サーバーに接続中...');
      final apiService = ref.read(apiServiceProvider);
      final isConnected = await apiService.healthCheck();
      if (!isConnected) {
        _updateStatus('サーバーに接続できません');
        _hasError = true;
        await Future.delayed(const Duration(seconds: 2));
      }

      // 4. 設定の読み込み完了を待機
      _updateStatus('設定を読み込み中...');
      await _waitForSettingsLoaded();

      // 5. 準備完了
      _updateStatus('準備完了');
      await Future.delayed(const Duration(milliseconds: 300));

      // 6. メイン画面へ遷移
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (context) => const MainScaffold()),
      );
    } catch (e) {
      _updateStatus('エラーが発生しました');
      _hasError = true;
      await Future.delayed(const Duration(seconds: 2));
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (context) => const MainScaffold()),
      );
    }
  }

  Future<void> _preloadFonts() async {
    // Noto Sans JP の各ウェイトを事前読み込み
    await GoogleFonts.pendingFonts([
      GoogleFonts.notoSansJp(fontWeight: FontWeight.w400),
      GoogleFonts.notoSansJp(fontWeight: FontWeight.w500),
      GoogleFonts.notoSansJp(fontWeight: FontWeight.w700),
    ]);
  }

  Future<void> _waitForSettingsLoaded() async {
    // SettingsNotifier の初期化をトリガー（まだ読まれていない場合）
    ref.read(settingsNotifierProvider);

    // 最大5秒待機
    const maxWait = Duration(seconds: 5);
    const checkInterval = Duration(milliseconds: 100);
    var elapsed = Duration.zero;

    while (elapsed < maxWait) {
      final settingsState = ref.read(settingsNotifierProvider);
      if (!settingsState.isLoading) {
        return; // 読み込み完了
      }
      await Future.delayed(checkInterval);
      elapsed += checkInterval;
    }
    // タイムアウトしても続行
  }

  void _updateStatus(String message) {
    if (mounted) {
      setState(() {
        _statusMessage = message;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).colorScheme.surface,
      body: Stack(
        fit: StackFit.expand,
        children: [
          // 背景画像（縦を画面に合わせて表示）
          Center(
            child: Image.asset(
              'assets/splash_screen.png',
              fit: BoxFit.fitHeight,
              height: double.infinity,
            ),
          ),
          // ローディング表示（画面下部）
          Positioned(
            left: 0,
            right: 0,
            bottom: MediaQuery.of(context).padding.bottom + 80,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (_hasError)
                  Icon(
                    Icons.warning_amber_rounded,
                    size: 32,
                    color: Theme.of(context).colorScheme.error,
                  )
                else
                  const CircularProgressIndicator(),
                const SizedBox(height: 16),
                Text(
                  _statusMessage,
                  style: TextStyle(
                    fontSize: 14,
                    color: _hasError
                        ? Theme.of(context).colorScheme.error
                        : Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
