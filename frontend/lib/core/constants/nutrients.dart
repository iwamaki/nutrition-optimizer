import 'package:flutter/material.dart';

/// 栄養素定義
///
/// 日本人の食事摂取基準（2020年版）厚生労働省 準拠
/// https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/kenkou/eiyou/syokuji_kijyun.html
class NutrientDefinition {
  final String key;             // APIキー名（例: 'calories', 'vitamin_b1'）
  final String label;           // 表示名（例: 'カロリー', 'ビタミンB1'）
  final Color color;            // グラフ表示色
  final double? upperLimitRatio; // 耐容上限量（推奨量に対する倍率）、nullは上限なし
  final bool isUpperTarget;     // true: 上限方向が目標（ナトリウム等）

  const NutrientDefinition({
    required this.key,
    required this.label,
    required this.color,
    this.upperLimitRatio,
    this.isUpperTarget = false,
  });

  /// 上限の達成率を計算（%）
  /// 例: 推奨量の上限が3倍なら、実績100%で上限の33%、実績300%で上限の100%
  double? getUpperLimitPercent(double achievementPercent) {
    if (upperLimitRatio == null) return null;
    return achievementPercent / (upperLimitRatio! * 100) * 100;
  }
}

/// エネルギー・三大栄養素
/// 耐容上限量は厚生労働省「日本人の食事摂取基準（2020年版）」より
const basicNutrients = [
  NutrientDefinition(key: 'calories', label: 'カロリー', color: Colors.orange, upperLimitRatio: 1.3),
  NutrientDefinition(key: 'protein', label: 'タンパク質', color: Colors.red),
  NutrientDefinition(key: 'fat', label: '脂質', color: Colors.amber),
  NutrientDefinition(key: 'carbohydrate', label: '炭水化物', color: Colors.blue),
  NutrientDefinition(key: 'fiber', label: '食物繊維', color: Colors.green),
];

/// ミネラル
/// ナトリウム: 目標量を100%とし、他の栄養素と同じ表示（130%超で警告）
final mineralNutrients = [
  const NutrientDefinition(key: 'sodium', label: 'ナトリウム', color: Colors.grey, upperLimitRatio: 1.3),
  NutrientDefinition(key: 'potassium', label: 'カリウム', color: Colors.purple.shade300),
  const NutrientDefinition(key: 'calcium', label: 'カルシウム', color: Colors.blueGrey, upperLimitRatio: 3.3),
  const NutrientDefinition(key: 'magnesium', label: 'マグネシウム', color: Colors.cyan),
  const NutrientDefinition(key: 'iron', label: '鉄', color: Colors.brown, upperLimitRatio: 6.7),
  NutrientDefinition(key: 'zinc', label: '亜鉛', color: Colors.indigo.shade300, upperLimitRatio: 4.1),
];

/// ビタミン
final vitaminNutrients = [
  const NutrientDefinition(key: 'vitamin_a', label: 'ビタミンA', color: Colors.deepOrange, upperLimitRatio: 3.0),
  const NutrientDefinition(key: 'vitamin_d', label: 'ビタミンD', color: Colors.teal, upperLimitRatio: 12.0),
  NutrientDefinition(key: 'vitamin_e', label: 'ビタミンE', color: Colors.lime.shade700, upperLimitRatio: 150.0),
  NutrientDefinition(key: 'vitamin_k', label: 'ビタミンK', color: Colors.green.shade700),
  NutrientDefinition(key: 'vitamin_b1', label: 'ビタミンB1', color: Colors.pink.shade300),
  NutrientDefinition(key: 'vitamin_b2', label: 'ビタミンB2', color: Colors.pink.shade500),
  NutrientDefinition(key: 'vitamin_b6', label: 'ビタミンB6', color: Colors.pink.shade700, upperLimitRatio: 43.0),
  NutrientDefinition(key: 'vitamin_b12', label: 'ビタミンB12', color: Colors.red.shade700),
  NutrientDefinition(key: 'niacin', label: 'ナイアシン', color: Colors.pink.shade200, upperLimitRatio: 23.0),
  NutrientDefinition(key: 'pantothenic_acid', label: 'パントテン酸', color: Colors.pink.shade100),
  NutrientDefinition(key: 'biotin', label: 'ビオチン', color: Colors.purple.shade200),
  const NutrientDefinition(key: 'folate', label: '葉酸', color: Colors.lightGreen, upperLimitRatio: 4.2),
  NutrientDefinition(key: 'vitamin_c', label: 'ビタミンC', color: Colors.yellow.shade700),
];

/// 全栄養素（グループごとにフラット化）
final allNutrients = [
  ...basicNutrients,
  ...mineralNutrients,
  ...vitaminNutrients,
];

/// コア栄養素（常に計算、8種類）
/// 最適化ロジックで必ず考慮される基本栄養素
const coreNutrientKeys = [
  'calories',
  'protein',
  'fat',
  'carbohydrate',
  'fiber',
  'iron',
  'calcium',
  'vitamin_d',
];

/// オプション栄養素（ユーザー選択可能、16種類）
/// パフォーマンス向上のため、必要に応じて無効化可能
const optionalNutrientKeys = [
  // ミネラル
  'sodium',
  'potassium',
  'magnesium',
  'zinc',
  // ビタミン
  'vitamin_a',
  'vitamin_e',
  'vitamin_k',
  'vitamin_b1',
  'vitamin_b2',
  'vitamin_b6',
  'vitamin_b12',
  'niacin',
  'pantothenic_acid',
  'biotin',
  'folate',
  'vitamin_c',
];

/// コア栄養素の定義を取得
List<NutrientDefinition> get coreNutrients =>
    allNutrients.where((n) => coreNutrientKeys.contains(n.key)).toList();

/// オプション栄養素の定義を取得
List<NutrientDefinition> get optionalNutrients =>
    allNutrients.where((n) => optionalNutrientKeys.contains(n.key)).toList();

/// 有効な栄養素キーを取得
List<String> getEnabledNutrientKeys(Set<String>? enabledOptional) {
  // コア栄養素は常に有効
  final enabled = List<String>.from(coreNutrientKeys);

  // enabledOptionalがnullの場合は全て有効
  if (enabledOptional == null) {
    enabled.addAll(optionalNutrientKeys);
  } else {
    // 指定されたオプション栄養素のみ追加
    for (final key in enabledOptional) {
      if (optionalNutrientKeys.contains(key) && !enabled.contains(key)) {
        enabled.add(key);
      }
    }
  }

  return enabled;
}

/// 栄養データの出典
const nutrientDataSource = '日本食品標準成分表（八訂）増補2023年';

/// 栄養摂取基準の出典
const nutrientStandardSource = '日本人の食事摂取基準（2020年版）厚生労働省';
