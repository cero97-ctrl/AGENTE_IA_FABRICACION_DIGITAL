import os
import shutil


def _extract_text_local(pdf_path):
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        text = "\n".join([page.extract_text() for page in reader.pages])
        return text
    except Exception as e:
        print(f"   ⚠️ pypdf local falló: {e}")
        return ""


def _extract_text_sandbox(pdf_path, run_tool):
    basename = os.path.basename(pdf_path)
    sandbox_path = os.path.join(".out", basename)
    shutil.copy(pdf_path, sandbox_path)
    path_in_sandbox = f"/mnt/out/{basename}"

    read_code = (
        f"from pypdf import PdfReader; "
        f"reader = PdfReader('{path_in_sandbox}'); "
        f"print('\\n'.join([page.extract_text() for page in reader.pages]))"
    )
    res = run_tool("run_sandbox.py", ["--code", read_code])
    if res and res.get("status") == "success":
        return res.get("stdout", "")
    return ""


def _extract_text_with_ocr(pdf_path, run_tool):
    basename = os.path.basename(pdf_path)
    sandbox_path = os.path.join(".out", basename)
    shutil.copy(pdf_path, sandbox_path)
    path_in_sandbox = f"/mnt/out/{basename}"

    ocr_code = (
        f"from pdf2image import convert_from_path; "
        f"import pytesseract; "
        f"images = convert_from_path('{path_in_sandbox}', dpi=300); "
        f"for img in images: print(pytesseract.image_to_string(img, lang='spa+eng')); "
        f"print('')"
    )
    res = run_tool("run_sandbox.py", ["--code", ocr_code])
    if res and res.get("status") == "success":
        return res.get("stdout", "")
    return ""


def _is_latex_request(caption):
    return any(w in caption.strip().lower() for w in ["latex", "tex", "convertir", "convert"])


def _build_prompt(text, caption, file_name):
    caption_lower = caption.strip().lower()

    if _is_latex_request(caption):
        return (
            "Convierte el siguiente contenido extraído de un PDF a formato LaTeX. "
            "Respeta la estructura: secciones, párrafos, listas. "
            "Usa ecuaciones matemáticas donde sea apropiado ($...$ o $$...$$).\n\n"
            f"{text[:12000]}"
        ), "🔄 Convirtiendo documento a LaTeX..."

    if any(w in caption_lower for w in ["pregunta", "question", "duda", "consulta"]):
        return (
            f"Responde la siguiente pregunta sobre este documento:\n\n"
            f"Pregunta: {caption}\n\n"
            f"Contenido del documento:\n{text[:12000]}"
        ), f"❓ Analizando documento para responder tu pregunta..."

    if any(w in caption_lower for w in ["resumir", "summary", "resume", "resumen"]):
        return (
            "Resume los puntos clave de este documento técnico de ingeniería. "
            "Destaca: propósito, metodología, resultados, conclusiones.\n\n"
            f"{text[:12000]}"
        ), "🧠 Resumiendo documento..."

    if any(w in caption_lower for w in ["ocr", "escaneado", "scan", "imagen"]):
        return None, "ocr"  # signal for OCR fallback

    if any(w in caption_lower for w in ["raw", "texto", "text", "crudo"]):
        return None, "raw"

    return (
        "Analiza el siguiente contenido extraído de un PDF de ingeniería/fabricación digital "
        "y proporciona un resumen estructurado con los puntos clave:\n\n"
        f"{text[:12000]}"
    ), "🧠 Analizando documento..."


def handle_pdf(file_id, file_name, caption, sender_id, run_tool):
    import time
    local_path = os.path.join(".tmp", file_name)

    run_tool("telegram_tool.py", [
        "--action", "send", "--message",
        f"📂 Recibí `{file_name}`. Extrayendo contenido...",
        "--chat-id", sender_id
    ])
    run_tool("telegram_tool.py", [
        "--action", "download", "--file-id", file_id, "--dest", local_path
    ])

    text = _extract_text_local(local_path)
    if not text or not text.strip():
        text = _extract_text_sandbox(local_path, run_tool)

    is_latex = _is_latex_request(caption)
    prompt, action = _build_prompt(text, caption, file_name)

    if action == "ocr":
        text = _extract_text_with_ocr(local_path, run_tool)
        if not text or not text.strip():
            return "⚠️ No se pudo extraer texto ni con OCR. El PDF puede estar corrupto o ser solo imágenes sin texto legible."
        run_tool("telegram_tool.py", [
            "--action", "send", "--message",
            "🔍 Usando OCR (reconocimiento óptico)...",
            "--chat-id", sender_id
        ])
        prompt, action = _build_prompt(text, caption, file_name)
        if action == "ocr":
            action = "🧠 Analizando documento escaneado..."

    if action == "raw":
        chunk = text[:4000]
        return f"📄 Texto extraído de `{file_name}`:\n\n{chunk}"

    if not text or not text.strip():
        return "⚠️ No se pudo extraer texto del PDF. Prueba con `/ocr` como caption o es un documento escaneado."

    run_tool("telegram_tool.py", [
        "--action", "send", "--message", action, "--chat-id", sender_id
    ])
    llm_res = run_tool("chat_with_llm.py", ["--prompt", prompt])

    if llm_res and "content" in llm_res:
        content = llm_res["content"]

        if is_latex:
            tex_name = file_name.rsplit(".", 1)[0] + ".tex"
            tex_path = os.path.join(".tmp", tex_name)
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(content)
            run_tool("telegram_tool.py", [
                "--action", "send-document", "--file-path", tex_path,
                "--chat-id", sender_id,
                "--caption", f"✅ {tex_name} generado desde {file_name}"
            ])
            return f"✅ Archivo `{tex_name}` generado y enviado."

        return content
    return "❌ Error al generar el análisis con la LLM."


def handle_pdf_from_document(msg, sender_id, run_tool):
    parts = msg.replace("__DOCUMENT__:", "").split("|||")
    file_id = parts[0]
    file_name = parts[1]
    caption = parts[2] if len(parts) > 2 else ""
    return handle_pdf(file_id, file_name, caption, sender_id, run_tool)
