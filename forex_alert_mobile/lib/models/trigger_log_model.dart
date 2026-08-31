class TriggerLogModel {
  final int id;
  final int? alertId;
  final String symbol;
  final String conditionSummary;
  final double triggerPrice;
  final String timeframe;
  final List<String> channelsSent;
  final DateTime timestamp;

  TriggerLogModel({
    required this.id,
    this.alertId,
    required this.symbol,
    required this.conditionSummary,
    required this.triggerPrice,
    required this.timeframe,
    required this.channelsSent,
    required this.timestamp,
  });

  factory TriggerLogModel.fromJson(Map<String, dynamic> json) {
    return TriggerLogModel(
      id: json['id'] ?? 0,
      alertId: json['alert_id'],
      symbol: json['symbol'] ?? '',
      conditionSummary: json['condition_summary'] ?? '',
      triggerPrice: (json['trigger_price'] as num?)?.toDouble() ?? 0.0,
      timeframe: json['timeframe'] ?? '1m',
      channelsSent: (json['channels_sent'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      timestamp: json['timestamp'] != null 
          ? DateTime.tryParse(json['timestamp'].toString()) ?? DateTime.now() 
          : DateTime.now(),
    );
  }
}
