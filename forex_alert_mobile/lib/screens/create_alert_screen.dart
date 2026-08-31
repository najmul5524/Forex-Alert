import 'package:flutter/material.dart';
import '../models/alert_model.dart';
import '../services/api_service.dart';
import '../services/firestore_service.dart';

class CreateAlertScreen extends StatefulWidget {
  final String? initialSymbol;
  final double? initialPrice;

  const CreateAlertScreen({super.key, this.initialSymbol, this.initialPrice});

  @override
  State<CreateAlertScreen> createState() => _CreateAlertScreenState();
}

class _CreateAlertScreenState extends State<CreateAlertScreen> {
  final _formKey = GlobalKey<FormState>();

  final List<String> _symbols = [
    'EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'AUDUSD', 'USDCAD', 'BTCUSDT', 'ETHUSDT', 'SOLUSDT'
  ];

  final List<String> _timeframes = ['1m', '5m', '15m', '1h', '4h', '1d'];

  final Map<String, String> _conditions = {
    'price_cross_up': 'Crossing Above (Price > Level)',
    'price_cross_down': 'Crossing Below (Price < Level)',
    'price_greater': 'Greater Than (Price >= Level)',
    'price_less': 'Less Than (Price <= Level)',
    'price_cross_indicator': 'Price Crosses Indicator (e.g. 50 EMA)',
    'indicator_cross_indicator': 'Indicator Crosses Indicator (e.g. Fast/Slow EMA)',
    'indicator_cross_value': 'Indicator Threshold (e.g. RSI 70 / 30)',
    'channel_exit': 'Exiting Price Channel',
  };

  late String _selectedSymbol;
  String _selectedTimeframe = '1m';
  String _selectedCondition = 'price_cross_up';
  String _triggerFrequency = 'only_once';

  final TextEditingController _targetPriceController = TextEditingController();
  final TextEditingController _indicatorPeriodController = TextEditingController(text: '14');
  final TextEditingController _rsiThresholdController = TextEditingController(text: '70');
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _messageController = TextEditingController();

  final String _indicatorType = 'ema';
  String _indicatorDirection = 'above';
  bool _sendPush = true;
  bool _sendEmail = false;
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _selectedSymbol = widget.initialSymbol ?? 'EURUSD';
    if (widget.initialPrice != null) {
      _targetPriceController.text = widget.initialPrice!.toString();
    } else {
      _targetPriceController.text = '1.08500';
    }
  }

  @override
  void dispose() {
    _targetPriceController.dispose();
    _indicatorPeriodController.dispose();
    _rsiThresholdController.dispose();
    _emailController.dispose();
    _messageController.dispose();
    super.dispose();
  }

  Future<void> _submitAlert() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isSaving = true);

    final Map<String, dynamic> params = {};
    if (['price_cross_up', 'price_cross_down', 'price_greater', 'price_less'].contains(_selectedCondition)) {
      params['target_price'] = double.tryParse(_targetPriceController.text) ?? 1.0850;
    } else if (_selectedCondition == 'price_cross_indicator') {
      params['direction'] = _indicatorDirection;
      params['indicator'] = {
        'type': _indicatorType,
        'period': int.tryParse(_indicatorPeriodController.text) ?? 20,
      };
    } else if (_selectedCondition == 'indicator_cross_value') {
      params['direction'] = _indicatorDirection;
      params['threshold'] = double.tryParse(_rsiThresholdController.text) ?? 70.0;
      params['indicator'] = {
        'type': 'rsi',
        'period': int.tryParse(_indicatorPeriodController.text) ?? 14,
      };
    }

    final channels = <String>['in_app'];
    if (_sendPush) channels.add('push');
    if (_sendEmail && _emailController.text.isNotEmpty) channels.add('email');

    final newAlert = AlertModel(
      symbol: _selectedSymbol,
      timeframe: _selectedTimeframe,
      conditionType: _selectedCondition,
      params: params,
      triggerFrequency: _triggerFrequency,
      channels: channels,
      targetEmail: _emailController.text.isNotEmpty ? _emailController.text.trim() : null,
      message: _messageController.text.isNotEmpty ? _messageController.text.trim() : null,
      isActive: true,
    );

    final created = await ApiService.createAlert(newAlert);
    if (created != null) {
      await FirestoreService.saveAlert(created);
    } else {
      await FirestoreService.saveAlert(newAlert);
    }

    if (mounted) {
      setState(() => _isSaving = false);
      Navigator.of(context).pop(true);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Alert created for $_selectedSymbol!'),
          backgroundColor: const Color(0xFF10B981),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFF0F172A),
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
        left: 20,
        right: 20,
        top: 20,
      ),
      child: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: Colors.blueGrey.shade700,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  const Text('⚡', style: TextStyle(fontSize: 20)),
                  const SizedBox(width: 8),
                  const Text(
                    'Create Market Alert',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(Icons.close, color: Colors.blueGrey),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              Row(
                children: [
                  Expanded(
                    flex: 3,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Instrument', style: TextStyle(fontSize: 12, color: Colors.blueGrey)),
                        const SizedBox(height: 6),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12),
                          decoration: BoxDecoration(
                            color: const Color(0xFF131D31),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: const Color(0xFF334155)),
                          ),
                          child: DropdownButtonHideUnderline(
                            child: DropdownButton<String>(
                              value: _selectedSymbol,
                              isExpanded: true,
                              dropdownColor: const Color(0xFF131D31),
                              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                              items: _symbols.map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
                              onChanged: (v) => setState(() => _selectedSymbol = v!),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Timeframe', style: TextStyle(fontSize: 12, color: Colors.blueGrey)),
                        const SizedBox(height: 6),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12),
                          decoration: BoxDecoration(
                            color: const Color(0xFF131D31),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: const Color(0xFF334155)),
                          ),
                          child: DropdownButtonHideUnderline(
                            child: DropdownButton<String>(
                              value: _selectedTimeframe,
                              isExpanded: true,
                              dropdownColor: const Color(0xFF131D31),
                              style: const TextStyle(color: Color(0xFF38BDF8), fontWeight: FontWeight.bold),
                              items: _timeframes.map((tf) => DropdownMenuItem(value: tf, child: Text(tf))).toList(),
                              onChanged: (v) => setState(() => _selectedTimeframe = v!),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              const Text('Trigger Condition', style: TextStyle(fontSize: 12, color: Colors.blueGrey)),
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(
                  color: const Color(0xFF131D31),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF334155)),
                ),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    value: _selectedCondition,
                    isExpanded: true,
                    dropdownColor: const Color(0xFF131D31),
                    style: const TextStyle(color: Colors.amberAccent, fontWeight: FontWeight.w600, fontSize: 13),
                    items: _conditions.entries
                        .map((e) => DropdownMenuItem(value: e.key, child: Text(e.value, overflow: TextOverflow.ellipsis)))
                        .toList(),
                    onChanged: (v) => setState(() => _selectedCondition = v!),
                  ),
                ),
              ),
              const SizedBox(height: 16),

              if (['price_cross_up', 'price_cross_down', 'price_greater', 'price_less'].contains(_selectedCondition)) ...[
                const Text('Target Level Price', style: TextStyle(fontSize: 12, color: Colors.blueGrey)),
                const SizedBox(height: 6),
                TextFormField(
                  controller: _targetPriceController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  style: const TextStyle(color: Colors.white, fontFamily: 'monospace', fontWeight: FontWeight.bold),
                  decoration: InputDecoration(
                    hintText: '1.08550',
                    hintStyle: TextStyle(color: Colors.blueGrey.shade600),
                    filled: true,
                    fillColor: const Color(0xFF131D31),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF334155))),
                    enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF334155))),
                    focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF38BDF8))),
                  ),
                  validator: (v) => (v == null || v.isEmpty) ? 'Please enter a target price' : null,
                ),
              ],

              if (_selectedCondition == 'price_cross_indicator' || _selectedCondition == 'indicator_cross_value') ...[
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Direction', style: TextStyle(fontSize: 12, color: Colors.blueGrey)),
                          const SizedBox(height: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12),
                            decoration: BoxDecoration(
                              color: const Color(0xFF131D31),
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: const Color(0xFF334155)),
                            ),
                            child: DropdownButtonHideUnderline(
                              child: DropdownButton<String>(
                                value: _indicatorDirection,
                                isExpanded: true,
                                dropdownColor: const Color(0xFF131D31),
                                style: const TextStyle(color: Colors.white),
                                items: const [
                                  DropdownMenuItem(value: 'above', child: Text('Crosses Above')),
                                  DropdownMenuItem(value: 'below', child: Text('Crosses Below')),
                                ],
                                onChanged: (v) => setState(() => _indicatorDirection = v!),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Period', style: TextStyle(fontSize: 12, color: Colors.blueGrey)),
                          const SizedBox(height: 6),
                          TextFormField(
                            controller: _indicatorPeriodController,
                            keyboardType: TextInputType.number,
                            style: const TextStyle(color: Colors.white, fontFamily: 'monospace'),
                            decoration: InputDecoration(
                              filled: true,
                              fillColor: const Color(0xFF131D31),
                              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF334155))),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ],

              if (_selectedCondition == 'indicator_cross_value') ...[
                const SizedBox(height: 12),
                const Text('Threshold (e.g. 70 for Overbought, 30 for Oversold)', style: TextStyle(fontSize: 12, color: Colors.blueGrey)),
                const SizedBox(height: 6),
                TextFormField(
                  controller: _rsiThresholdController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  style: const TextStyle(color: Colors.white, fontFamily: 'monospace'),
                  decoration: InputDecoration(
                    filled: true,
                    fillColor: const Color(0xFF131D31),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF334155))),
                  ),
                ),
              ],

              const SizedBox(height: 16),

              const Text('Trigger Frequency', style: TextStyle(fontSize: 12, color: Colors.blueGrey)),
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(
                  color: const Color(0xFF131D31),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF334155)),
                ),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    value: _triggerFrequency,
                    isExpanded: true,
                    dropdownColor: const Color(0xFF131D31),
                    style: const TextStyle(color: Colors.white),
                    items: const [
                      DropdownMenuItem(value: 'only_once', child: Text('Only Once (Auto-deactivate)')),
                      DropdownMenuItem(value: 'once_per_bar', child: Text('Once Per Bar')),
                      DropdownMenuItem(value: 'once_per_bar_close', child: Text('Once Per Bar Close')),
                      DropdownMenuItem(value: 'every_time', child: Text('Every Time (with 5m cooldown)')),
                    ],
                    onChanged: (v) => setState(() => _triggerFrequency = v!),
                  ),
                ),
              ),
              const SizedBox(height: 16),

              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFF131D31),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF334155)),
                ),
                child: Column(
                  children: [
                    CheckboxListTile(
                      value: _sendPush,
                      title: const Text('📱 Smartphone Push Alert', style: TextStyle(color: Colors.white, fontSize: 13)),
                      activeColor: const Color(0xFF38BDF8),
                      contentPadding: EdgeInsets.zero,
                      dense: true,
                      onChanged: (v) => setState(() => _sendPush = v ?? true),
                    ),
                    CheckboxListTile(
                      value: _sendEmail,
                      title: const Text('✉️ Email Notification', style: TextStyle(color: Colors.white, fontSize: 13)),
                      activeColor: const Color(0xFF38BDF8),
                      contentPadding: EdgeInsets.zero,
                      dense: true,
                      onChanged: (v) => setState(() => _sendEmail = v ?? false),
                    ),
                  ],
                ),
              ),

              if (_sendEmail) ...[
                const SizedBox(height: 12),
                TextFormField(
                  controller: _emailController,
                  keyboardType: TextInputType.emailAddress,
                  style: const TextStyle(color: Colors.white),
                  decoration: InputDecoration(
                    hintText: 'your_email@gmail.com',
                    hintStyle: TextStyle(color: Colors.blueGrey.shade600),
                    labelText: 'Recipient Email',
                    labelStyle: const TextStyle(color: Colors.blueGrey),
                    filled: true,
                    fillColor: const Color(0xFF131D31),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
              ],

              const SizedBox(height: 12),
              TextFormField(
                controller: _messageController,
                style: const TextStyle(color: Colors.white),
                decoration: InputDecoration(
                  hintText: 'e.g. Look for 5m reversal entry!',
                  hintStyle: TextStyle(color: Colors.blueGrey.shade600),
                  labelText: 'Custom Note / Message',
                  labelStyle: const TextStyle(color: Colors.blueGrey),
                  filled: true,
                  fillColor: const Color(0xFF131D31),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),

              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton(
                  onPressed: _isSaving ? null : _submitAlert,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF0EA5E9),
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  ),
                  child: _isSaving
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text('⚡ Activate Alert', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
