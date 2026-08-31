import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/trigger_log_model.dart';

class LogCard extends StatelessWidget {
  final TriggerLogModel log;

  const LogCard({super.key, required this.log});

  @override
  Widget build(BuildContext context) {
    final formattedTime = DateFormat('HH:mm:ss • MMM dd').format(log.timestamp.toLocal());

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF131D31),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF1E293B)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: const Color(0xFFF43F5E).withValues(alpha: 0.15),
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
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        log.timeframe,
                        style: TextStyle(
                          fontSize: 10,
                          color: Colors.blueGrey.shade300,
                        ),
                      ),
                    ),
                    const Spacer(),
                    Text(
                      formattedTime,
                      style: TextStyle(
                        fontSize: 10,
                        color: Colors.blueGrey.shade500,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  log.conditionSummary,
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.blueGrey.shade200,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Trigger Price: ${log.triggerPrice}',
                  style: const TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFF38BDF8),
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
