import 'package:flutter/material.dart';
import '../models/alert_model.dart';

class AlertCard extends StatelessWidget {
  final AlertModel alert;
  final Function(bool) onToggle;
  final VoidCallback onDelete;
  final VoidCallback onTestTrigger;

  const AlertCard({
    super.key,
    required this.alert,
    required this.onToggle,
    required this.onDelete,
    required this.onTestTrigger,
  });

  @override
  Widget build(BuildContext context) {
    final conditionTitle = alert.conditionType.replaceAll('_', ' ').toUpperCase();
    String paramDetail = '';
    if (alert.params.containsKey('target_price')) {
      paramDetail = 'Target: ${alert.params['target_price']}';
    } else if (alert.params.containsKey('threshold')) {
      paramDetail = 'Threshold: ${alert.params['threshold']}';
    } else if (alert.conditionType == 'price_cross_indicator') {
      paramDetail = 'Ind: ${(alert.params['indicator'] as Map?)?['type']?.toString().toUpperCase()} (${(alert.params['indicator'] as Map?)?['period']})';
    } else {
      paramDetail = 'Rule: ${alert.params}';
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF131D31),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: alert.isActive ? const Color(0xFF334155) : const Color(0xFF1E293B),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.25),
            blurRadius: 8,
            offset: const Offset(0, 4),
          )
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: const Color(0xFF0EA5E9).withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: const Color(0xFF0EA5E9).withValues(alpha: 0.4)),
                ),
                child: Text(
                  alert.symbol,
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                    color: Color(0xFF38BDF8),
                  ),
                ),
              ),
              const SizedBox(width: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.06),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  alert.timeframe,
                  style: TextStyle(
                    fontSize: 11,
                    color: Colors.blueGrey.shade300,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              const Spacer(),
              Switch(
                value: alert.isActive,
                activeThumbColor: const Color(0xFF34D399),
                activeTrackColor: const Color(0xFF10B981).withValues(alpha: 0.4),
                inactiveThumbColor: Colors.blueGrey.shade600,
                inactiveTrackColor: const Color(0xFF1E293B),
                onChanged: onToggle,
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            conditionTitle,
            style: const TextStyle(
              fontWeight: FontWeight.w700,
              fontSize: 13,
              color: Colors.amberAccent,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            paramDetail,
            style: TextStyle(
              fontSize: 12,
              fontFamily: 'monospace',
              color: Colors.blueGrey.shade200,
            ),
          ),
          if (alert.message != null && alert.message!.isNotEmpty) ...[
            const SizedBox(height: 6),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: const Color(0xFF0F172A),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.indigo.withValues(alpha: 0.3)),
              ),
              child: Text(
                'Note: ${alert.message}',
                style: const TextStyle(
                  fontSize: 11,
                  color: Color(0xFFA5B4FC),
                ),
              ),
            ),
          ],
          const SizedBox(height: 12),
          const Divider(height: 1, color: Color(0xFF1E293B)),
          const SizedBox(height: 8),
          Row(
            children: [
              Text(
                'Fired: ${alert.triggerCount}x',
                style: TextStyle(
                  fontSize: 11,
                  color: Colors.blueGrey.shade400,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const Spacer(),
              TextButton.icon(
                onPressed: onTestTrigger,
                icon: const Icon(Icons.bolt, size: 14, color: Color(0xFF38BDF8)),
                label: const Text('Test', style: TextStyle(fontSize: 11, color: Color(0xFF38BDF8))),
                style: TextButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  minimumSize: Size.zero,
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
              ),
              const SizedBox(width: 8),
              IconButton(
                onPressed: onDelete,
                icon: const Icon(Icons.delete_outline, size: 16, color: Color(0xFFF43F5E)),
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
                tooltip: 'Delete Alert',
              ),
            ],
          ),
        ],
      ),
    );
  }
}
