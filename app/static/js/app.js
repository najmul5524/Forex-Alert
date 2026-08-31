document.addEventListener(DOMContentLoaded, () => {
    const App = {
        symbol: EURUSD,
        timeframe: 1m,
        chart: null,
        symbols: [],
        alerts: [],
        logs: [],
        ws: null,
        vapidPublicKey: window.VAPID_PUBLIC_KEY || ",

 async init() {
 this.chart = new TradingChart(chart-container);
 await this.loadSymbols();
 await this.loadAlerts();
 await this.loadLogs();
 await this.chart.loadSymbolData(this.symbol, this.timeframe);
 this.chart.setAlertLines(this.alerts);

 this.initWebSocket();
 this.setupEventListeners();
 this.setupConditionFormWatcher();
 },

 async loadSymbols() {
 try {
 const resp = await fetch(/api/market/symbols);
 this.symbols = await resp.json();
 this.renderSymbolsSelector();
 } catch (e) {
 console.error(Failed to load symbols:, e);
 }
 },

 renderSymbolsSelector() {
 const container = document.getElementById(symbol-list);
 if (!container) return;

 container.innerHTML = this.symbols.map(s => 
 <button class=symbol-btn px-3 py-2 rounded-lg flex items-center justify-between transition-all  data-symbol=>
 <div class=text-left>
 <div class=font-semibold text-xs tracking-wider></div>
 <div class=text-[10px] opacity-75></div>
 </div>
 <div class=text-right>
 <div class=font-mono text-xs font-bold id=price-card-></div>
 </div>
 </button>
 ).join();

 container.querySelectorAll(.symbol-btn).forEach(btn => {
 btn.addEventListener(click, () => {
 this.changeSymbol(btn.dataset.symbol);
 });
 });

 this.updateHeaderPrice();
 },

 updateHeaderPrice() {
 const currentObj = this.symbols.find(s => s.symbol === this.symbol);
 if (!currentObj) return;

 document.getElementById(current-symbol-title).innerText = currentObj.name + ();
 const priceEl = document.getElementById(current-symbol-price);
 if (priceEl) {
 priceEl.innerText = currentObj.current_price.toFixed(currentObj.decimals);
 }
 },

 async changeSymbol(newSym) {
 if (this.symbol === newSym) return;
 this.symbol = newSym;
 this.renderSymbolsSelector();
 await this.chart.loadSymbolData(this.symbol, this.timeframe);
 this.chart.setAlertLines(this.alerts);
 },

 async changeTimeframe(newTf) {
 if (this.timeframe === newTf) return;
 this.timeframe = newTf;
 document.querySelectorAll(.tf-btn).forEach(b => {
 if (b.dataset.tf === newTf) {
 b.classList.add(bg-sky-600, text-white);
 b.classList.remove(text-slate-400, hover:bg-slate-800);
 } else {
 b.classList.remove(bg-sky-600, text-white);
 b.classList.add(text-slate-400, hover:bg-slate-800);
 }
 });
 await this.chart.loadSymbolData(this.symbol, this.timeframe);
 },

 async loadAlerts() {
 try {
 const resp = await fetch(/api/alerts);
 this.alerts = await resp.json();
 this.renderAlerts();
 if (this.chart) {
 this.chart.setAlertLines(this.alerts);
 }
 } catch (e) {
 console.error(Failed to load alerts:, e);
 }
 },

 renderAlerts() {
 const container = document.getElementById(alerts-list-container);
 const badgeCount = document.getElementById(active-alerts-count);
 if (badgeCount) {
 const activeCount = this.alerts.filter(a => a.is_active).length;
 badgeCount.innerText = activeCount;
 }

 if (!container) return;

 if (this.alerts.length === 0) {
 container.innerHTML = 
 <div class=p-8 text-center text-slate-500>
 <div class=text-3xl mb-2>🔔</div>
 <div class=font-medium text-sm>No alerts configured yet</div>
 <div class=text-xs mt-1>Click Create Alert to set price or indicator triggers.</div>
 </div>
 ;
 return;
 }

 container.innerHTML = this.alerts.map(a => {
 let conditionText = a.condition_type.replace(/_/g, ' ').toUpperCase();
 let detailText = ;
 if (a.params.target_price) {
 detailText = Target: <span class=font-mono text-sky-400 font-semibold></span>;
 } else if (a.params.threshold) {
 detailText = Threshold: <span class=font-mono text-sky-400 font-semibold></span>;
 } else if (a.condition_type === price_cross_indicator) {
 detailText = Ind: <span class=font-mono text-sky-400 font-semibold> ()</span>;
 } else if (a.condition_type === indicator_cross_indicator) {
 detailText = Cross: <span class=font-mono text-sky-400 font-semibold> / </span>;
 }

 const channelBadges = (a.channels || []).map(ch => {
 const icons = { push: '📱 Push', email: '✉️ Email', webhook: '🔗 Hook', in_app: '🔊 App' };
 return <span class=px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-300 border border-slate-700></span>;
 }).join(' ');

 return 
 <div class=p-3 bg-slate-850 hover:bg-slate-800/80 rounded-xl border  transition-all flex flex-col gap-2>
 <div class=flex items-center justify-between>
 <div class=flex items-center gap-2>
 <span class=font-bold text-sm text-slate-100></span>
 <span class=px-2 py-0.5 rounded text-[10px] font-semibold bg-sky-950 text-sky-400 border border-sky-800/60></span>
 <span class=text-[11px] font-medium text-amber-400></span>
 </div>
 <div class=flex items-center gap-2>
 <button class=toggle-alert-btn p-1 rounded-md text-xs font-semibold  data-id=>
 
 </button>
 <button class=test-alert-btn p-1 px-2 rounded-md text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 title=Test Fire Alert data-id=>
 ⚡ Test
 </button>
 <button class=delete-alert-btn p-1 px-2 rounded-md text-xs bg-rose-950/60 hover:bg-rose-900 text-rose-300 border border-rose-900/80 title=Delete Alert data-id=>
 ✕
 </button>
 </div>
 </div>
 <div class=flex items-center justify-between text-xs text-slate-400>
 <div></div>
 <div class=text-[11px]>Frequency: <span class=text-slate-300 font-medium></span></div>
 </div>
 <div class=flex items-center justify-between pt-1 border-t border-slate-800/80 text-[11px] text-slate-400>
 <div class=flex gap-1.5 flex-wrap></div>
 <div>Triggers: <span class=font-mono font-semibold text-slate-200></span></div>
 </div>
 </div>
 ;
 }).join();

 // Wire buttons
 container.querySelectorAll(.toggle-alert-btn).forEach(btn => {
 btn.addEventListener(click, async () => {
 const id = btn.dataset.id;
 await fetch(/api/alerts//toggle, { method: POST });
 await this.loadAlerts();
 });
 });

 container.querySelectorAll(.test-alert-btn).forEach(btn => {
 btn.addEventListener(click, async () => {
 const id = btn.dataset.id;
 const resp = await fetch(/api/alerts//test-trigger, { method: POST });
 if (resp.ok) {
 showToastNotification(Test Dispatched, Test alert payload broadcasted across all configured channels., success);
 }
 });
 });

 container.querySelectorAll(.delete-alert-btn).forEach(btn => {
 btn.addEventListener(click, async () => {
 const id = btn.dataset.id;
 if (confirm(Delete this alert?)) {
 await fetch(/api/alerts/, { method: DELETE });
 await this.loadAlerts();
 }
 });
 });
 },

 async loadLogs() {
 try {
 const resp = await fetch(/api/alerts/history/logs);
 this.logs = await resp.json();
 this.renderLogs();
 } catch (e) {
 console.error(Failed to load logs:, e);
 }
 },

 renderLogs() {
 const container = document.getElementById(trigger-logs-container);
 if (!container) return;

 if (this.logs.length === 0) {
 container.innerHTML = 
 <div class=p-6 text-center text-slate-500 text-xs>No alert trigger logs recorded yet.</div>
 ;
 return;
 }

 container.innerHTML = this.logs.map(log => 
 <div class=p-2.5 bg-slate-900/60 rounded-lg border border-slate-800 flex items-center justify-between text-xs>
 <div class=flex items-center gap-2>
 <span class=text-rose-400 font-bold>🚨</span>
 <div>
 <div class=font-semibold text-slate-200> <span class=text-slate-400 font-normal>()</span></div>
 <div class=text-[11px] text-slate-400></div>
 </div>
 </div>
 <div class=text-right>
 <div class=font-mono font-bold text-sky-400></div>
 <div class=text-[10px] text-slate-500></div>
 </div>
 </div>
 ).join();
 },

 initWebSocket() {
 const protocol = window.location.protocol === https: ? wss: : ws:;
 const wsUrl = ${protocol}///ws;
 this.ws = new WebSocket(wsUrl);

 this.ws.onopen = () => {
 const statusDot = document.getElementById(ws-status-dot);
 const statusText = document.getElementById(ws-status-text);
 if (statusDot) statusDot.className = w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse;
 if (statusText) statusText.innerText = Live Market Connected;
 };

 this.ws.onclose = () => {
 const statusDot = document.getElementById(ws-status-dot);
 const statusText = document.getElementById(ws-status-text);
 if (statusDot) statusDot.className = w-2.5 h-2.5 rounded-full bg-rose-500;
 if (statusText) statusText.innerText = Reconnecting...;
 setTimeout(() => this.initWebSocket(), 3000);
 };

 this.ws.onmessage = (event) => {
 try {
 const msg = JSON.parse(event.data);
 if (msg.type === tick) {
 const tick = msg.data;
 // Update symbol price in symbols list
 const sObj = this.symbols.find(s => s.symbol === tick.symbol);
 if (sObj) {
 sObj.current_price = tick.price;
 const cardPrice = document.getElementById(price-card-);
 if (cardPrice) {
 cardPrice.innerText = tick.price.toFixed(sObj.decimals);
 }
 }

 // If tick is for currently selected symbol, update chart & header
 if (tick.symbol === this.symbol) {
 const headerPrice = document.getElementById(current-symbol-price);
 if (headerPrice && sObj) {
 headerPrice.innerText = tick.price.toFixed(sObj.decimals);
 }
 if (tick.candle_1m && this.chart) {
 this.chart.updateTick(tick.candle_1m);
 }
 }
 } else if (msg.type === alert_triggered) {
 const alertData = msg.data;
 playAlertChime();
 showToastNotification(
 🚨 Alert: (),
 ${alertData.summary} at ,
 alert
 );
 this.loadAlerts();
 this.loadLogs();
 }
 } catch (e) {
 console.error(WS message parse error:, e);
 }
 };
 },

 setupEventListeners() {
 // Timeframe buttons
 document.querySelectorAll(.tf-btn).forEach(btn => {
 btn.addEventListener(click, () => this.changeTimeframe(btn.dataset.tf));
 });

 // Indicator checkboxes
 document.querySelectorAll(.indicator-toggle).forEach(chk => {
 chk.addEventListener(change, () => {
 this.chart.toggleIndicator(chk.dataset.indicator, chk.checked);
 });
 });

 // Push Notification enable button
 const pushBtn = document.getElementById(enable-push-btn);
 if (pushBtn) {
 pushBtn.addEventListener(click, async () => {
 pushBtn.disabled = true;
 pushBtn.innerText = Enabling...;
 const res = await registerPushNotifications(this.vapidPublicKey);
 if (res.success) {
 pushBtn.className = px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800;
 pushBtn.innerText = ✓ Push Enabled;
 showToastNotification(Push Notifications Active, You will receive background alerts on this browser., success);
 } else {
 pushBtn.disabled = false;
 pushBtn.innerText = Enable Push Alerts;
 showToastNotification(Push Error, res.message, warning);
 }
 });
 }

 // Quick Tick Simulation Injector
 const injectBtn = document.getElementById(simulate-tick-btn);
 if (injectBtn) {
 injectBtn.addEventListener(click, async () => {
 const priceInput = document.getElementById(simulate-price-input);
 const priceVal = parseFloat(priceInput.value);
 if (!priceVal) return;

 await fetch(/api/market/tick-override, {
 method: POST,
 headers: { Content-Type: application/json },
 body: JSON.stringify({ symbol: this.symbol, price: priceVal })
 });
 showToastNotification(Injected Price, Simulated price pushed for , info);
 });
 }

 // Create Alert Modal Open/Close
 const openModalBtn = document.getElementById(open-alert-modal-btn);
 const closeModalBtn = document.getElementById(close-alert-modal-btn);
 const modal = document.getElementById(alert-modal);
 if (openModalBtn && modal) {
 openModalBtn.addEventListener(click, () => {
 document.getElementById(modal-alert-symbol).value = this.symbol;
 document.getElementById(modal-alert-timeframe).value = this.timeframe;
 const sObj = this.symbols.find(s => s.symbol === this.symbol);
 if (sObj) {
 document.getElementById(modal-target-price).value = sObj.current_price.toFixed(sObj.decimals);
 }
 modal.classList.remove(hidden);
 });
 }
 if (closeModalBtn && modal) {
 closeModalBtn.addEventListener(click, () => modal.classList.add(hidden));
 }

 // Create Alert Form Submit
 const alertForm = document.getElementById(create-alert-form);
 if (alertForm) {
 alertForm.addEventListener(submit, async (e) => {
 e.preventDefault();
 await this.handleCreateAlertSubmit();
 });
 }

 // Settings Modal Open/Close
 const openSettingsBtn = document.getElementById(open-settings-btn);
 const closeSettingsBtn = document.getElementById(close-settings-btn);
 const settingsModal = document.getElementById(settings-modal);
 if (openSettingsBtn && settingsModal) {
 openSettingsBtn.addEventListener(click, async () => {
 await this.loadSettingsIntoModal();
 settingsModal.classList.remove(hidden);
 });
 }
 if (closeSettingsBtn && settingsModal) {
 closeSettingsBtn.addEventListener(click, () => settingsModal.classList.add(hidden));
 }

 // Settings Form Submit
 const settingsForm = document.getElementById(settings-form);
 if (settingsForm) {
 settingsForm.addEventListener(submit, async (e) => {
 e.preventDefault();
 await this.handleSettingsSubmit();
 });
 }

 // Test Push Button in Settings
 const testPushBtn = document.getElementById(settings-test-push-btn);
 if (testPushBtn) {
 testPushBtn.addEventListener(click, async () => {
 const resp = await fetch(/api/notifications/test-push, { method: POST });
 const res = await resp.json();
 if (resp.ok) {
 showToastNotification(Push Test Dispatched, Sent to registered browser(s)., success);
 } else {
 showToastNotification(Push Test Failed, res.detail || Error, warning);
 }
 });
 }

 // Test Email Button in Settings
 const testEmailBtn = document.getElementById(settings-test-email-btn);
 if (testEmailBtn) {
 testEmailBtn.addEventListener(click, async () => {
 const emailInput = document.getElementById(settings-test-email-target).value;
 if (!emailInput) {
 alert(Please enter recipient email in test box);
 return;
 }
 const resp = await fetch(/api/notifications/test-email, {
 method: POST,
 headers: { Content-Type: application/json },
 body: JSON.stringify({ email: emailInput })
 });
 const res = await resp.json();
 if (resp.ok) {
 showToastNotification(Email Test Sent, Check your inbox at , success);
 } else {
 showToastNotification(Email Test Failed, res.detail || Check SMTP settings, warning);
 }
 });
 }
 },

 setupConditionFormWatcher() {
 const condSelect = document.getElementById(modal-condition-type);
 if (!condSelect) return;

 condSelect.addEventListener(change, () => {
 const val = condSelect.value;
 const priceGroup = document.getElementById(group-target-price);
 const indCrossIndGroup = document.getElementById(group-ind-cross-ind);
 const indValGroup = document.getElementById(group-ind-value);
 const channelGroup = document.getElementById(group-channel);

 // Hide all dynamic groups first
 priceGroup.classList.add(hidden);
 indCrossIndGroup.classList.add(hidden);
 indValGroup.classList.add(hidden);
 channelGroup.classList.add(hidden);

 if ([price_cross_up, price_cross_down, price_greater, price_less].includes(val)) {
 priceGroup.classList.remove(hidden);
 } else if (val === price_cross_indicator) {
 indValGroup.classList.remove(hidden);
 } else if (val === indicator_cross_indicator) {
 indCrossIndGroup.classList.remove(hidden);
 } else if (val === indicator_cross_value) {
 indValGroup.classList.remove(hidden);
 } else if ([channel_exit, channel_enter].includes(val)) {
 channelGroup.classList.remove(hidden);
 }
 });
 },

 async handleCreateAlertSubmit() {
 const symbol = document.getElementById(modal-alert-symbol).value;
 const timeframe = document.getElementById(modal-alert-timeframe).value;
 const condType = document.getElementById(modal-condition-type).value;
 const triggerFreq = document.getElementById(modal-trigger-freq).value;
 const targetEmail = document.getElementById(modal-alert-email).value.trim();
 const webhookUrl = document.getElementById(modal-alert-webhook).value.trim();
 const customMessage = document.getElementById(modal-alert-message).value.trim();

 const channels = [];
 if (document.getElementById(modal-ch-push).checked) channels.push(push);
 if (document.getElementById(modal-ch-email).checked && targetEmail) channels.push(email);
 if (document.getElementById(modal-ch-inapp).checked) channels.push(in_app);
 if (document.getElementById(modal-ch-webhook).checked && webhookUrl) channels.push(webhook);

 const params = {};

 if ([price_cross_up, price_cross_down, price_greater, price_less].includes(condType)) {
 params.target_price = parseFloat(document.getElementById(modal-target-price).value);
 } else if (condType === price_cross_indicator) {
 params.direction = document.getElementById(modal-indval-direction).value;
 params.indicator = {
 type: document.getElementById(modal-indval-type).value,
 period: parseInt(document.getElementById(modal-indval-period).value)
 };
 } else if (condType === indicator_cross_indicator) {
 params.direction = document.getElementById(modal-ind1-direction).value;
 params.indicator_1 = {
 type: document.getElementById(modal-ind1-type).value,
 period: parseInt(document.getElementById(modal-ind1-period).value)
 };
 params.indicator_2 = {
 type: document.getElementById(modal-ind2-type).value,
 period: parseInt(document.getElementById(modal-ind2-period).value)
 };
 } else if (condType === indicator_cross_value) {
 params.direction = document.getElementById(modal-indval-direction).value;
 params.threshold = parseFloat(document.getElementById(modal-indval-threshold).value);
 params.indicator = {
 type: document.getElementById(modal-indval-type).value,
 period: parseInt(document.getElementById(modal-indval-period).value)
 };
 } else if ([channel_exit, channel_enter].includes(condType)) {
 params.lower_bound = parseFloat(document.getElementById(modal-channel-lower).value);
 params.upper_bound = parseFloat(document.getElementById(modal-channel-upper).value);
 }

 const alertPayload = {
 symbol: symbol,
 timeframe: timeframe,
 condition_type: condType,
 params: params,
 trigger_frequency: triggerFreq,
 cooldown_minutes: 5,
 channels: channels.length > 0 ? channels : [in_app],
 target_email: targetEmail || null,
 webhook_url: webhookUrl || null,
 message: customMessage || null,
 is_active: true
 };

 try {
 const resp = await fetch(/api/alerts, {
 method: POST,
 headers: { Content-Type: application/json },
 body: JSON.stringify(alertPayload)
 });

 if (resp.ok) {
 document.getElementById(alert-modal).classList.add(hidden);
 showToastNotification(Alert Created, Alert for set successfully., success);
 await this.loadAlerts();
 } else {
 const err = await resp.json();
 alert(Error creating alert:  + (err.detail || Check input parameters));
 }
 } catch (e) {
 console.error(Alert creation failed:, e);
 }
 },

 async loadSettingsIntoModal() {
 try {
 const resp = await fetch(/api/settings);
 const s = await resp.json();
 document.getElementById(setting-smtp-host).value = s.smtp_host || ;
 document.getElementById(setting-smtp-port).value = s.smtp_port || 587;
 document.getElementById(setting-smtp-user).value = s.smtp_user || ;
 document.getElementById(setting-smtp-from).value = s.smtp_from_email || ;
 document.getElementById(setting-smtp-tls).checked = s.smtp_use_tls !== false;
 document.getElementById(setting-discord-webhook).value = s.discord_webhook_url || ;
 document.getElementById(setting-twelvedata-key).value = s.twelve_data_api_key || ;
 document.getElementById(setting-finnhub-key).value = s.finnhub_api_key || ;
 } catch (e) {
 console.error(Failed to load settings:, e);
 }
 },

 async handleSettingsSubmit() {
 const payload = {
 smtp_host: document.getElementById(setting-smtp-host).value.trim(),
 smtp_port: parseInt(document.getElementById(setting-smtp-port).value) || 587,
 smtp_user: document.getElementById(setting-smtp-user).value.trim(),
 smtp_from_email: document.getElementById(setting-smtp-from).value.trim(),
 smtp_use_tls: document.getElementById(setting-smtp-tls).checked,
 discord_webhook_url: document.getElementById(setting-discord-webhook).value.trim(),
 twelve_data_api_key: document.getElementById(setting-twelvedata-key).value.trim(),
 finnhub_api_key: document.getElementById(setting-finnhub-key).value.trim(),
 };

 const pwd = document.getElementById(setting-smtp-pass).value;
 if (pwd) payload.smtp_password = pwd;

 try {
 const resp = await fetch(/api/settings, {
 method: POST,
 headers: { Content-Type: application/json },
 body: JSON.stringify(payload)
 });
 if (resp.ok) {
 document.getElementById(settings-modal).classList.add(hidden);
 showToastNotification(Settings Saved, Application settings updated., success);
 }
 } catch (e) {
 console.error(Settings save failed:, e);
 }
 }
 };

 window.App = App;
 App.init();
});
