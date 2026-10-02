# Instalación: Claude Code + Gmail + tu banco

Esta guía te deja listo para que Money Pal lea los movimientos de tu banco desde tu Gmail. Toma unos 15 minutos.

## Lo que necesitas

- Una computadora con macOS, Linux o Windows.
- Una cuenta de [Claude](https://claude.ai) con un plan que incluya Claude Code (Pro o Max).
- La cuenta de Gmail donde recibes los avisos de movimientos de tu banco.
- Python 3 (para exportar a Excel/PDF). En macOS, si `python3 --version` no responde, instálalo con `xcode-select --install`.

### Bancos disponibles

| Banco | Estado | Cómo activar sus avisos |
|---|---|---|
| BCP | ✅ verificado | [banks/bcp](../banks/bcp/README.md#activa-las-notificaciones) |

¿Tu banco no está? Puedes agregarlo tú mismo con `/nuevo-banco` (Paso 5), sin programar. Lista completa y estados en [banks/](../banks/README.md).

Puedes usar **varios bancos a la vez**: Money Pal los lee todos y los junta en un solo reporte.

---

## Paso 1 · Activa los avisos de tu banco por correo

Money Pal lee los correos que tu banco envía cada vez que usas tu tarjeta, pagas un servicio o haces una transferencia. Actívalos en la app o banca por internet de tu banco (el README de cada banco, en la tabla de arriba, explica dónde y cómo se ven esos correos).

Money Pal solo puede leer los movimientos que tengan correo. Si activas los avisos hoy, tu historial empieza hoy.

> 💡 No necesitas cambiar cómo usas tu Gmail. Si sueles borrar estos avisos, no pasa nada: Money Pal también lee la papelera, guarda cada transacción en tu computadora y, con la [lectura semanal](rutina.md), los lee antes de que Gmail vacíe la papelera (30 días).

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
2. Busca **Gmail**, haz clic en **Connect** y autoriza con la cuenta donde llegan los avisos de tu banco.
3. Claude Code usa los mismos conectores que tu cuenta de claude.ai. Para comprobarlo, abre `claude` y escribe `/mcp`: debe aparecer Gmail.

## Paso 4 · Descarga Money Pal

```bash
git clone https://github.com/paulero/money-pal.git
cd money-pal
claude
```

Siempre abre Claude Code **dentro de la carpeta `money-pal`**. Así se aplican las reglas de seguridad del proyecto.

Clónalo en tu carpeta de inicio, **no** en iCloud Drive, Dropbox ni en Escritorio o Documentos si los sincronizas con iCloud: Money Pal te avisa si lo está.

### Seguridad: Gmail en solo lectura

Dentro de este proyecto, Claude solo puede **buscar y leer** correos. El archivo [`.claude/settings.json`](../.claude/settings.json) deja pasar únicamente las herramientas de lectura de Gmail (las demás, incluidas las que el conector agregue en el futuro, se bloquean) y además bloquea una por una las que modifican tu correo: enviar, responder, reenviar, borrar, crear borradores, marcar como spam o cambiar etiquetas.

> ⚠️ **Ese límite se aplica en tu computadora, no en Google.** El permiso que le das al conector en el Paso 3 cubre todo lo que el conector sabe hacer (también enviar o borrar). Money Pal se limita a leer, pero si dejas de usarlo o pierdes tu computadora, revoca el acceso: [cómo hacerlo](../SECURITY.md#revocar-el-acceso-a-tu-gmail).

## Paso 5 · Prueba de conexión

Dentro de Claude Code, en la carpeta `money-pal`, escribe (cambia `bcp` por tu banco):

```
Busca en mi Gmail los correos de los remitentes de banks/bcp/banco.json
de los últimos 30 días y muéstrame cuántos hay y una tabla con fecha,
comercio, moneda y monto de los 5 más recientes. No guardes nada.
```

Si ves tu tabla, ¡estás listo! 🎉

**¿Tu banco no está en la lista?** Escribe `/nuevo-banco <banco>` (p. ej. `/nuevo-banco interbank`). Claude revisa tus avisos, arma las reglas de tu banco y las prueba; si quieres, también las comparte con el proyecto (solo reglas y correos inventados, nunca tus datos). Más en [banks/](../banks/README.md#agrega-tu-banco-sin-programar).

## Problemas comunes

| Problema | Solución |
|---|---|
| `/mcp` no muestra Gmail | Revisa que el conector esté activo en claude.ai y que Claude Code use la misma cuenta (`/login`). |
| No encuentra correos | Busca en Gmail `from:` con el remitente de tu banco (está en `banks/<banco>/banco.json`). Si no hay resultados, revisa el Paso 1 o tu carpeta de spam. |
| Aparecen correos de otra cuenta | Desconecta y vuelve a conectar Gmail con la cuenta correcta. |

---

## Paso 6 · Importa tu historial

Una sola vez, en la Terminal dentro de `money-pal`, indicando tu banco (o varios):

```bash
scripts/importar-historial.sh 18 bcp
scripts/importar-historial.sh 18 bcp interbank   # si usas varios
```

Lee Gmail (incluida la papelera) **mes por mes hacia atrás**, hasta 18 meses o hasta donde encuentre avisos de ese banco. Cada mes corre en una sesión nueva de Claude, así funciona igual con 50 o con 1,500 correos. Toma alrededor de un minuto por mes; puedes dejarlo corriendo.

¿Prefieres empezar rápido? En Claude Code: `/leer-correos bcp 3 meses`.

Desde ahí, tus bancos quedan registrados: la lectura semanal, `/leer-correos` y el cierre de mes los leen todos sin que tengas que nombrarlos.

## Paso 7 · Categorías, reporte y rutinas

1. En Claude Code: `/categorias` (define tus categorías) y `/exportar` (tu primer reporte).
2. En la Terminal: `scripts/instalar-rutinas.sh` para la lectura semanal y el cierre de mes automático ([detalles](rutina.md)).
