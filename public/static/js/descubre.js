// Filtros del catálogo (categoría y texto) sin recargar la página.
(() => {
  const botones = document.querySelectorAll("[data-filtro-cat]");
  const texto = document.getElementById("filtroTexto");
  const items = document.querySelectorAll("#listaActividades [data-item]");
  const contador = document.getElementById("contador");
  const vacio = document.getElementById("sinResultados");

  let categoria = document.querySelector("[data-filtro-cat].is-active")?.dataset.filtroCat || "todos";

  function aplicar() {
    const busqueda = texto.value.trim().toLowerCase();
    let visibles = 0;
    items.forEach((item) => {
      const card = item.querySelector(".cv-card");
      const ok =
        (categoria === "todos" || card.dataset.categoria === categoria) &&
        (!busqueda || card.dataset.nombre.includes(busqueda));
      item.classList.toggle("d-none", !ok);
      if (ok) visibles++;
    });
    contador.textContent = visibles;
    vacio.classList.toggle("d-none", visibles > 0);
  }

  botones.forEach((b) =>
    b.addEventListener("click", () => {
      categoria = b.dataset.filtroCat;
      botones.forEach((x) => x.classList.toggle("is-active", x === b));
      const url = new URL(location);
      categoria === "todos" ? url.searchParams.delete("categoria") : url.searchParams.set("categoria", categoria);
      history.replaceState(null, "", url);
      aplicar();
    })
  );
  texto.addEventListener("input", aplicar);
  aplicar();
})();
