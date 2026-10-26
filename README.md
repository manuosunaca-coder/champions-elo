# champions-elo

Pronósticos de la Champions League con rating Elo para el blog de pronósticos.

- `champions.py`: descarga resultados (API pública de ESPN), calcula el Elo, pronostica los partidos y simula el torneo. Solo librería estándar de Python.
- `data.json`: lo que lee el widget. `history.json`: pronósticos y aciertos. `results.json`: caché de resultados.
- `widget.js`: widget para Blogger (`<div class="uce-app" data-view="all"></div>`).
- GitHub Actions lo ejecuta solo varias veces al día.
