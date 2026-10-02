# Seguridad y privacidad

Money Pal maneja información financiera personal. Estas son nuestras reglas:

## Principios

1. **Tus datos se guardan en tu computadora.** Las transacciones, categorías y reportes quedan en `data/` y `output/`. Este proyecto no tiene servidores ni recolecta datos.
2. **Claude procesa tus correos en la nube.** Para leer los avisos, Claude Code envía el contenido de esos correos a la API de Anthropic, igual que cualquier conversación con Claude. Ese tratamiento se rige por los términos y la [política de privacidad de Anthropic](https://www.anthropic.com/legal/privacy) de tu cuenta, no por este proyecto.
3. **Solo lectura.** Money Pal solo necesita leer correos; nunca envía, borra ni modifica mensajes. Ojo: ese límite lo aplica Claude Code en tu computadora. El permiso que le diste a Google para el conector de Gmail es más amplio (ver [Revocar el acceso](#revocar-el-acceso-a-tu-gmail)).
4. **Nada real en el repositorio.** Credenciales, tokens, archivos `.json`, `.xlsx`, `.csv` y `.pdf` con transacciones reales están bloqueados por `.gitignore`. Los ejemplos usan datos ficticios.
5. **Mínimo necesario.** De cada transacción se guardan fecha, tipo, comercio, tarjeta (últimos 4 dígitos), moneda y monto. En las **transferencias**, el "comercio" es el nombre de la persona o empresa que recibió el dinero: tu archivo contiene nombres de terceros, trátalo con el mismo cuidado que tu estado de cuenta.

## Protecciones incluidas

- **Gmail con lista de permitidos.** Antes de cada herramienta de Gmail, [`scripts/gmail_solo_lectura.py`](scripts/gmail_solo_lectura.py) deja pasar solo las de lectura (`search_threads`, `get_message`, `get_thread`). Una herramienta nueva del conector queda bloqueada hasta que alguien la revise. La lista de bloqueados de `.claude/settings.json` queda como segunda capa.
- **Librerías fijas y verificadas.** `requirements.txt` fija cada librería a una versión exacta con su hash: si un archivo descargado no coincide, no se instala. Las acciones de GitHub también van fijadas por commit, y Dependabot propone las actualizaciones como Pull Requests revisados.
- **Patrones de bancos con límite de tiempo.** Las reglas de un banco (`banco.json`) pueden venir de contribuciones. Las pruebas rechazan patrones que puedan volverse lentísimos, y en tu computadora cada búsqueda tiene 1 segundo como máximo: un patrón lento no congela la lectura.
- **Rutinas automáticas limitadas.** Las rutinas sin supervisión solo pueden leer Gmail, leer el proyecto y escribir en `data/` y `output/`. Si un correo trae instrucciones escondidas, Claude no puede modificar scripts ni archivos fuera del proyecto. Esos límites no se amplían con tu configuración personal de Claude Code: las rutinas solo cargan la del proyecto.
- **Avisos falsos fuera.** Cualquiera puede falsificar el remitente de un correo. Money Pal nunca lee el spam, que es donde Gmail manda los avisos falsos de un banco con DMARC `quarantine` o `reject`, y solo marca un banco como verificado si su dominio lo publica. Los correos descartados por spam se muestran para que los revises.
- **Solo tu usuario.** `data/` y `output/` quedan cerradas para otras cuentas de la computadora (permisos 700/600), y cada archivo nuevo se crea igual.
- **Respaldos.** Antes de cada guardado se copia la versión anterior a `data/respaldos/` (las últimas 10), y el archivo se reemplaza de una sola vez para que un corte no lo deje a medias.
- **Registros con fecha de vencimiento.** `output/logs/` incluye resúmenes de tus gastos y se borra automáticamente a los 90 días.
- **Página de revisión solo local.** `scripts/revisar.sh` abre un servidor que solo escucha en `127.0.0.1`. Cada petición necesita un token secreto que cambia cada vez, y se rechaza si viene de otro sitio (Host u Origin ajenos). La página no carga nada de internet y muestra el texto de los correos siempre como texto, nunca como código. Se cierra sola tras 30 minutos sin uso.
- **Reportes sin fórmulas externas.** Un texto de un correo que empiece con `=` queda como texto en Excel, nunca como fórmula.

## Recomendado en tu computadora

- Activa el cifrado del disco (**FileVault** en macOS, **BitLocker** en Windows).
- Ten un respaldo aparte (p. ej. **Time Machine**): `data/respaldos/` protege de errores, no de perder la computadora.
- No guardes la carpeta del proyecto en iCloud Drive, Dropbox u otra carpeta sincronizada.

## Revocar el acceso a tu Gmail

Money Pal lee tu Gmail a través del conector de claude.ai, que guarda un permiso de Google de larga duración. Las rutinas semanales y mensuales lo usan sin que tengas que iniciar sesión cada vez.

**Revócalo si:** pierdes o te roban la computadora, dejas de usar Money Pal, o ves actividad que no reconoces.

1. **Desconecta el conector:** [claude.ai](https://claude.ai) → **Settings → Connectors** → Gmail → **Disconnect**.
2. **Quita el permiso en Google:** [myaccount.google.com/permissions](https://myaccount.google.com/permissions) → busca Claude / Anthropic → **Quitar acceso**.
3. **Quita las rutinas** (si aún tienes la computadora): `scripts/instalar-rutinas.sh --quitar`.

Los pasos 1 y 2 se pueden hacer desde cualquier dispositivo. Después de eso, ninguna sesión de Claude Code (ni la que quedó en una computadora perdida) puede volver a leer tu Gmail. Tus datos de `data/` siguen en la computadora: si la perdiste, el cifrado del disco (FileVault) es lo que los protege.

## Antes de contribuir

- Revisa tu `git diff` antes de hacer commit.
- No pegues capturas de correos reales en issues o Pull Requests; usa datos inventados.
- Las contribuciones externas solo pueden cambiar `banks/` y `docs/`; los comandos y scripts los revisa el mantenedor.

## Reportar un problema de seguridad

Si encuentras una vulnerabilidad, **no abras un issue público**. Usa la opción *Report a vulnerability* en la pestaña **Security** de este repositorio.
