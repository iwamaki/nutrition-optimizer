import 'package:flutter/material.dart';

/// 栄養素定義
///
/// 日本人の食事摂取基準（2020年版）厚生労働省 準拠
/// https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/kenkou/eiyou/syokuji_kijyun.html
class NutrientDefinition {
  final String key;       // APIキー名（例: 'calories', 'vitamin_b1'）
  final String label;     // 表示名（例: 'カロリー', 'ビタミンB1'）
  final Color color;      // グラフ表示色

  const NutrientDefinition({
    required this.key,
    required this.label,
    required this.color,
  });
}

/// エネルギー・三大栄養素
const basicNutrients = [
  NutrientDefinition(key: 'calories', label: 'カロリー', color: Colors.orange),
  NutrientDefinition(key: 'protein', label: 'タンパク質', color: Colors.red),
  NutrientDefinition(key: 'fat', label: '脂質', color: Colors.amber),
  NutrientDefinition(key: 'carbohydrate', label: '炭水化物', color: Colors.blue),
  NutrientDefinition(key: 'fiber', label: '食物繊維', color: Colors.green),
];

/// ミネラル
final mineralNutrients = [
  const NutrientDefinition(key: 'sodium', label: 'ナトリウム', color: Colors.grey),
  NutrientDefinition(key: 'potassium', label: 'カリウム', color: Colors.purple.shade300),
  const NutrientDefinition(key: 'calcium', label: 'カルシウム', color: Colors.blueGrey),
  const NutrientDefinition(key: 'magnesium', label: 'マグネシウム', color: Colors.cyan),
  const NutrientDefinition(key: 'iron', label: '鉄', color: Colors.brown),
  NutrientDefinition(key: 'zinc', label: '亜鉛', color: Colors.indigo.shade300),
];

/// ビタミン
final vitaminNutrients = [
  const NutrientDefinition(key: 'vitamin_a', label: 'ビタミンA', color: Colors.deepOrange),
  const NutrientDefinition(key: 'vitamin_d', label: 'ビタミンD', color: Colors.teal),
  NutrientDefinition(key: 'vitamin_e', label: 'ビタミンE', color: Colors.lime.shade700),
  NutrientDefinition(key: 'vitamin_k', label: 'ビタミンK', color: Colors.green.shade700),
  NutrientDefinition(key: 'vitamin_b1', label: 'ビタミンB1', color: Colors.pink.shade300),
  NutrientDefinition(key: 'vitamin_b2', label: 'ビタミンB2', color: Colors.pink.shade500),
  NutrientDefinition(key: 'vitamin_b6', label: 'ビタミンB6', color: Colors.pink.shade700),
  NutrientDefinition(key: 'vitamin_b12', label: 'ビタミンB12', color: Colors.red.shade700),
  NutrientDefinition(key: 'niacin', label: 'ナイアシン', color: Colors.pink.shade200),
  NutrientDefinition(key: 'pantothenic_acid', label: 'パントテン酸', color: Colors.pink.shade100),
  NutrientDefinition(key: 'biotin', label: 'ビオチン', color: Colors.purple.shade200),
  const NutrientDefinition(key: 'folate', label: '葉酸', color: Colors.lightGreen),
  NutrientDefinition(key: 'vitamin_c', label: 'ビタミンC', color: Colors.yellow.shade700),
];

/// 全栄養素（グループごとにフラット化）
final allNutrients = [
  ...basicNutrients,
  ...mineralNutrients,
  ...vitaminNutrients,
];

/// 栄養データの出典
const nutrientDataSource = '日本食品標準成分表（八訂）増補2023年';

/// 栄養摂取基準の出典
const nutrientStandardSource = '日本人の食事摂取基準（2020年版）厚生労働省';
