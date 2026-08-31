class SymbolRate {
  final String symbol;
  final String name;
  final String type;
  final double currentPrice;
  final int decimals;

  SymbolRate({
    required this.symbol,
    required this.name,
    required this.type,
    required this.currentPrice,
    required this.decimals,
  });

  factory SymbolRate.fromJson(Map<String, dynamic> json) {
    return SymbolRate(
      symbol: json['symbol'] ?? '',
      name: json['name'] ?? '',
      type: json['type'] ?? 'forex',
      currentPrice: (json['current_price'] as num?)?.toDouble() ?? 0.0,
      decimals: json['decimals'] ?? 4,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'symbol': symbol,
      'name': name,
      'type': type,
      'current_price': currentPrice,
      'decimals': decimals,
    };
  }
}
