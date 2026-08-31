function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

let audioCtx = null;
function playAlertChime(soundType = "chime") {
    try {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }

        const now = audioCtx.currentTime;
        if (soundType === "radar") {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(1200, now);
            osc.frequency.exponentialRampToValueAtTime(300, now + 0.4);
            gain.gain.setValueAtTime(0.4, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.4);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start(now);
            osc.stop(now + 0.4);
        } else if (soundType === "siren") {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(400, now);
            osc.frequency.linearRampToValueAtTime(800, now + 0.25);
            osc.frequency.linearRampToValueAtTime(400, now + 0.5);
            gain.gain.setValueAtTime(0.3, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start(now);
            osc.stop(now + 0.6);
        } else {
            // Standard Chime (Tone 1 + Tone 2)
            const osc1 = audioCtx.createOscillator();
            const gain1 = audioCtx.createGain();
            osc1.type = 'sine';
            osc1.frequency.setValueAtTime(587.33, now); // D5
            gain1.gain.setValueAtTime(0.3, now);
            gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
            osc1.connect(gain1);
            gain1.connect(audioCtx.destination);
            osc1.start(now);
            osc1.stop(now + 0.35);

            const osc2 = audioCtx.createOscillator();
            const gain2 = audioCtx.createGain();
            osc2.type = 'sine';
            osc2.frequency.setValueAtTime(880.00, now + 0.12); // A5
            gain2.gain.setValueAtTime(0.4, now + 0.12);
            gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
            osc2.connect(gain2);
            gain2.connect(audioCtx.destination);
            osc2.start(now + 0.12);
            osc2.stop(now + 0.6);
        }
    } catch (e) {
        console.warn("Audio chime error:", e);
    }
}

async function registerPushNotifications(vapidPublicKey) {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        console.warn("Web Push is not supported in this browser.");
        return { success: false, message: "Web Push not supported in this browser" };
    }

    try {
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
            return { success: false, message: "Push notification permission denied by user" };
        }

        const registration = await navigator.serviceWorker.register('/static/js/sw.js');
        await navigator.serviceWorker.ready;

        let subscription = await registration.pushManager.getSubscription();
        if (!subscription && vapidPublicKey) {
            const convertedVapidKey = urlBase64ToUint8Array(vapidPublicKey);
            subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: convertedVapidKey
            });
        }

        if (subscription) {
            const subJson = subscription.toJSON();
            const resp = await fetch('/api/notifications/subscribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    endpoint: subJson.endpoint,
                    keys: {
                        p256dh: subJson.keys?.p256dh,
                        auth: subJson.keys?.auth
                    }
                })
            });

            if (resp.ok) {
                return { success: true, message: "Push notifications active!" };
            }
        }
        return { success: false, message: "Failed to store subscription on server" };
    } catch (err) {
        console.error("Push registration error:", err);
        return { success: false, message: err.message };
    }
}

function showToastNotification(title, message, type = "info") {
    const toastContainer = document.getElementById("toast-container");
    if (!toastContainer) return;

    const toast = document.createElement("div");
    const icons = {
        success: "✅",
        warning: "🚨",
        info: "ℹ️",
        alert: "🔔"
    };

    toast.className = "p-3.5 rounded-xl border shadow-xl backdrop-blur-md transition-all duration-300 transform translate-y-2 opacity-0 flex items-start gap-3 w-80 md:w-96 bg-slate-900/95 border-slate-700 text-slate-100";
    toast.innerHTML = `
        <div class="text-lg shrink-0 mt-0.5">${icons[type] || "🔔"}</div>
        <div class="flex-1 min-w-0">
            <div class="font-bold text-xs leading-snug">${title}</div>
            <div class="text-[11px] text-slate-300 mt-0.5 break-words">${message}</div>
        </div>
        <button class="text-xs text-slate-400 hover:text-white ml-1" onclick="this.parentElement.remove()">✕</button>
    `;

    toastContainer.appendChild(toast);
    requestAnimationFrame(() => {
        toast.classList.remove("translate-y-2", "opacity-0");
        toast.classList.add("translate-y-0", "opacity-100");
    });

    setTimeout(() => {
        toast.classList.add("opacity-0", "translate-y-2");
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}
