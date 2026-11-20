// Comportamientos compartidos por todas las páginas.

// Botón "siguiente" de los carruseles horizontales.
document.querySelectorAll("[data-scroll]").forEach((boton) => {
  const carrusel = document.querySelector(boton.dataset.scroll);
  if (!carrusel) return;
  boton.addEventListener("click", () => {
    const alFinal = carrusel.scrollLeft + carrusel.clientWidth >= carrusel.scrollWidth - 4;
    carrusel.scrollTo({ left: alFinal ? 0 : carrusel.scrollLeft + carrusel.clientWidth * 0.8, behavior: "smooth" });
  });
});

// Los mensajes de confirmación se cierran solos.
document.querySelectorAll(".cv-flashes .alert-success, .cv-flashes .alert-info").forEach((alerta) => {
  setTimeout(() => bootstrap.Alert.getOrCreateInstance(alerta).close(), 5000);
});
