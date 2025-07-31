import streamlit as st
import json
import gzip
import os
from datetime import datetime

# === Función para limpiar datos JSON ===
def clean_json_data(data, remove_nulls, remove_empty_arrays, preserve_structure):
    campos_obligatorios = {
        'numDocumentoIdObligado', 'numFactura', 'usuarios',
        'tipoDocumentoIdentificacion', 'numDocumentoIdentificacion',
        'consecutivo', 'servicios'
    }

    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            cleaned_value = clean_json_data(value, remove_nulls, remove_empty_arrays, preserve_structure)
            should_keep = False

            if preserve_structure and key in campos_obligatorios:
                should_keep = True
            elif cleaned_value is not None:
                if isinstance(cleaned_value, (dict, list)):
                    if cleaned_value:
                        should_keep = True
                else:
                    if cleaned_value != "" and cleaned_value != 0:
                        should_keep = True
                    elif not remove_nulls:
                        should_keep = True

            if should_keep:
                cleaned[key] = cleaned_value

        return cleaned

    elif isinstance(data, list):
        cleaned = []
        for item in data:
            cleaned_item = clean_json_data(item, remove_nulls, remove_empty_arrays, preserve_structure)
            if cleaned_item is not None:
                if isinstance(cleaned_item, (dict, list)):
                    if cleaned_item or not remove_empty_arrays:
                        cleaned.append(cleaned_item)
                else:
                    cleaned.append(cleaned_item)
        return cleaned

    else:
        if data is None or data == "":
            return None if remove_nulls else data
        return data

# === Interfaz Streamlit ===
st.set_page_config(page_title="Optimizador JSON", layout="wide")
st.title("🔧 Optimizador de Archivos JSON - Web")

# Subir archivo JSON
uploaded_file = st.file_uploader("📁 Sube tu archivo JSON", type=["json"])

# Opciones de optimización
st.sidebar.title("⚙️ Opciones")
remove_nulls = st.sidebar.checkbox("✂️ Eliminar campos null/vacíos", value=True)
remove_empty_arrays = st.sidebar.checkbox("🗑️ Eliminar arrays vacíos", value=True)
minify_json = st.sidebar.checkbox("📦 Minificar JSON", value=True)
compress_gzip = st.sidebar.checkbox("🗜️ Comprimir con GZIP (.json.gz)", value=False)
preserve_structure = st.sidebar.checkbox("🛡️ Preservar estructura RIPS", value=True)

if uploaded_file:
    try:
        json_data = json.load(uploaded_file)
        original_size = uploaded_file.size
        st.success(f"📊 Archivo cargado: {uploaded_file.name} ({original_size / 1024:.1f} KB)")

        # Conteo original
        usuarios = len(json_data.get("usuarios", []))
        medicamentos = sum(len(u.get("servicios", {}).get("medicamentos", [])) for u in json_data.get("usuarios", []))
        otros = sum(len(u.get("servicios", {}).get("otrosServicios", [])) for u in json_data.get("usuarios", []))

        st.write("👥 Usuarios:", usuarios)
        st.write("💊 Medicamentos:", medicamentos)
        st.write("🏥 Otros servicios:", otros)

        # Optimizar
        json_optim = clean_json_data(json_data, remove_nulls, remove_empty_arrays, preserve_structure)

        # Recuento post optimización
        usuarios_opt = len(json_optim.get("usuarios", []))
        medicamentos_opt = sum(len(u.get("servicios", {}).get("medicamentos", [])) for u in json_optim.get("usuarios", []))
        otros_opt = sum(len(u.get("servicios", {}).get("otrosServicios", [])) for u in json_optim.get("usuarios", []))

        if (usuarios, medicamentos, otros) != (usuarios_opt, medicamentos_opt, otros_opt):
            st.warning("⚠️ Hubo cambios en los conteos tras la optimización")

        # Guardar resultado
        output_name = uploaded_file.name.replace(".json", "_optimizado.json")
        json_kwargs = {
            'ensure_ascii': False,
            'separators': (',', ':') if minify_json else (',', ': '),
            'indent': None if minify_json else 2
        }

        if compress_gzip:
            output_name += ".gz"
            with gzip.open(output_name, 'wt', encoding='utf-8') as f:
                json.dump(json_optim, f, **json_kwargs)
            with open(output_name, 'rb') as f:
                st.download_button("📥 Descargar .json.gz", f, file_name=output_name)
        else:
            with open(output_name, 'w', encoding='utf-8') as f:
                json.dump(json_optim, f, **json_kwargs)
            with open(output_name, 'rb') as f:
                st.download_button("📥 Descargar JSON Optimizado", f, file_name=output_name)

        optimized_size = os.path.getsize(output_name)
        reduction = original_size - optimized_size
        percent = (reduction / original_size) * 100 if original_size > 0 else 0
        st.info(f"📉 Reducción: {reduction / 1024:.1f} KB ({percent:.1f}%)")

    except Exception as e:
        st.error(f"❌ Error al procesar el JSON: {str(e)}")
