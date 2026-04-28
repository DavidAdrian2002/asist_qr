const lista = document.getElementById("lista");

// Guardar QR ya escaneados
const escaneados = new Set();

// Bloqueo para evitar múltiples lecturas seguidas
let bloqueado = false;

// Contadores
let varones = 0;
let mujeres = 0;

// ================= MENSAJE =================
function mostrarMensaje(texto, tipo = "success") {
    const msg = document.getElementById("msg");

    msg.className = `alert alert-${tipo} text-center fw-bold`;
    msg.innerText = texto;

    setTimeout(() => {
        msg.innerText = "";
        msg.className = "";
    }, 1500);
}

// ================= SCANNER =================
function iniciarScanner() {

    const html5QrCode = new Html5Qrcode("reader");

    html5QrCode.start(
        { facingMode: "environment" }, // 📷 cámara trasera
        {
            fps: 10,
            qrbox: 250
        },

        (decodedText) => {

            // 🚫 evitar múltiples lecturas
            if (bloqueado) return;
            if (escaneados.has(decodedText)) return;

            bloqueado = true;
            escaneados.add(decodedText);

            // 📡 enviar al backend
            fetch("/registrar_asistencia", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    qr: decodedText,
                    curso_id: typeof CURSO_ID !== "undefined" ? CURSO_ID : null
                })
            })
            .then(res => res.json())
            .then(data => {

                console.log("RESPUESTA:", data);

                if (data.success) {

                    // 👨‍🎓 CONTADORES
                    if (data.sexo === "M") {
                        varones++;
                        document.getElementById("varones").innerText = varones;
                    } else {
                        mujeres++;
                        document.getElementById("mujeres").innerText = mujeres;
                    }

                    // 🔊 sonido
                    new Audio("/static/sounds/beep.mp3").play();

                    // 📳 vibración (si el dispositivo lo permite)
                    if (navigator.vibrate) {
                        navigator.vibrate(200);
                    }

                    // 📋 agregar a lista
                    const item = document.createElement("li");
                    item.className = "list-group-item list-group-item-success";
                    item.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <strong>${data.nombre} ${data.apellido}</strong><br>
                                DNI: ${data.dni}
                            </div>
                            <span class="badge bg-success">✔</span>
                        </div>
                    `;

                    lista.appendChild(item);

                    mostrarMensaje("✔ Registrado", "success");
document.body.style.backgroundColor = "#d4edda";

setTimeout(() => {
    document.body.style.backgroundColor = "";
}, 300);

                } else {
                    mostrarMensaje("❌ QR inválido", "danger");
                }

                // 🔓 desbloquear después de 2 segundos
                setTimeout(() => {
                    bloqueado = false;
                }, 2000);

            })
            .catch(err => {
                console.error("ERROR:", err);
                mostrarMensaje("Error de conexión", "danger");
                bloqueado = false;
            });

        }
    )
    .catch(err => {
        console.error("Error cámara:", err);
        mostrarMensaje("No se pudo acceder a la cámara", "danger");
    });
}

// 🚀 iniciar
iniciarScanner();