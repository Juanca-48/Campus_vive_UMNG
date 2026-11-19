// Recorrido inicial de 4 pasos: bienvenida → intereses → grupos → mapa.
(() => {
  const form = document.getElementById("onboarding");
  const pasos = [...form.querySelectorAll(".cv-step")];
  const puntos = [...form.querySelectorAll(".cv-progress__dot")];
  const MAX_RECOMENDADAS = 4;

  const intereses = () =>
    [...form.querySelectorAll("input[name=intereses]:checked")].map((c) => c.value);

  // Muestra hasta 4 grupos de las categorías elegidas (o los más populares si no eligió ninguna).
  function filtrarRecomendadas() {
    const elegidos = intereses();
    let visibles = 0;
    form.querySelectorAll("#recomendadas > [data-categoria]").forEach((col) => {
      const coincide = elegidos.length === 0 || elegidos.includes(col.dataset.categoria);
      const mostrar = coincide && visibles < MAX_RECOMENDADAS;
      col.classList.toggle("d-none", !mostrar);
      if (mostrar) visibles++;
    });
  }

  // En el mapa deja solo los lugares con alguna categoría elegida (todos si no eligió ninguna).
  const pines = [...form.querySelectorAll(".cv-mapa-pin")];
  function filtrarMapa() {
    const elegidos = intereses();
    pines.forEach((pin) => {
      const coincide = elegidos.length === 0 || pin.dataset.categorias.split(" ").some((c) => elegidos.includes(c));
      pin.classList.toggle("d-none", !coincide);
      pin.classList.remove("is-open");
    });
  }
  // Tocar un marcador muestra sus actividades (el hover no existe en pantallas táctiles).
  pines.forEach((pin) =>
    pin.addEventListener("click", () => {
      const abrir = !pin.classList.contains("is-open");
      pines.forEach((p) => p.classList.remove("is-open"));
      pin.classList.toggle("is-open", abrir);
    })
  );

  function irA(indice) {
    if (indice === 2) filtrarRecomendadas();
    if (indice === 3) filtrarMapa();
    pasos.forEach((p, i) => p.classList.toggle("is-active", i === indice));
    puntos.forEach((p, i) => p.classList.toggle("is-active", i === indice));
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const actual = () => pasos.findIndex((p) => p.classList.contains("is-active"));

  // Los enlaces del paso 3 guardan los intereses antes de salir; si no, el
  // acceso a /actividad devuelve al paso 1 porque el recorrido no está completo.
  form.querySelectorAll("[data-step='2'] a[href]").forEach((a) =>
    a.addEventListener("click", (e) => {
      e.preventDefault();
      form.elements.next.value = a.getAttribute("href");
      form.submit();
    })
  );

  form.querySelectorAll("[data-next]").forEach((b) => b.addEventListener("click", () => irA(actual() + 1)));
  puntos.forEach((p) => p.addEventListener("click", () => irA(Number(p.dataset.goto))));
})();
