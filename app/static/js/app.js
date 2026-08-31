document.addEventListener("DOMContentLoaded", () => {
    const App = {
        symbol: "EURUSD",
        timeframe: "1m",
        chart: null,
        symbols: [],
        alerts: [],
        logs: [],
        ws: null,
        vapidPublicKey: window.VAPID_PUBLIC_KEY || "",

        async init() {
            this.initTheme();
            this.chart = new TradingChart("chart-container");
            await this.loadSymbols();
            await this.loadAlerts();
            await this.loadLogs();
            await this.chart.loadCandles(this.symbol, this.timeframe);
            this.chart.setAlertPriceLines(this.alerts);

            this.initWebSocket();
            this.setupEventListeners();
            this.setupConditionFormWatcher();
        },

        initTheme() {
            const savedTheme = localStorage.getItem("app_theme") || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
            this.setTheme(savedTheme === "dark");
        },

        setTheme(isDark) {
            const icon = document.getElementById("theme-toggle-icon");
            if (isDark) {
                document.documentElement.classList.add("dark");
                localStorage.setItem("app_theme", "dark");
                if (icon) icon.textContent = "☀️";
            } else {
                document.documentElement.classList.remove("dark");
                localStorage.setItem("app_theme", "light");
                if (icon) icon.textContent = "🌙";
            }
            if (this.chart) {
                this.chart.setTheme(isDark);
            }
        },

        async loadSymbols() {
            try {
                const resp = await fetch("/api/market/symbols");
                this.symbols = await resp.json();
                this.renderSymbolsGrid();
            } catch (e) {
                console.error("Failed to load symbols:", e);
            }
        },

        renderSymbolsGrid() {
            const container = document.getElementById("symbols-grid");
            if (!container) return;

            container.innerHTML = this.symbols.map(s => {
                const isActive = s.symbol === this.symbol;
                return `
                <button class="symbol-btn p-2 rounded-xl border text-left transition-all ${
                    isActive 
                        ? 'bg-sky-50 dark:bg-sky-950/80 border-sky-500 text-sky-600 dark:text-sky-400 shadow-sm' 
                        : 'bg-slate-50 dark:bg-slate-850 hover:bg-slate-100 dark:hover:bg-slate-800 border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200'
                }" data-symbol="${s.symbol}">
                    <div class="font-bold text-xs leading-tight">${s.symbol}</div>
                    <div class="text-[10px] text-slate-500 dark:text-slate-400 truncate">${s.name}</div>
                    <div class="font-mono font-bold text-xs mt-1 text-sky-600 dark:text-sky-400" id="rate-${s.symbol}">
                        ${s.current_price.toFixed(s.decimals)}
                    </div>
                </button>
                `;
            }).join("");

            container.querySelectorAll(".symbol-btn").forEach(btn => {
                btn.addEventListener("click", () => {
                    this.changeSymbol(btn.dataset.symbol);
                });
            });

            this.updateHeaderPrice();
        },

        updateHeaderPrice() {
            const currentObj = this.symbols.find(s => s.symbol === this.symbol);
            if (!currentObj) return;

            const titleEl = document.getElementById("current-symbol-title");
            if (titleEl) titleEl.innerText = `${currentObj.name} (${currentObj.symbol})`;
            const priceEl = document.getElementById("current-symbol-price");
            if (priceEl) {
                priceEl.innerText = currentObj.current_price.toFixed(currentObj.decimals);
            }
        },

        async changeSymbol(newSym) {
            if (this.symbol === newSym) return;
            this.symbol = newSym;
            this.renderSymbolsGrid();
            await this.chart.loadCandles(this.symbol, this.timeframe);
            this.chart.setAlertPriceLines(this.alerts);
        },

        async changeTimeframe(newTf) {
            if (this.timeframe === newTf) return;
            this.timeframe = newTf;
            document.querySelectorAll(".tf-btn").forEach(b => {
                if (b.dataset.tf === newTf) {
                    b.classList.add("bg-sky-600", "text-white");
                    b.classList.remove("text-slate-600", "dark:text-slate-400", "hover:bg-slate-100", "dark:hover:bg-slate-800");
                } else {
                    b.classList.remove("bg-sky-600", "text-white");
                    b.classList.add("text-slate-600", "dark:text-slate-400", "hover:bg-slate-100", "dark:hover:bg-slate-800");
                }
            });
            await this.chart.loadCandles(this.symbol, this.timeframe);
        },

        async loadAlerts() {
            try {
                const resp = await fetch("/api/alerts");
                this.alerts = await resp.json();
                this.renderAlerts();
                if (this.chart) {
                    this.chart.setAlertPriceLines(this.alerts);
                }
            } catch (e) {
                console.error("Failed to load alerts:", e);
            }
        },

        renderAlerts() {
            const container = document.getElementById("alerts-list");
            const badgeCount = document.getElementById("alerts-count-badge");
            if (badgeCount) {
                const activeCount = this.alerts.filter(a => a.is_active).length;
                badgeCount.innerText = activeCount;
            }

            if (!container) return;

            if (this.alerts.length === 0) {
                container.innerHTML = `
                    <div class="p-6 text-center text-slate-400 dark:text-slate-500">
                        <div class="text-2xl mb-1">🔔</div>
                        <div class="font-semibold text-xs text-slate-600 dark:text-slate-400">No alerts configured yet</div>
                        <div class="text-[11px] mt-0.5">Click Create Alert to set price or indicator triggers.</div>
                    </div>
                `;
                return;
            }

            container.innerHTML = this.alerts.map(a => {
                let conditionText = a.condition_type.replace(/_/g, " ").toUpperCase();
                let detailText = "";
                if (a.params.target_price) {
                    detailText = `Target: <span class="font-mono text-sky-600 dark:text-sky-400 font-bold">${a.params.target_price}</span>`;
                } else if (a.params.threshold) {
                    detailText = `Threshold: <span class="font-mono text-sky-600 dark:text-sky-400 font-bold">${a.params.threshold}</span>`;
                } else if (a.condition_type === "price_cross_indicator") {
                    detailText = `Ind: <span class="font-mono text-sky-600 dark:text-sky-400 font-bold">${a.params.indicator?.type?.toUpperCase()} (${a.params.indicator?.period})</span>`;
                }

                return `
                <div class="p-3 bg-slate-50 dark:bg-slate-850 hover:bg-slate-100 dark:hover:bg-slate-800/80 rounded-xl border border-slate-200 dark:border-slate-800 transition-all flex flex-col gap-1.5 text-xs">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <span class="font-bold text-slate-900 dark:text-slate-100">${a.symbol}</span>
                            <span class="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-sky-100 dark:bg-sky-950 text-sky-700 dark:text-sky-400 border border-sky-200 dark:border-sky-800/60">${a.timeframe}</span>
                            <span class="text-[11px] font-semibold text-amber-600 dark:text-amber-400">${conditionText}</span>
                        </div>
                        <div class="flex items-center gap-1.5">
                            <button class="toggle-alert-btn px-2 py-0.5 rounded text-[10px] font-bold ${a.is_active ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-400 border border-emerald-300 dark:border-emerald-800' : 'bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400'}" data-id="${a.id}">
                                ${a.is_active ? "Active" : "Paused"}
                            </button>
                            <button class="test-alert-btn px-1.5 py-0.5 rounded text-[10px] bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700" title="Test Fire Alert" data-id="${a.id}">
                                ⚡
                            </button>
                            <button class="delete-alert-btn px-1.5 py-0.5 rounded text-[10px] bg-rose-100 dark:bg-rose-950/60 hover:bg-rose-200 dark:hover:bg-rose-900 text-rose-700 dark:text-rose-300 border border-rose-300 dark:border-rose-900/80" title="Delete Alert" data-id="${a.id}">
                                ✕
                            </button>
                        </div>
                    </div>
                    <div class="flex items-center justify-between text-slate-600 dark:text-slate-400 text-[11px]">
                        <div>${detailText}</div>
                        <div>Fired: <span class="font-mono font-bold text-slate-800 dark:text-slate-200">${a.trigger_count}x</span></div>
                    </div>
                </div>
                `;
            }).join("");

            // Wire action buttons
            container.querySelectorAll(".toggle-alert-btn").forEach(btn => {
                btn.addEventListener("click", async () => {
                    const id = btn.dataset.id;
                    await fetch(`/api/alerts/${id}/toggle`, { method: "POST" });
                    await this.loadAlerts();
                });
            });

            container.querySelectorAll(".test-alert-btn").forEach(btn => {
                btn.addEventListener("click", async () => {
                    const id = btn.dataset.id;
                    const resp = await fetch(`/api/alerts/${id}/test-trigger`, { method: "POST" });
                    if (resp.ok) {
                        showToastNotification("Test Dispatched", "Test alert broadcasted across channels.", "success");
                    }
                });
            });

            container.querySelectorAll(".delete-alert-btn").forEach(btn => {
                btn.addEventListener("click", async () => {
                    const id = btn.dataset.id;
                    if (confirm("Delete this alert?")) {
                        await fetch(`/api/alerts/${id}`, { method: "DELETE" });
                        await this.loadAlerts();
                    }
                });
            });
        },

        async loadLogs() {
            try {
                const resp = await fetch("/api/alerts/history/logs");
                this.logs = await resp.json();
                this.renderLogs();
            } catch (e) {
                console.error("Failed to load logs:", e);
            }
        },

        renderLogs() {
            const container = document.getElementById("trigger-logs-list");
            if (!container) return;

            if (this.logs.length === 0) {
                container.innerHTML = `
                    <div class="p-6 text-center text-slate-400 dark:text-slate-500 text-xs">No alert trigger logs recorded yet.</div>
                `;
                return;
            }

            container.innerHTML = this.logs.map(log => `
                <div class="p-2.5 bg-slate-50 dark:bg-slate-900/60 rounded-xl border border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs transition-colors">
                    <div class="flex items-center gap-2">
                        <span class="text-rose-500 font-bold">🚨</span>
                        <div>
                            <div class="font-bold text-slate-900 dark:text-slate-200">${log.symbol} <span class="text-slate-500 font-normal">(${log.timeframe})</span></div>
                            <div class="text-[11px] text-slate-600 dark:text-slate-400">${log.condition_summary}</div>
                        </div>
                    </div>
                    <div class="text-right">
                        <div class="font-mono font-bold text-sky-600 dark:text-sky-400">${log.trigger_price}</div>
                        <div class="text-[10px] text-slate-400 dark:text-slate-500">${new Date(log.timestamp).toLocaleTimeString()}</div>
                    </div>
                </div>
            `).join("");
        },

        initWebSocket() {
            const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                const dot = document.getElementById("ws-status-dot");
                const text = document.getElementById("ws-status-text");
                if (dot) dot.className = "w-2 h-2 rounded-full bg-emerald-500";
                if (text) text.innerText = "Live Stream Connected";
            };

            this.ws.onclose = () => {
                const dot = document.getElementById("ws-status-dot");
                const text = document.getElementById("ws-status-text");
                if (dot) dot.className = "w-2 h-2 rounded-full bg-amber-500";
                if (text) text.innerText = "Reconnecting...";
                setTimeout(() => this.initWebSocket(), 3000);
            };

            this.ws.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data);
                    if (msg.type === "tick") {
                        const tick = msg.data;
                        const cardPrice = document.getElementById(`rate-${tick.symbol}`);
                        if (cardPrice) {
                            cardPrice.innerText = tick.price.toFixed(cardPrice.innerText.includes(".") ? cardPrice.innerText.split(".")[1].length : 2);
                        }

                        if (tick.symbol === this.symbol) {
                            const curPriceEl = document.getElementById("current-symbol-price");
                            if (curPriceEl) curPriceEl.innerText = tick.price.toFixed(curPriceEl.innerText.includes(".") ? curPriceEl.innerText.split(".")[1].length : 2);
                            this.chart.updateTick(tick.symbol, tick);
                        }
                    } else if (msg.type === "alert_triggered") {
                        showToastNotification("🚨 Alert Triggered", msg.data.summary, "warning");
                        this.loadAlerts();
                        this.loadLogs();
                    }
                } catch (e) {
                    console.error("WS parse error:", e);
                }
            };
        },

        setupEventListeners() {
            // Theme toggle button
            const themeBtn = document.getElementById("theme-toggle-btn");
            if (themeBtn) {
                themeBtn.addEventListener("click", () => {
                    const isDark = document.documentElement.classList.contains("dark");
                    this.setTheme(!isDark);
                });
            }

            // Timeframe selector buttons
            document.querySelectorAll(".tf-btn").forEach(btn => {
                btn.addEventListener("click", () => this.changeTimeframe(btn.dataset.tf));
            });

            // Indicator checkboxes
            document.querySelectorAll(".indicator-toggle").forEach(chk => {
                chk.addEventListener("change", () => {
                    this.chart.toggleIndicator(chk.dataset.indicator, chk.checked);
                });
            });

            // Push Notification enable button
            const pushBtn = document.getElementById("enable-push-btn");
            if (pushBtn) {
                pushBtn.addEventListener("click", async () => {
                    pushBtn.disabled = true;
                    pushBtn.innerText = "Enabling...";
                    const res = await registerPushNotifications(this.vapidPublicKey);
                    if (res.success) {
                        pushBtn.className = "px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-400 border border-emerald-300 dark:border-emerald-800";
                        pushBtn.innerText = "✓ Push Enabled";
                        showToastNotification("Push Notifications Active", "You will receive background alerts on this browser.", "success");
                    } else {
                        pushBtn.disabled = false;
                        pushBtn.innerText = "📱 Enable Push Alerts";
                        showToastNotification("Push Notice", res.message, "warning");
                    }
                });
            }

            // Quick Tick Simulation Injector
            const injectBtn = document.getElementById("simulate-tick-btn");
            if (injectBtn) {
                injectBtn.addEventListener("click", async () => {
                    const priceInput = document.getElementById("simulate-price-input");
                    const priceVal = parseFloat(priceInput.value);
                    if (!priceVal) return;

                    await fetch("/api/market/tick-override", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ symbol: this.symbol, price: priceVal })
                    });
                    showToastNotification("Injected Price", `Simulated price ${priceVal} pushed for ${this.symbol}`, "info");
                });
            }

            // Create Alert Modal
            const openModalBtn = document.getElementById("open-alert-modal-btn");
            const closeModalBtn = document.getElementById("close-alert-modal-btn");
            const cancelModalBtn = document.getElementById("cancel-alert-modal-btn");
            const modal = document.getElementById("alert-modal");
            
            if (openModalBtn && modal) {
                openModalBtn.addEventListener("click", () => {
                    document.getElementById("modal-symbol").value = this.symbol;
                    document.getElementById("modal-timeframe").value = this.timeframe;
                    modal.classList.remove("hidden");
                });
            }
            if (closeModalBtn && modal) {
                closeModalBtn.addEventListener("click", () => modal.classList.add("hidden"));
            }
            if (cancelModalBtn && modal) {
                cancelModalBtn.addEventListener("click", () => modal.classList.add("hidden"));
            }

            // Create Alert Form Submit
            const alertForm = document.getElementById("create-alert-form");
            if (alertForm) {
                alertForm.addEventListener("submit", async (e) => {
                    e.preventDefault();
                    await this.handleCreateAlertSubmit();
                });
            }

            // Channel Email toggle
            const emailChk = document.getElementById("modal-channel-email");
            const emailRow = document.getElementById("modal-email-row");
            if (emailChk && emailRow) {
                emailChk.addEventListener("change", () => {
                    if (emailChk.checked) emailRow.classList.remove("hidden");
                    else emailRow.classList.add("hidden");
                });
            }

            // Settings Modal
            const openSettingsBtn = document.getElementById("open-settings-btn");
            const closeSettingsBtn = document.getElementById("close-settings-modal-btn");
            const settingsModal = document.getElementById("settings-modal");
            if (openSettingsBtn && settingsModal) {
                openSettingsBtn.addEventListener("click", () => settingsModal.classList.remove("hidden"));
            }
            if (closeSettingsBtn && settingsModal) {
                closeSettingsBtn.addEventListener("click", () => settingsModal.classList.add("hidden"));
            }

            // Test Push in Settings
            const testPushBtn = document.getElementById("send-test-push-btn");
            if (testPushBtn) {
                testPushBtn.addEventListener("click", async () => {
                    const resp = await fetch("/api/notifications/test-push", { method: "POST" });
                    const res = await resp.json();
                    if (resp.ok) {
                        showToastNotification("Push Test Dispatched", "Sent test notification to registered browsers/devices.", "success");
                    } else {
                        showToastNotification("Push Test", res.detail || "Dispatched", "warning");
                    }
                });
            }

            // Save Settings
            const saveSettingsBtn = document.getElementById("save-settings-btn");
            if (saveSettingsBtn && settingsModal) {
                saveSettingsBtn.addEventListener("click", () => {
                    settingsModal.classList.add("hidden");
                    showToastNotification("Settings Saved", "Settings updated successfully.", "success");
                });
            }
        },

        setupConditionFormWatcher() {
            const condSelect = document.getElementById("modal-condition-type");
            const container = document.getElementById("dynamic-params-container");
            if (!condSelect || !container) return;

            const renderParams = () => {
                const val = condSelect.value;
                if (["price_cross_up", "price_cross_down", "price_greater", "price_less"].includes(val)) {
                    const sObj = this.symbols.find(s => s.symbol === this.symbol);
                    const defaultP = sObj ? sObj.current_price.toFixed(sObj.decimals) : "1.08500";
                    container.innerHTML = `
                        <div>
                            <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Target Price Level</label>
                            <input type="number" step="any" id="modal-target-price" value="${defaultP}" class="w-full bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg p-2 text-xs font-mono">
                        </div>
                    `;
                } else if (val === "price_cross_indicator") {
                    container.innerHTML = `
                        <div class="grid grid-cols-3 gap-2">
                            <div>
                                <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Indicator</label>
                                <select id="modal-ind-type" class="w-full bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg p-2 text-xs">
                                    <option value="ema">EMA</option>
                                    <option value="sma">SMA</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Period</label>
                                <input type="number" id="modal-ind-period" value="50" class="w-full bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg p-2 text-xs">
                            </div>
                            <div>
                                <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Direction</label>
                                <select id="modal-ind-dir" class="w-full bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg p-2 text-xs">
                                    <option value="above">Crosses Above</option>
                                    <option value="below">Crosses Below</option>
                                </select>
                            </div>
                        </div>
                    `;
                } else if (val === "indicator_cross_value") {
                    container.innerHTML = `
                        <div class="grid grid-cols-2 gap-2">
                            <div>
                                <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">RSI Direction</label>
                                <select id="modal-ind-dir" class="w-full bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg p-2 text-xs">
                                    <option value="above">Crosses Above</option>
                                    <option value="below">Crosses Below</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Threshold (e.g. 70 or 30)</label>
                                <input type="number" id="modal-rsi-threshold" value="70" class="w-full bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg p-2 text-xs font-mono">
                            </div>
                        </div>
                    `;
                } else {
                    container.innerHTML = `
                        <div>
                            <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Target Price</label>
                            <input type="number" step="any" id="modal-target-price" value="1.0850" class="w-full bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg p-2 text-xs font-mono">
                        </div>
                    `;
                }
            };

            condSelect.addEventListener("change", renderParams);
            renderParams();
        },

        async handleCreateAlertSubmit() {
            const symbol = document.getElementById("modal-symbol").value;
            const timeframe = document.getElementById("modal-timeframe").value;
            const condType = document.getElementById("modal-condition-type").value;
            const freq = document.getElementById("modal-frequency").value;
            const customMessage = document.getElementById("modal-message").value.trim();
            const targetEmail = document.getElementById("modal-target-email") ? document.getElementById("modal-target-email").value.trim() : null;

            const channels = ["in_app"];
            if (document.getElementById("modal-channel-push").checked) channels.push("push");
            if (document.getElementById("modal-channel-email").checked && targetEmail) channels.push("email");

            const params = {};
            if (["price_cross_up", "price_cross_down", "price_greater", "price_less"].includes(condType)) {
                params.target_price = parseFloat(document.getElementById("modal-target-price").value);
            } else if (condType === "price_cross_indicator") {
                params.direction = document.getElementById("modal-ind-dir").value;
                params.indicator = {
                    type: document.getElementById("modal-ind-type").value,
                    period: parseInt(document.getElementById("modal-ind-period").value)
                };
            } else if (condType === "indicator_cross_value") {
                params.direction = document.getElementById("modal-ind-dir").value;
                params.threshold = parseFloat(document.getElementById("modal-rsi-threshold").value);
                params.indicator = { type: "rsi", period: 14 };
            }

            const alertPayload = {
                symbol: symbol,
                timeframe: timeframe,
                condition_type: condType,
                params: params,
                trigger_frequency: freq,
                channels: channels,
                target_email: targetEmail || null,
                message: customMessage || null,
                is_active: true
            };

            try {
                const resp = await fetch("/api/alerts", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(alertPayload)
                });

                if (resp.ok) {
                    document.getElementById("alert-modal").classList.add("hidden");
                    showToastNotification("Alert Created", `Alert for ${symbol} set successfully.`, "success");
                    await this.loadAlerts();
                } else {
                    const err = await resp.json();
                    alert("Error creating alert: " + (err.detail || "Check input parameters"));
                }
            } catch (e) {
                console.error("Alert creation failed:", e);
            }
        }
    };

    window.App = App;
    App.init();
});
