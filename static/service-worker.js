self.addEventListener("install", e => {
    console.log("Service Worker instalado");
});

self.addEventListener("fetch", e => {
    // Podés cachear en el futuro si querés
});