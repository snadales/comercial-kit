/* Navarino — interruptor de tema Día / Nocturno.
   Día es el tema por defecto. La preferencia se guarda en localStorage
   ("nv-theme": "dia" | "nocturno" | "auto"); si el almacenamiento no está
   disponible, la página funciona igual en Día.
   El <head> debe aplicar la preferencia antes de pintar (ver base.html). */
(function () {
  "use strict";
  var CLAVE = "nv-theme";
  var raiz = document.documentElement;

  function leer() {
    try { return window.localStorage.getItem(CLAVE); } catch (e) { return null; }
  }
  function guardar(valor) {
    try { window.localStorage.setItem(CLAVE, valor); } catch (e) { /* sin almacenamiento */ }
  }
  function esNocturno() {
    var t = raiz.getAttribute("data-theme");
    if (t === "nocturno") return true;
    if (t === "auto" && window.matchMedia) {
      return window.matchMedia("(prefers-color-scheme: dark)").matches;
    }
    return false;
  }
  function aplicar(valor) {
    if (valor === "nocturno" || valor === "auto") raiz.setAttribute("data-theme", valor);
    else raiz.removeAttribute("data-theme");
  }
  function sincronizar() {
    var nocturno = esNocturno();
    var botones = document.querySelectorAll("[data-nv-theme-toggle]");
    for (var i = 0; i < botones.length; i++) {
      botones[i].setAttribute("aria-pressed", nocturno ? "true" : "false");
    }
  }

  var guardado = leer();
  if (guardado) aplicar(guardado);

  document.addEventListener("click", function (ev) {
    var boton = ev.target.closest && ev.target.closest("[data-nv-theme-toggle]");
    if (!boton) return;
    var siguiente = esNocturno() ? "dia" : "nocturno";
    aplicar(siguiente);
    guardar(siguiente);
    sincronizar();
  });

  if (window.matchMedia) {
    var mq = window.matchMedia("(prefers-color-scheme: dark)");
    if (mq.addEventListener) mq.addEventListener("change", sincronizar);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", sincronizar);
  else sincronizar();
})();
