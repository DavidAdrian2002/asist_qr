const lista = document.getElementById("lista");

// 🔒 Guardar QR ya escaneados
const escaneados = new Set();

// 💬 Mensaje visual
function mostrarMensaje(texto) {
    let msg = document.getElementById("msg");

    if (!msg) {
        msg = document.createElement("div");
        msg.id = "msg";
        msg.className = "alert alert-warning mt-2 text-center";
        document.body.prepend(msg);
    }

    msg.innerText = texto;

    setTimeout(() => {
        msg.innerText = "";
    }, 1500);
}

async function iniciarScanner() {
    const html5QrCode = new Html5Qrcode("reader");

    html5QrCode.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: 250 },

        async (decodedText) => {

            // 🚫 Evitar múltiples lecturas del mismo QR
            if (escaneados.has(decodedText)) return;

            escaneados.add(decodedText);

            // ⏸ Pausar escaneo
            await html5QrCode.pause();

            fetch("/registrar_tarde", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    qr: decodedText,
                    curso_id: CURSO_ID   // 👈 🔥 CLAVE
                })
            })
            .then(res => res.json())
            .then(data => {

                if (data.success) {

                    const item = document.createElement("li");
                    item.className = "list-group-item list-group-item-warning";
                    item.innerText = data.nombre + " " + data.apellido + " (CR)";
                    lista.appendChild(item);

                    mostrarMensaje("⏱ Registrado como tardanza");

                    // 🔊 sonido
                    new Audio("/static/sounds/beep.mp3").play();

                    // 📳 vibración
                    if (navigator.vibrate) {
                        navigator.vibrate(200);
                    }

                } else {
                    mostrarMensaje("❌ QR inválido o fuera de curso");
                }

            });

            // ▶ Reanudar después de 2 segundos
            setTimeout(() => {
                html5QrCode.resume();
            }, 2000);
        }
    ).catch(err => {
        console.error("Error cámara:", err);
    });
}

iniciarScanner();