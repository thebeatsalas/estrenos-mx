# Calendario de estrenos de cine en México

Genera automáticamente un archivo `.ics` con los estrenos de cine en México
(usando datos de TMDB) y lo mantiene actualizado cada semana con GitHub Actions.

## Setup (una sola vez)

### 1. Consigue tu API key de TMDB
1. Crea cuenta gratis en https://www.themoviedb.org
2. Ve a tu perfil → Configuración → API
3. Solicita una API key tipo "Developer" (te la dan al instante)
4. Copia el **API Read Access Token** (empieza como un JWT largo, no la "API Key" corta)

### 2. Sube este proyecto a un repositorio de GitHub
1. Crea un repo nuevo en GitHub (puede ser público o privado)
2. Sube todos los archivos de esta carpeta (arrastrar y soltar funciona en la web de GitHub)

### 3. Guarda tu API key como "secret"
1. En el repo: Settings → Secrets and variables → Actions → New repository secret
2. Nombre: `TMDB_API_KEY`
3. Valor: el token que copiaste en el paso 1

### 4. Activa GitHub Pages (para tener la URL pública del .ics)
1. En el repo: Settings → Pages
2. En "Source", selecciona la rama `main` y carpeta `/ (root)`
3. Guarda. GitHub te dará una URL tipo:
   `https://TU_USUARIO.github.io/TU_REPO/estrenos.ics`
   (el archivo aparecerá ahí después de la primera corrida del workflow)

### 5. Corre el workflow por primera vez (manual)
1. En el repo: pestaña "Actions"
2. Selecciona "Actualizar estrenos" → "Run workflow"
3. Esto genera `estrenos.json` y `estrenos.ics` por primera vez y los sube al repo

### 6. Suscríbete en Google Calendar
1. Google Calendar → "Otros calendarios" (+) → "Desde URL"
2. Pega la URL de tu `estrenos.ics` (paso 4)
3. Listo — Google revisa esa URL cada ~12-24h y refleja los cambios solo

## Después de esto

No tienes que hacer nada más. El workflow corre solo cada lunes, actualiza
`estrenos.ics` en el repo, y Google Calendar recoge los cambios automáticamente.

Si quieres forzar una actualización manual en cualquier momento, repite el paso 5.

## Notas

- Cobertura: TMDB no siempre tiene la fecha de México cargada para películas
  chicas o indies. Estrenos comerciales grandes (Marvel, Disney, taquilla)
  casi siempre están.
- Si el script deja de funcionar (ve la pestaña Actions para ver errores),
  lo más probable es que cambió algo en la API de TMDB — no debería pasar
  seguido.
