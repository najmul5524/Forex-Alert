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
function playAlertChime() {
    try {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }

        const now = audioCtx.currentTime;
        // Tone 1
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

        // Tone 2 (Higher, 120ms later)
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
    } catch (e) {
        console.warn(Audio chime error:, e);
    }
}

async function registerPushNotifications(vapidPublicKey) {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        console.warn(Web Push is not supported in this browser.);
        return { success: false, message: Web Push not supported in this browser };
    }

    try {
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
            return { success: false, message: Push notification permission denied by user };
        }

        const registration = await navigator.serviceWorker.register('/static/js/sw.js');
        await navigator.serviceWorker.ready;

        let subscription = await registration.pushManager.getSubscription();
        if (!subscription) {
            const convertedVapidKey = urlBase64ToUint8Array(vapidPublicKey);
            subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: convertedVapidKey
            });
        }

        const subJson = subscription.toJSON();
        const resp = await fetch('/api/notifications/subscribe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                endpoint: subJson.endpoint,
                keys: {
                    p256dh: subJson.keys.p256dh,
                    auth: subJson.keys.auth
                }
            })
        });

        if (resp.ok) {
            return { success: true, message: Push notifications active! };
        } else {
            return { success: false, message: Failed to store subscription on server };
        }
    } catch (err) {
        console.error(Push registration error:, err);
        return { success: false, message: err.message };
    }
}

function showToastNotification(title, message, type = info) {
    const toastContainer = document.getElementById(toast-container);
    if (!toastContainer) return;

    const toast = document.createElement(div);
    const colors = {
        success: bg-emerald-900/90 border-emerald-500 text-emerald-100,
        alert: bg-rose-950/90 border-rose-500 text-rose-100 shadow-rose-900/50,
        info: bg-slate-800/90 border-sky-500 text-slate-100,
        warning: bg-amber-900/90 border-amber-500 text-amber-100
    };

    toast.className = p-4 rounded-xl border shadow-xl backdrop-blur-md transition-all duration-300 transform translate-y-2 opacity-0 flex items-start gap-3 w-80 md:w-96 ;
    toast.innerHTML = 
        <div class=text-xl shrink-0 mt-0.5>
            
        </div>
        <div class=flex-1 min-w-0>
            <div class=font-semibold text-sm leading-snug></div>
            <div class=text-xs opacity-90 mt-1 break-words></div>
        </div>
        <button class=text-xs opacity-60 hover:opacity-100 ml-1 onclick=this.parentElement.remove()>✕</button>
    ;

    toastContainer.appendChild(toast);
    requestAnimationFrame(() => {
        toast.classList.remove(translate-y-2, opacity-0);
        toast.classList.add(translate-y-0, opacity-100);
    });

    setTimeout(() => {
        toast.classList.add(opacity-0, translate-y-2);
        setTimeout(() => toast.remove(), 300);
    }, 6000);
}
