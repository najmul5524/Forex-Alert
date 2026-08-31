import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/trigger_log_model.dart';

class LogCard extends StatelessWidget {
  final TriggerLogModel log;

  const LogCard({super.key, required this.log});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final formattedTime = DateFormat('HH:mm:ss • MMM dd').format(log.timestamp.toLocal());

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Theme.of(context).dividerColor),
        boxShadow: [
          BoxShadow(
            color: isDark ? Colors.black.withValues(alpha: 0.2) : Colors.black.withValues(alpha: 0.04),
            blurRadius: 4,
            offset: const Offset(0, 2),
          )
        ],
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: const Color(0xFFF43F5E).withValues(alpha: isDark ? 0.15 : 0.1),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: const Color(0xFFF43F5E).withValues(alpha: 0.3)),
            ),
            child: const Text('🚨', style: TextStyle(fontSize: 16)),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      log.symbol,
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                        color: Theme.of(context).colorScheme.onSurface,
                      ),
                    ),
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                      decoration: BoxDecoration(
                        color: isDark ? Colors.white.withValues(alpha: 0.08) : Colors.black.withValues(alpha: 0.05),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        log.timeframe,
                        style: TextStyle(
                          fontSize: 10,
                          color: isDark ? Colors.blueGrey.shade300 : Colors.blueGrey.shade700,
                        ),
                      ),
                    ),
                    const Spacer(),
                    Text(
                      formattedTime,
                      style: TextStyle(
                        fontSize: 10,
                        color: isDark ? Colors.blueGrey.shade500 : Colors.blueGrey.shade500,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  log.conditionSummary,
                  style: TextStyle(
                    fontSize: 12,
                    color: isDark ? Colors.blueGrey.shade200 : Colors.blueGrey.shade700,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Trigger Price: ${log.triggerPrice}',
                  style: TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: Theme.of(context).colorScheme.primary,
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
