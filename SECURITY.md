# Seguridad y privacidad

Money Pal maneja información financiera personal. Estas son nuestras reglas:

## Principios

1. **Todo corre localmente.** Claude Code se ejecuta en tu computadora y lee tu Gmail con tu propio permiso. Este proyecto no tiene servidores ni recolecta datos.
2. **Solo lectura.** Money Pal solo necesita leer correos; nunca envía, borra ni modifica mensajes.
3. **Nada real en el repositorio.** Credenciales, tokens, archivos `.json`, `.xlsx`, `.csv` y `.pdf` con transacciones reales están bloqueados por `.gitignore`. Los ejemplos usan datos ficticios.
4. **Mínimo necesario.** Solo se extraen fecha, comercio, tarjeta (últimos 4 dígitos), moneda y monto.

## Antes de contribuir

- Revisa tu `git diff` antes de hacer commit.
- No pegues capturas de correos reales en issues o Pull Requests; usa datos inventados.

## Reportar un problema de seguridad

Si encuentras una vulnerabilidad, **no abras un issue público**. Usa la opción *Report a vulnerability* en la pestaña **Security** de este repositorio.
