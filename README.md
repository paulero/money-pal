# Money Pal · M.ainy p@l

**Tu asistente de gastos personales, open source y con la privacidad primero.**

Money Pal usa **Claude Code + tu Gmail** para leer las notificaciones de consumo que te envía tu banco (empezamos con **BCP**), ordenarlas en categorías y generar un reporte en **Excel o PDF**. Todo corre en tu propia computadora: tus datos bancarios nunca se suben a este repositorio ni a ningún servidor nuestro.

> ⚠️ Proyecto en construcción. Avanzamos paso a paso; revisa la [hoja de ruta](#hoja-de-ruta).

---

## Empieza aquí

👉 [Guía de instalación: Claude Code + Gmail + BCP](docs/instalacion.md)

Luego, dentro de Claude Code en la carpeta `money-pal`:

| Comando | Qué hace |
|---|---|
| `/leer-bcp 3 meses` | Lee tus correos del BCP y guarda las transacciones en `data/` (solo en tu computadora). |
| `/categorias` | Te propone 5 categorías según tus gastos, las ajustas a tu gusto y categoriza todo. |
| `/categorias revisar` | Categoriza los gastos nuevos y te pregunta solo por comercios desconocidos. |
| `/exportar` | Genera tu reporte en Excel y PDF en `output/` (también `/exportar pdf septiembre`). |

Mira el formato con [datos de ejemplo](examples/), o genera un reporte de prueba sin tus datos:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/exportar.py --ejemplo
```

## ¿Qué hace?

- **Lee tus correos de consumo** del banco desde tu Gmail (solo lectura).
- **Extrae cada transacción**: fecha, comercio, tarjeta, moneda y monto.
- **Te ayuda a definir tus categorías**: 5 recomendadas; puedes agregar, pero más de 7 no se recomienda. Pocas categorías = decisiones más claras.
- **Exporta a Excel o PDF**: resumen por categoría, detalle por mes y gastos recurrentes.
- **Rutina de fin de mes**: compara tus gastos de los últimos **3, 6, 12 y 18 meses**.
- **Sugerencias según tu perfil** (riesgo, edad, metas): ahorrar, salir de deudas, independencia financiera (FI) u otra meta.

## Privacidad y seguridad primero

- Tus credenciales y tokens de Gmail se quedan **solo en tu máquina**.
- El archivo `.gitignore` bloquea credenciales, tokens y archivos de transacciones reales para que nunca se suban por error.
- Los ejemplos del repositorio usan **datos ficticios**.
- Acceso a Gmail en modo **solo lectura**.

Más detalles en [SECURITY.md](SECURITY.md).

## Estructura

```
money-pal/
├── .claude/        # Comandos de Claude Code y reglas de seguridad
├── banks/          # Un folder por banco o institución
│   └── bcp/        # Reglas para leer correos del BCP
├── docs/           # Guías de instalación y uso
├── scripts/        # Exportación a Excel y PDF
└── examples/       # Datos de ejemplo (ficticios)
```

## Hoja de ruta

1. [x] Repositorio, licencia y reglas de privacidad
2. [x] [Guía de instalación: Claude Code + Gmail + BCP](docs/instalacion.md)
3. [x] Lector de correos BCP + definición de categorías (`/leer-bcp`, `/categorias`)
4. [x] Exportación a Excel y PDF (`/exportar`)
5. [ ] Rutina de fin de mes (comparativo 3 / 6 / 12 / 18 meses)
6. [ ] Guía para agregar otros bancos e instituciones
7. [ ] Sugerencias según perfil (riesgo, edad, metas)

## Contribuir

Money Pal es open source para que cualquiera pueda **agregar su banco o institución**. Crea una carpeta en `banks/<tu-banco>/` con las reglas para leer sus correos y abre un Pull Request. Nunca incluyas datos reales en tus contribuciones.

## Aviso

Money Pal es una herramienta educativa y de organización personal. **No es asesoría financiera.** Las sugerencias son referenciales; consulta con un profesional antes de tomar decisiones de inversión.

## Licencia

[MIT](LICENSE)
