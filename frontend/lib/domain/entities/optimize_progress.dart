/// 最適化の進捗フェーズ
enum OptimizePhase {
  phase1('phase1', '栄養素フィルタリング中...'),
  phase2('phase2', '料理フィルタを適用中...'),
  phase3('phase3', '最適化モデルを構築中...'),
  phase4('phase4', '制約条件を適用中...'),
  phase5('phase5', '計算中...'),
  phase6('phase6', '結果を整理中...');

  const OptimizePhase(this.value, this.message);

  final String value;
  final String message;

  /// 値からEnumを取得
  static OptimizePhase fromValue(String value) {
    return OptimizePhase.values.firstWhere(
      (e) => e.value == value,
      orElse: () => OptimizePhase.phase1,
    );
  }

  /// 進捗率を取得（0-100）
  int get progressPercent {
    switch (this) {
      case OptimizePhase.phase1:
        return 10;
      case OptimizePhase.phase2:
        return 20;
      case OptimizePhase.phase3:
        return 35;
      case OptimizePhase.phase4:
        return 50;
      case OptimizePhase.phase5:
        return 70;
      case OptimizePhase.phase6:
        return 95;
    }
  }

  /// フェーズ番号を取得（1-6）
  int get phaseNumber {
    return int.parse(value.replaceAll('phase', ''));
  }
}

/// 最適化の進捗状態
class OptimizeProgress {
  final OptimizePhase phase;
  final String message;
  final int progress;
  final double? elapsedSeconds;

  const OptimizeProgress({
    required this.phase,
    required this.message,
    required this.progress,
    this.elapsedSeconds,
  });

  factory OptimizeProgress.fromJson(Map<String, dynamic> json) {
    return OptimizeProgress(
      phase: OptimizePhase.fromValue(json['phase'] as String),
      message: json['message'] as String,
      progress: json['progress'] as int,
      elapsedSeconds: json['elapsed_seconds'] != null
          ? (json['elapsed_seconds'] as num).toDouble()
          : null,
    );
  }

  /// 初期状態
  static const initial = OptimizeProgress(
    phase: OptimizePhase.phase1,
    message: '準備中...',
    progress: 0,
  );

  /// 完了状態
  static const completed = OptimizeProgress(
    phase: OptimizePhase.phase6,
    message: '完了しました',
    progress: 100,
  );

  /// 指定されたフェーズが完了しているか
  bool isPhaseCompleted(OptimizePhase targetPhase) {
    return phase.phaseNumber > targetPhase.phaseNumber || progress >= 100;
  }

  /// 現在のフェーズか
  bool isCurrentPhase(OptimizePhase targetPhase) {
    return phase == targetPhase && progress < 100;
  }
}
