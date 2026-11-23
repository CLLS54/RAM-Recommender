# RAM-RECOMMENDER (AMD + Intel, DDR3/4/5)

Recomendador de configuración de memoria DRAM **multiplataforma** + **base de datos de fabricantes/dies**.

Compatible con:
- **AMD**: AM4 (DDR4, Zen/Zen+/Zen2/Zen3), AM5 (DDR5, Zen4/Zen5), AM3+ (DDR3, FX/Phenom)
- **Intel**: LGA1150 (DDR3), LGA1151 / LGA1200 (DDR4), LGA1700 (DDR4 **y** DDR5), LGA1851 (DDR5, Core Ultra)
- **macOS**: Apple Silicon y Mac Intel (deteccion; la memoria unificada/soldada no se ajusta)
- **Linux**: deteccion por sysfs + dmidecode (los modulos requieren permisos)
- **Cualquier fabricante**: Samsung, SK hynix, Micron/Crucial, Nanya… y un **respaldo genérico** si el chip no se identifica.

> ⚠️ **Verdad incómoda (por diseño):** los timings de RAM **no se pueden cambiar en caliente desde Windows**. Se fijan en la **BIOS/UEFI** y requieren reinicio. Esta herramienta **recomienda** una configuración de partida; tú la aplicas en la BIOS.

## Timings reales con CPU-Z (v3.3)

SMBIOS **no** publica los timings activos (CL/tRCD/tRP/tRAS). CPU-Z sí. Desde
la 3.3 el programa, si encuentra CPU-Z instalado, lo ejecuta en modo fantasma
(`cpuz.exe -txt=report`) y lee de su informe:

```
Perfil actual : 2926 MT/s  21-21-21-47  tRFC 514  CR 2T   (leido con CPU-Z)

COMPARATIVA CON EL PERFIL APLICADO
  actual : 2926 MT/s  21-21-21-47  tRFC 514  1.20 V
  motor  : 2933 MT/s  16-18-18-36  tRFC 513  1.35 V
```

- La validación es la misma que con ZenTimings: si el informe no corresponde a
  este equipo, se descarta y se explica por qué.
- Funciona con un informe ya guardado (`*.txt`) desde "Abrir CPU-Z o snapshot...".
- CLI: `RAMRecommender-cli.exe timings [--json]`.
- Es **opcional**: sin CPU-Z se muestra el perfil que publica el hardware y se
  avisa de que los timings activos no son legibles. Nunca se inventan.

## Portabilidad: funciona en cualquier equipo (v3.2)

**Nuevo en 3.2:** el "Perfil actual" se calcula del hardware real, no de un
snapshot. Un i7-10700 con DDR4-3200 corriendo a 2933 muestra:

```
Perfil actual : 2933 MT/s (SPD 3200 MT/s) - 16 GB - 2 modulos
  Modulos: SK hynix HMA81GS6DJR8N-XN (8 GB), SK hynix HMA81GS6DJR8N-XN (8 GB)
  Nominal del SPD: 3200 MT/s
  Configurada ahora: 2933 MT/s (corre por debajo del SPD)
  Ajuste: posible en BIOS/UEFI (en equipos OEM la BIOS puede no exponerlo)
```

Lectura por sistema (`src/hwsys.py`): **Windows** WMI/SMBIOS, **macOS**
`system_profiler`, **Linux** sysfs + `dmidecode`. En Apple Silicon se informa
"memoria unificada - no ajustable" y no se recomiendan timings que no existen.
Los timings activos siguen marcados como **no legibles** (SMBIOS no los publica).

El `.exe` es de Windows; en macOS/Linux se ejecuta desde la fuente:
`python3 src/app_gui.py` (requiere Python 3 + tkinter).



La versión anterior **solo era correcta en la máquina donde se diseñó**. En otro
equipo diagnosticaba 48 GB (4 módulos Crucial+HP) aunque tuviera 16 GB, daba la
plataforma por AM4/LGA1700 y proponía 1.35 V de VDIMM y 3800 MT/s. Causas y
arreglos:

| Síntoma | Causa | Arreglo |
|---|---|---|
| Memoria y perfil de **otro equipo** | La GUI cargaba el `ZenTimings_snapshot_*.json` más reciente que encontrara junto al `.exe` sin comprobarlo | `hwmatch.snapshot_check()` compara módulos, GB (±5 %), generación DDR y part numbers con WMI; si no cuadra **se ignora y se explica en "Fuente:"**. `Abrir snapshot…` pide confirmación explícita |
| Plataforma equivocada | `detect_platform` devolvía LGA1700 para cualquier Intel y `am4` por defecto | `hwmatch.platform_from()` deduce por chipset y generación real; si no hay datos usa `generic` (nunca inventa un socket) |
| VDIMM 1.35 V en DDR4 | Valor fijo en la GUI (el XMP del equipo de origen) | Se usa el nominal de la generación (1.2 V DDR4, 1.1 V DDR5) y el motor avisa cuando el 1.35 V es el de la fila XMP |
| 3800 MT/s con tope 2933 | El respaldo del motor elegía la fila **más alta** del die | El tope de plataforma es duro: se recomienda el tope (2933) con los timings de la fila más baja |
| "Enlace 1:1 / FCLK" en Intel | Infinity Fabric solo existe en AMD | En Intel se explica **Gear 1/Gear 2** en lugar de inventar FCLK |
| "sin identificar" con Hynix DJR | La tabla SPD solo cubría 2 part numbers | `recommend.identify_die()` usa el parser de part numbers (Hynix/Micron/Samsung/Nanya) y es el único punto de verdad para GUI y doctor |

**No hace falta ningún programa externo.** El hardware se lee por WMI/SMBIOS
(PowerShell + CIM, incluido en Windows). ZenTimings y CPU-Z son **opcionales**:
su snapshot solo sirve para comparar los timings ya aplicados en la BIOS.

Suites de validación (sin instalar nada):

```powershell
python tests\test_hwmatch.py    # plataforma, VDIMM y rechazo de snapshots ajenos
python tests\run_tests.py       # suite completa del proyecto
```

## Qué hace

1. **Base de datos de dies** (`data/dram_dies.json`): 20 ICs DDR3/DDR4/DDR5 de Samsung, SK hynix, Micron y Nanya (más respaldos genéricos), con timings de referencia por frecuencia, tier, `tRFC` en ns y **voltaje máximo diario seguro**.
2. **Mapa SPD/part-number → die** (`data/spd_map.json`): heurísticas de prefijos (Hynix `HMA…DJR`), tabla de versiones SPD y códigos de marcado de IC.
3. **Motor de recomendación** (`recommend.py`): según plataforma, CPU (generación Zen), die, nº de módulos, rank y objetivo (safe/balanced/latency/bandwidth) calcula:
   - Frecuencia objetivo (respeta el modo **1:1** y el techo de cada generación)
   - Timings primarios `tCL-tRCD-tRP-tRAS`, `tRC`, `tRFC` (ns → clocks)
   - **FCLK** (AM4) / modo UCLK (AM5)
   - Voltajes: `VDIMM/VDD`, `VSOC`, `VDDG IOD/CCD`, `VDDP`, `VPP`
   - Avisos de seguridad (C-die 1.35 V, FCLK≥1900 + WHEA, X3D, 2:1 en DDR5, dual-rank…)

## Ejecutables (sin instalar Python) 🆕

En **`dist\`** hay dos binarios portables (con **icono** propio):

| Archivo | Modo | Para qué |
|---|---|---|
| **`RAMRecommender.exe`** | Ventana (GUI) | Uso normal, doble clic |
| **`RAMRecommender-cli.exe`** | Consola | Scripts / automatización |

**GUI** — elegir plataforma/CPU/memoria, **Detectar desde kit.txt**, **Importar archivo...** (cualquier reporte CPU-Z/HWiNFO/Thaiphoon), **Pegar reporte...**, **Recomendar**, **Guardar preset...** y **Benchmark**.

**Consola** (`RAMRecommender-cli.exe <comando>`):
```powershell
RAMRecommender-cli.exe list
RAMRecommender-cli.exe recommend --platform lga1200 --cpu 10700 --die hynix_8gbit_djr
RAMRecommender-cli.exe recommend --platform am5 --cpu 9800X3D --die hynix_16gbit_a_die_ddr5 --json
RAMRecommender-cli.exe kit --file kit.txt --platform am4 --preset preset.json
RAMRecommender-cli.exe bench --label stock --size 512
RAMRecommender-cli.exe bench --compare
```
El estado del benchmark se guarda en `dist\state\` (junto al .exe).

Para regenerar **ambos** (incluye `data/`, `bench/` y el icono):

```powershell
pwsh -File build_exe.ps1
```

## Uso por consola (con Python)

```powershell
# Ver todos los dies de la base de datos
python recommend.py --list

# Identificar un modulo por su part number
python recommend.py --spd HMA81GS6DJR8N-XN

# Recomendacion AM4 (Ryzen 5800X3D + Hynix DJR)
python recommend.py --platform am4 --cpu 5800X3D --die hynix_8gbit_djr --modules 2 --rank 1 --goal balanced

# Recomendacion AM5 DDR5 (9800X3D + Hynix A-die)
python recommend.py --platform am5 --cpu 9800X3D --die hynix_16gbit_a_die_ddr5 --modules 2 --rank 1

# Intel LGA1200 DDR4 (i7-10700 + Hynix DJR)
python recommend.py --platform lga1200 --cpu 10700 --die hynix_8gbit_djr

# Intel LGA1700 en DDR5 o DDR4
python recommend.py --platform lga1700 --ddr 5 --cpu 14700K --die hynix_16gbit_a_die_ddr5
python recommend.py --platform lga1700 --ddr 4 --cpu 12700K --die samsung_8gbit_b_die

# DDR3 (Haswell / AM3+)
python recommend.py --platform lga1150 --cpu 4790K --die ddr3_hynix_4gbit --goal bandwidth

# Sin saber el die: usa el respaldo generico del tipo de memoria
python recommend.py --platform lga1200 --cpu 10400

# Salida JSON (para integrarla en otra app)
python recommend.py --platform am5 --cpu 9800X3D --die hynix_16gbit_a_die_ddr5 --json
```

Objetivos: `safe` (conservador), `balanced` (3600/6000 CL30), `latency` (máx 1:1 con CL bajo), `bandwidth` (frecuencia alta).

## Leer la RAM REAL del equipo (nuevo en 0.4.0) 🆕

`spd_live.py` consulta WMI/SMBIOS y muestra lo que hay **físicamente instalado**, sin pegar nada a mano:

```powershell
python cli.py detect            # informe completo + recomendación
python cli.py detect --json
python kit_import.py --live --preset state\mio.json
```

Muestra por cada ranura: fabricante, part number, capacidad, tipo real (DDR4/DDR5), formato (DIMM/SODIMM),
frecuencia nominal del SPD **y la frecuencia real a la que corre** (avisa si está por debajo),
voltaje, y el die deducido del part number con su nivel de confianza. También rellena solo
plataforma, CPU y número de módulos.

> **Los timings (tCL/tRCD/tRP/tRAS) no se pueden leer desde Windows.** No es una carencia de esta
> herramienta: SMBIOS no los publica y leerlos exige acceder al bus SMBus del SPD con un driver
> firmado (lo que hacen Thaiphoon Burner o ZenTimings). El programa lo dice explícitamente en vez
> de inventar valores; si los tienes, pásalos con `kit --file`.

En la ventana: botón **"Leer mi RAM (real)"**, que además rellena el formulario y selecciona el die.

## Importar tu kit (texto o ventana)

No necesito acceso a tu PC Ryzen: tú me pasas (o pegas) el **reporte** y la herramienta lo lee sola.

```powershell
# Ventana para PEGAR el reporte, detectar, guardar kit.txt y generar preset
python kit_import.py --gui

# O desde un archivo (busca kit.txt/spd.txt/memoria.txt/report.txt por defecto)
python kit_import.py --file kit.txt --platform am4 --cpu 5800X3D --preset state\mio.json
python kit_import.py                       # usa kit.txt si existe
```

**Formatos reconocidos** (autodetecta, sin importar el orden): reporte de **Thaiphoon Burner**, copia de **ZenTimings**, **HWiNFO**, **CPU-Z**, o "Etiqueta: valor" pegado a mano.

**Qué extrae**: fabricante, part number, die, frecuencia (DDR4-3200 / 1600 MHz / MT/s), timings (`tCL, tRCD, tRP, tRAS, tRC, tRFC, tFAW…`) y voltajes (`VDIMM, VSOC, VDDIO…`). Con eso identifica el die en la base de datos y emite el preset.

## Estructura

```
RAM-RECOMMENDER/
├─ src/
│  ├─ app_gui.py          # aplicación con ventana (origen del .exe GUI)
│  ├─ cli.py              # punto de entrada de consola (origen del .exe CLI)
│  ├─ recommend.py        # motor multi-plataforma (timings + subtimings + preset)
│  ├─ hwmatch.py          # portabilidad: plataforma real, VDIMM nominal, valida snapshots
│  ├─ sync11.py           # escala 1:1 (MCLK:FCLK:UCLK) y Gear en Intel
│  ├─ spd_live.py         # lee la RAM real del equipo (WMI/SMBIOS)
│  ├─ kit_import.py       # importa el SPD/timings desde texto o ventana
│  ├─ bench.py            # wrapper: mide y compara antes/después
│  └─ doctor.py           # diagnóstico del entorno (CLI: doctor)
├─ data/
│  ├─ dram_dies.json      # base de datos de fabricantes/dies
│  └─ spd_map.json        # SPD / part-number -> die
├─ bench/
│  ├─ membench.cs         # benchmark nativo (latencia aleatoria + ancho de banda)
│  └─ membench.exe        # compilado con csc
├─ assets/                # icono de los ejecutables
├─ tests/
│  ├─ run_tests.py        # suite completa del proyecto
│  └─ test_hwmatch.py     # portabilidad: plataforma, VDIMM, snapshots ajenos
├─ tools/                 # utilidades de mantenimiento de datos e iconos
├─ examples/              # reportes de ejemplo (CPU-Z)
├─ dist/                  # binarios recién compilados
├─ RAMRecommender.exe     # ejecutable portable (GUI) - listo para copiar
├─ RAMRecommender-cli.exe # ejecutable portable (consola)
├─ RAMRecommender.spec    # receta de PyInstaller (ambos .exe)
├─ build_exe.ps1          # atajo: python -m PyInstaller RAMRecommender.spec
├─ LEEME.txt              # guía rápida de uso y portabilidad
└─ README.md
```

## Benchmark de memoria (medir antes/después)

```powershell
# medir y guardar (etiquetas ayuda a comparar)
python bench.py --label stock --size 512
python bench.py --label preset --size 512
python bench.py --compare
```

Salida de ejemplo (Intel i7-10700 en HP ProDesk, DDR4-2933):
```
Medicion (working set 512 MB):
  Latencia aleatoria : 63.72 ns  (menos = mejor)
  Copia              : 13.04 GB/s  (mas = mejor)
  Lectura            : 31.30 GB/s  (mas = mejor)
  Escritura          : 13.60 GB/s  (mas = mejor)
  (trafico real de copia: 26.09 GB/s)
```
> Mide **latencia aleatoria** (ns, menos = mejor) y **ancho de banda** de copia/lectura/escritura (GB/s, más = mejor).
> El ancho de banda se mide **multihilo** (varios hilos saturan la RAM; un solo hilo en .NET queda limitado por el bucle).
> Los buffers se **pre-tocan** por completo: sin eso la primera copia paga *page faults* y la cifra sale falsa.
> Copia/escritura dan ~la mitad que lectura porque escriben incurren en *read-for-ownership* (el tráfico real es ×2).
> Hay **varianza natural** entre corridas aunque no cambies nada: corre 3-5 veces y compara medianas.

## Preset para BIOS

```powershell
python recommend.py --platform am4 --cpu 5800X3D --die hynix_8gbit_djr --preset state\preset.json
```
Genera un JSON con frecuencia, timings primarios, subtimings y voltajes, listo para transcribir en la UEFI.

## Alcance y límites (honestos)

- Los valores son **referencias típicas de la comunidad** (MemTestHelper OC guide, Thaiphoon die DB, 1usmus DRAM Calculator, hilos AM5-DDR5). **No** son el comportamiento exacto de tu módulo: el binning y el silicio varían.
- El recomendador **no aplica** nada (ni podría): genera un preset para la BIOS. Sí **interpreta** reportes de SPD/timings vía `kit_import.py` (Thaiphoon / ZenTimings / HWiNFO / CPU-Z).
- **Valida siempre** con MemTest86 / HCI (≥400 %) y vigila errores **WHEA** en tiempo real.

## Roadmap

- [x] **Benchmark propio** de latencia/ancho de banda (medir antes/después).
- [x] **Subtimings** completos para un preset de BIOS.
- [x] **Exportar preset** listo para BIOS (`--preset`).
- [x] Importar el **SPD/timings desde texto** o ventana (`kit_import.py`).
- [x] Soporte **Intel + AMD** y **DDR3/DDR4/DDR5** + respaldo genérico.
- [x] **Ejecutables** portables con icono: GUI (`RAMRecommender.exe`) y consola (`RAMRecommender-cli.exe`).
- [ ] Checklist de stress y umbrales de temperatura.
- [ ] Afinar valores DDR5 con más datos por die.

### Nota sobre el benchmark
Un benchmark de memoria **sí** se puede integrar (y ya está: `bench.py` + `bench/membench.cs`). Mide latencia en ns y ancho de banda en GB/s.
**Pero** recuerda: aunque mida "mejor config", **no puede aplicarla**; el resultado siempre se aplica en BIOS.
