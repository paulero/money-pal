# Money Pal · M.ainy p@l

**Tu asistente de gastos personales, open source y con la privacidad por diseño.**

Money Pal usa **Claude Code + tu Gmail** para leer los avisos de movimientos que te envían **tus bancos** (hoy **BCP**, y cualquiera puede [agregar el suyo](banks/README.md) sin programar), ordenarlos en categorías y generar un reporte en **Excel y PDF**. Todo corre en tu propia computadora: tus datos bancarios nunca se suben a este repositorio ni a ningún servidor nuestro.

> ⚠️ Proyecto en construcción. Avanzamos paso a paso; revisa la [hoja de ruta](#hoja-de-ruta).

---

## Empieza aquí

👉 [Guía de instalación: Claude Code + Gmail + tu banco](docs/instalacion.md)

Importa tu historial una vez con `scripts/importar-historial.sh 18 <banco>` y programa las rutinas con `scripts/instalar-rutinas.sh`. No necesitas cambiar cómo usas tu Gmail.

Luego, dentro de Claude Code en la carpeta `money-pal`:

| Comando | Qué hace |
|---|---|
| `/leer-correos` | Lee tus correos nuevos de tus bancos (también de la papelera) y guarda las transacciones en `data/` (solo en tu computadora). Acepta `2026-05` o `3 meses`. |
| `/categorias` | Te propone 5 categorías según tus gastos, las ajustas a tu gusto y categoriza todo. |
| `/categorias revisar` | Categoriza los gastos nuevos y te pregunta solo por comercios desconocidos. |
| `scripts/revisar.sh` | Abre una página, solo en tu computadora, para revisar, aprobar y cambiar las categorías de tus movimientos. |
| `/exportar` | Genera tu reporte en Excel y PDF en `output/` (también `/exportar pdf septiembre`). |
| `/nuevo-banco interbank` | Agrega tu banco a Money Pal desde tus propios correos, sin programar, y prepara la contribución. |
| `/cierre-de-mes` | Rutina de fin de mes: lee lo nuevo, categoriza y compara el mes con tus promedios de 3, 6, 12 y 18 meses. Se puede [programar cada mes](docs/rutina.md). |

Mira el formato con [datos de ejemplo](examples/), o genera un reporte de prueba sin tus datos:

```bash
python3 -m venv .venv && .venv/bin/pip install --require-hashes -r requirements.txt
.venv/bin/python scripts/exportar.py --ejemplo --cierre
```

## ¿Qué hace?

- **Lee tus correos de consumo** del banco desde tu Gmail (solo lectura).
- **Extrae cada transacción**: fecha, comercio, tarjeta, moneda y monto.
- **Te ayuda a definir tus categorías**: 5 recomendadas; puedes agregar, pero más de 7 no se recomienda. Pocas categorías = decisiones más claras.
- **Exporta a Excel y PDF**: resumen por categoría, detalle por mes y gastos recurrentes.
- **Rutina de fin de mes**: compara tus gastos de los últimos **3, 6, 12 y 18 meses**.
- **Sugerencias según tu perfil** (riesgo, edad, metas): ahorrar, salir de deudas, independencia financiera (FI) u otra meta.

## Privacidad y seguridad primero

- Tus credenciales y tokens de Gmail se quedan **solo en tu máquina**.
- El archivo `.gitignore` bloquea credenciales, tokens y archivos de transacciones reales para que nunca se suban por error.
- Los ejemplos del repositorio usan **datos ficticios**.
- Acceso a Gmail en modo **solo lectura**. Tu Gmail no se modifica: ni etiquetas, ni filtros, ni archivado.

Más detalles en [SECURITY.md](SECURITY.md).

## Estructura

```
money-pal/
├── .claude/        # Comandos de Claude Code y reglas de seguridad
├── banks/          # Un folder por banco: reglas (banco.json) y pruebas
│   └── bcp/        # BCP (verificado); agrega el tuyo con /nuevo-banco
├── docs/           # Guías de instalación y uso
├── scripts/        # Exportación a Excel/PDF, comparativo mensual y rutina automática
└── examples/       # Datos de ejemplo (ficticios)
```

## Hoja de ruta

1. [x] Repositorio, licencia y reglas de privacidad
2. [x] [Guía de instalación: Claude Code + Gmail + tu banco](docs/instalacion.md)
3. [x] Lector de correos (multi-banco) + definición de categorías (`/leer-correos`, `/categorias`)
4. [x] Exportación a Excel y PDF (`/exportar`)
5. [x] [Rutina de fin de mes](docs/rutina.md) (comparativo 3 / 6 / 12 / 18 meses, `/cierre-de-mes`)
6. [x] Agregar otros bancos: [plantilla `banco.json`](banks/README.md), `/nuevo-banco` y pruebas automáticas
7. [ ] Sugerencias según perfil (riesgo, edad, metas)

## Contribuir

Money Pal es open source para que cualquiera pueda **agregar su banco o institución**. Si tienes cuenta en un banco que aún no está, abre Claude Code en `money-pal` y escribe `/nuevo-banco <banco>`: Claude revisa tus correos (solo lectura), escribe las reglas y crea pruebas con correos **inventados**, verifica que no se filtre ningún dato real y prepara el Pull Request. Detalles en [banks/README.md](banks/README.md).

Cada Pull Request pasa pruebas automáticas: valida los bancos, genera el reporte de ejemplo y bloquea cualquier archivo con datos personales.

## Aviso

Money Pal es una herramienta educativa y de organización personal. **No es asesoría financiera.** Las sugerencias son referenciales; consulta con un profesional antes de tomar decisiones de inversión.

## Licencia

[MIT](LICENSE)
