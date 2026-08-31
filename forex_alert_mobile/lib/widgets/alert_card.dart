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
    final isDark = Theme.of(context).brightness == Brightness.dark;
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
        color: Theme.of(context).colorScheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: alert.isActive
              ? (isDark ? const Color(0xFF334155) : const Color(0xFFCBD5E1))
              : Theme.of(context).dividerColor,
        ),
        boxShadow: [
          BoxShadow(
            color: isDark ? Colors.black.withValues(alpha: 0.25) : Colors.black.withValues(alpha: 0.04),
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
                  color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.3)),
                ),
                child: Text(
                  alert.symbol,
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                ),
              ),
              const SizedBox(width: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                decoration: BoxDecoration(
                  color: isDark ? Colors.white.withValues(alpha: 0.06) : Colors.black.withValues(alpha: 0.04),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  alert.timeframe,
                  style: TextStyle(
                    fontSize: 11,
                    color: isDark ? Colors.blueGrey.shade300 : Colors.blueGrey.shade700,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              const Spacer(),
              Switch(
                value: alert.isActive,
                activeThumbColor: const Color(0xFF10B981),
                activeTrackColor: const Color(0xFF10B981).withValues(alpha: 0.3),
                inactiveThumbColor: Colors.blueGrey.shade400,
                inactiveTrackColor: isDark ? const Color(0xFF1E293B) : const Color(0xFFE2E8F0),
                onChanged: onToggle,
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            conditionTitle,
            style: TextStyle(
              fontWeight: FontWeight.w700,
              fontSize: 13,
              color: isDark ? Colors.amberAccent : Colors.orange.shade800,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            paramDetail,
            style: TextStyle(
              fontSize: 12,
              fontFamily: 'monospace',
              color: isDark ? Colors.blueGrey.shade200 : Colors.blueGrey.shade800,
            ),
          ),
          if (alert.message != null && alert.message!.isNotEmpty) ...[
            const SizedBox(height: 6),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: isDark ? const Color(0xFF0F172A) : const Color(0xFFF1F5F9),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.indigo.withValues(alpha: 0.2)),
              ),
              child: Text(
                'Note: ${alert.message}',
                style: TextStyle(
                  fontSize: 11,
                  color: isDark ? const Color(0xFFA5B4FC) : const Color(0xFF4338CA),
                ),
              ),
            ),
          ],
          const SizedBox(height: 12),
          Divider(height: 1, color: Theme.of(context).dividerColor),
          const SizedBox(height: 8),
          Row(
            children: [
              Text(
                'Fired: ${alert.triggerCount}x',
                style: TextStyle(
                  fontSize: 11,
                  color: isDark ? Colors.blueGrey.shade400 : Colors.blueGrey.shade600,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const Spacer(),
              TextButton.icon(
                onPressed: onTestTrigger,
                icon: Icon(Icons.bolt, size: 14, color: Theme.of(context).colorScheme.primary),
                label: Text('Test', style: TextStyle(fontSize: 11, color: Theme.of(context).colorScheme.primary)),
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
