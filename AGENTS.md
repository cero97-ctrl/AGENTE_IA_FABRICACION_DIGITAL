# AGENTS.md — Guía para asistentes de IA

## Descripción del proyecto

Bot de Telegram orquestado por IA para **fabricación digital**: diseño CAD 3D (FreeCAD), diseño electrónico/PCB (KiCad), generación de G-Code CNC, y más. Usa una arquitectura de **3 capas**: Directivas (YAML) → Orquestación (LLM) → Ejecución (scripts Python deterministas).

## Stack técnico

- **Python 3.10+** con `python-telegram-bot`, `google-generativeai`, `chromadb`, `docker`
- **Contenedor Docker** para FreeCAD y KiCad headless
- **Memoria persistente** vía ChromaDB
- **LLMs**: Groq (primario), Gemini/OpenRouter/Ollama (respaldo)

## Estructura del proyecto

```
.
├── bot.py                        # Entry point del bot de Telegram
├── execution/                    # Capa 3: scripts deterministas (argparse, stdout JSON)
│   ├── bot_manager.py            # Inicialización del bot y handlers
│   ├── listen_telegram.py        # Listener principal de Telegram
│   ├── generate_gcode.py         # G-Code desde imagen
│   ├── generate_gerbers.py       # Gerbers desde PCB
│   ├── generate_freecad_script.py# Modelos 3D FreeCAD
│   ├── build_sandbox.py          # Construir imagen Docker
│   └── ...                       # ~60 scripts de ejecución
├── directives/                   # Capa 1: directivas YAML
│   └── voice_interface.yaml
├── telegram_handlers/            # Handlers de comandos/documentos/fotos/voz
├── data/                         # Datos persistentes
├── .agent/                       # Framework y protocolo del agente
├── .tmp/                         # Archivos temporales (no commitear)
├── .env                          # Variables de entorno (no commitear)
├── requirements.txt              # Dependencias Python
├── Dockerfile.sandbox            # Imagen Docker con FreeCAD + KiCad
├── setup.sh                      # Setup con Conda
└── docs/                         # Documentación
```

## Comandos esenciales

| Comando | Descripción |
|---|---|
| `python bot.py` | Iniciar bot de Telegram |
| `python execution/listen_telegram.py` | Iniciar listener Telegram |
| `python execution/build_sandbox.py` | Construir imagen Docker sandbox |
| `python execution/run_sandbox.py` | Ejecutar comando en sandbox Docker |
| `python execution/run_tests.py` | Ejecutar tests |
| `python execution/check_system_health.py` | Chequeo de salud del sistema |
| `python execution/validate_directives.py` | Validar sintaxis de directivas YAML |
| `python execution/format_code.py` | Formatear código Python (autopep8) |
| `python execution/pre_commit_check.py` | Chequeo pre-commit completo |
| `conda activate pcb_env` | Activar entorno Conda |

## Convenciones de código

1. **Scripts en `execution/`**: Python 3.10+, usan `argparse`, salida stdout en **JSON**, errores explícitos
2. **Directivas en `directives/`**: formato YAML, campos obligatorios: `goal`, `steps`, `required_inputs`
3. **No inventar lógica repetible en el chat** — debe vivir en un script en `execution/`
4. **Sin credenciales en código** — usar `python-dotenv` y `.env`
5. **Tests**: `pytest` (archivos `test_*.py`)
6. **Formato**: autopep8
7. **Archivos temporales** en `.tmp/`, no en la raíz

## Variables de entorno (`.env`)

- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_ALLOWED_USERS`
- `GOOGLE_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`
- `OLLAMA_BASE_URL`, `OLLAMA_MODEL`
- `CONTEXT_SOFT_CAP_MESSAGES` (default: 12)
- `CONTEXT_HARD_CAP_CHARS` (default: 30000)
- `GITHUB_TOKEN`

## Links útiles

- [README](README.md)
- [Guía de contribución](CONTRIBUTING.md)
- [Referencia de comandos](docs/COMMAND_REFERENCE.md)
- [Documentación del framework](.agent/AGENT_FRAMEWORK.md)
- [Instrucciones del agente](.agent/AGENT_INSTRUCTIONS.md)
