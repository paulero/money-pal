# Instalación: Claude Code + Gmail + BCP

Esta guía te deja listo para que Money Pal lea tus consumos del BCP desde tu Gmail. Toma unos 15 minutos.

## Lo que necesitas

- Una computadora con macOS, Linux o Windows.
- Una cuenta de [Claude](https://claude.ai) con un plan que incluya Claude Code (Pro o Max).
- La cuenta de Gmail donde recibes las notificaciones del BCP.
- Una tarjeta BCP con notificaciones de consumo por correo.
- Python 3 (para exportar a Excel/PDF). En macOS, si `python3 --version` no responde, instálalo con `xcode-select --install`.

---

## Paso 1 · Activa las notificaciones de consumo del BCP

Money Pal lee los correos que el BCP envía cada vez que usas tu tarjeta. Asegúrate de recibirlos:

1. Abre la app **Banca Móvil BCP** y busca la sección de **notificaciones / alertas**.
2. Activa los avisos de **consumos por correo electrónico** para tus tarjetas.
3. Verifica que lleguen a tu Gmail. Deberían verse así:
   - **Remitente:** `notificaciones@notificacionesbcp.com.pe`
   - **Asunto:** `Realizaste un consumo con tu Tarjeta de Crédito BCP - Servicio de Notificaciones BCP`

> Los correos publicitarios del BCP (por ejemplo, de `bcpcomunica@email.bcp.com.pe`) **no** se usan.

Money Pal solo puede leer los consumos que tengan correo. Si activas las notificaciones hoy, tu historial empieza hoy.

> 💡 No necesitas cambiar cómo usas tu Gmail. Si sueles borrar estas notificaciones, no pasa nada: Money Pal también lee la papelera, guarda cada transacción en tu computadora y, con la [lectura semanal](rutina.md), las lee antes de que Gmail vacíe la papelera (30 días).

## Paso 2 · Instala Claude Code

En la Terminal (macOS/Linux):

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Luego inicia sesión con tu cuenta de Claude:

```bash
claude
```

La primera vez te pedirá iniciar sesión en el navegador. Para Windows y otras opciones, revisa la [documentación oficial](https://code.claude.com/docs/en/setup).

## Paso 3 · Conecta tu Gmail

1. Entra a [claude.ai](https://claude.ai) → **Settings → Connectors**.
2. Busca **Gmail**, haz clic en **Connect** y autoriza con la cuenta donde llegan los correos del BCP.
3. Claude Code usa los mismos conectores que tu cuenta de claude.ai. Para comprobarlo, abre `claude` y escribe `/mcp`: debe aparecer Gmail.

## Paso 4 · Descarga Money Pal

```bash
git clone https://github.com/paulero/money-pal.git
cd money-pal
claude
```

Siempre abre Claude Code **dentro de la carpeta `money-pal`**. Así se aplican las reglas de seguridad del proyecto.

### Seguridad: Gmail en solo lectura

El archivo [`.claude/settings.json`](../.claude/settings.json) **bloquea** todas las acciones que modifican tu Gmail: enviar, responder, reenviar, borrar, crear borradores, marcar como spam o cambiar etiquetas. Dentro de este proyecto, Claude solo puede **buscar y leer** correos.

## Paso 5 · Prueba de conexión

Dentro de Claude Code, en la carpeta `money-pal`, escribe:

```
Busca en mi Gmail los correos de notificaciones@notificacionesbcp.com.pe
de los últimos 30 días y muéstrame cuántos hay y una tabla con fecha,
comercio, moneda y monto de los 5 más recientes. No guardes nada.
```

Si ves tu tabla, ¡estás listo! 🎉

## Problemas comunes

| Problema | Solución |
|---|---|
| `/mcp` no muestra Gmail | Revisa que el conector esté activo en claude.ai y que Claude Code use la misma cuenta (`/login`). |
| No encuentra correos | Busca en Gmail `from:notificacionesbcp.com.pe`. Si no hay resultados, revisa el Paso 1 o tu carpeta de spam. |
| Aparecen correos de otra cuenta | Desconecta y vuelve a conectar Gmail con la cuenta correcta. |

---

## Paso 6 · Importa tu historial

Una sola vez, en la Terminal dentro de `money-pal`:

```bash
scripts/importar-historial.sh 18
```

Lee Gmail (incluida la papelera) **mes por mes hacia atrás**, hasta 18 meses o hasta donde encuentre correos del BCP. Cada mes corre en una sesión nueva de Claude, así funciona igual con 50 o con 1,500 correos. Toma unos minutos por mes; puedes dejarlo corriendo.

¿Prefieres empezar rápido? En Claude Code: `/leer-bcp 3 meses`.

## Paso 7 · Categorías, reporte y rutinas

1. En Claude Code: `/categorias` (define tus categorías) y `/exportar` (tu primer reporte).
2. En la Terminal: `scripts/instalar-rutinas.sh` para la lectura semanal y el cierre de mes automático ([detalles](rutina.md)).
