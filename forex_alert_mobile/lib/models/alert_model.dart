class AlertModel {
  final int? id;
  final String symbol;
  final String timeframe;
  final String conditionType;
  final Map<String, dynamic> params;
  final String triggerFrequency;
  final List<String> channels;
  final String? targetEmail;
  final String? webhookUrl;
  final String? message;
  final bool isActive;
  final int triggerCount;
  final DateTime? createdAt;

  AlertModel({
    this.id,
    required this.symbol,
    this.timeframe = '1m',
    required this.conditionType,
    required this.params,
    this.triggerFrequency = 'only_once',
    this.channels = const ['push', 'in_app'],
    this.targetEmail,
    this.webhookUrl,
    this.message,
    this.isActive = true,
    this.triggerCount = 0,
    this.createdAt,
  });

  factory AlertModel.fromJson(Map<String, dynamic> json) {
    return AlertModel(
      id: json['id'],
      symbol: json['symbol'] ?? '',
      timeframe: json['timeframe'] ?? '1m',
      conditionType: json['condition_type'] ?? '',
      params: json['params'] is Map<String, dynamic> ? json['params'] : {},
      triggerFrequency: json['trigger_frequency'] ?? 'only_once',
      channels: (json['channels'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? ['push', 'in_app'],
      targetEmail: json['target_email'],
      webhookUrl: json['webhook_url'],
      message: json['message'],
      isActive: json['is_active'] ?? true,
      triggerCount: json['trigger_count'] ?? 0,
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at'].toString()) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      if (id != null) 'id': id,
      'symbol': symbol,
      'timeframe': timeframe,
      'condition_type': conditionType,
      'params': params,
      'trigger_frequency': triggerFrequency,
      'channels': channels,
      'target_email': targetEmail,
      'webhook_url': webhookUrl,
      'message': message,
      'is_active': isActive,
      'trigger_count': triggerCount,
    };
  }

  AlertModel copyWith({
    int? id,
    String? symbol,
    String? timeframe,
    String? conditionType,
    Map<String, dynamic>? params,
    String? triggerFrequency,
    List<String>? channels,
    String? targetEmail,
    String? webhookUrl,
    String? message,
    bool? isActive,
    int? triggerCount,
    DateTime? createdAt,
  }) {
    return AlertModel(
      id: id ?? this.id,
      symbol: symbol ?? this.symbol,
      timeframe: timeframe ?? this.timeframe,
      conditionType: conditionType ?? this.conditionType,
      params: params ?? this.params,
      triggerFrequency: triggerFrequency ?? this.triggerFrequency,
      channels: channels ?? this.channels,
      targetEmail: targetEmail ?? this.targetEmail,
      webhookUrl: webhookUrl ?? this.webhookUrl,
      message: message ?? this.message,
      isActive: isActive ?? this.isActive,
      triggerCount: triggerCount ?? this.triggerCount,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}
