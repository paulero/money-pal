# Seguridad y privacidad

Money Pal maneja información financiera personal. Estas son nuestras reglas:

## Principios

1. **Tus datos se guardan en tu computadora.** Las transacciones, categorías y reportes quedan en `data/` y `output/`. Este proyecto no tiene servidores ni recolecta datos.
2. **Claude procesa tus correos en la nube.** Para leer los avisos, Claude Code envía el contenido de esos correos a la API de Anthropic, igual que cualquier conversación con Claude. Ese tratamiento se rige por los términos y la [política de privacidad de Anthropic](https://www.anthropic.com/legal/privacy) de tu cuenta, no por este proyecto.
3. **Solo lectura.** Money Pal solo necesita leer correos; nunca envía, borra ni modifica mensajes.
4. **Nada real en el repositorio.** Credenciales, tokens, archivos `.json`, `.xlsx`, `.csv` y `.pdf` con transacciones reales están bloqueados por `.gitignore`. Los ejemplos usan datos ficticios.
5. **Mínimo necesario.** De cada transacción se guardan fecha, tipo, comercio, tarjeta (últimos 4 dígitos), moneda y monto. En las **transferencias**, el "comercio" es el nombre de la persona o empresa que recibió el dinero: tu archivo contiene nombres de terceros, trátalo con el mismo cuidado que tu estado de cuenta.

## Protecciones incluidas

- **Rutinas automáticas limitadas.** Las rutinas sin supervisión solo pueden leer Gmail, leer el proyecto y escribir en `data/` y `output/`. Si un correo trae instrucciones escondidas, Claude no puede modificar scripts ni archivos fuera del proyecto.
- **Respaldos.** Antes de cada guardado se copia la versión anterior a `data/respaldos/` (las últimas 10), y el archivo se reemplaza de una sola vez para que un corte no lo deje a medias.
- **Registros con fecha de vencimiento.** `output/logs/` incluye resúmenes de tus gastos y se borra automáticamente a los 90 días.
- **Reportes sin fórmulas externas.** Un texto de un correo que empiece con `=` queda como texto en Excel, nunca como fórmula.

## Recomendado en tu computadora

- Activa el cifrado del disco (**FileVault** en macOS, **BitLocker** en Windows).
- Ten un respaldo aparte (p. ej. **Time Machine**): `data/respaldos/` protege de errores, no de perder la computadora.
- No guardes la carpeta del proyecto en iCloud Drive, Dropbox u otra carpeta sincronizada.

## Antes de contribuir

- Revisa tu `git diff` antes de hacer commit.
- No pegues capturas de correos reales en issues o Pull Requests; usa datos inventados.
- Las contribuciones externas solo pueden cambiar `banks/` y `docs/`; los comandos y scripts los revisa el mantenedor.

## Reportar un problema de seguridad

Si encuentras una vulnerabilidad, **no abras un issue público**. Usa la opción *Report a vulnerability* en la pestaña **Security** de este repositorio.
