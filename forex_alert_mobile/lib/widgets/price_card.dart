import 'package:flutter/material.dart';
import '../models/symbol_rate.dart';

class PriceCard extends StatelessWidget {
  final SymbolRate rate;
  final VoidCallback? onTap;

  const PriceCard({super.key, required this.rate, this.onTap});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final isForex = rate.type.toLowerCase() == 'forex';
    final isCrypto = rate.type.toLowerCase() == 'crypto';
    final badgeColor = isCrypto ? Colors.amber.shade700 : isForex ? const Color(0xFF0EA5E9) : Colors.indigo.shade600;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Theme.of(context).dividerColor),
          boxShadow: [
            BoxShadow(
              color: isDark ? Colors.black.withValues(alpha: 0.2) : Colors.black.withValues(alpha: 0.04),
              blurRadius: 6,
              offset: const Offset(0, 3),
            )
          ],
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: badgeColor.withValues(alpha: isDark ? 0.15 : 0.12),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: badgeColor.withValues(alpha: isDark ? 0.4 : 0.3)),
              ),
              child: Text(
                isCrypto ? '🪙' : isForex ? '💱' : '⚡',
                style: const TextStyle(fontSize: 18),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    rate.symbol,
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                      color: Theme.of(context).colorScheme.onSurface,
                      letterSpacing: 0.5,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    rate.name,
                    style: TextStyle(
                      fontSize: 11,
                      color: isDark ? Colors.blueGrey.shade400 : Colors.blueGrey.shade600,
                    ),
                  ),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  rate.currentPrice.toStringAsFixed(rate.decimals),
                  style: TextStyle(
                    fontFamily: 'monospace',
                    fontWeight: FontWeight.w800,
                    fontSize: 16,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                ),
                const SizedBox(height: 2),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: const Color(0xFF10B981).withValues(alpha: isDark ? 0.15 : 0.12),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: const Text(
                    '● LIVE',
                    style: TextStyle(
                      color: Color(0xFF10B981),
                      fontSize: 9,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
