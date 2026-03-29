// =============================================================================
// App.jsx - Componente principal del Validador KYC
// =============================================================================
// Este es el "cerebro visual" de la aplicacion. Presenta un formulario
// donde el usuario sube dos imagenes (INE y selfie), las envia al backend
// Python para procesamiento con IA, y muestra los resultados.
//
// Flujo:
//   1. Usuario sube foto de INE y selfie
//   2. Se envian al backend via POST (FormData)
//   3. El backend compara rostros (DeepFace) y extrae texto (EasyOCR)
//   4. Se muestran los resultados en pantalla
// =============================================================================

import { useState } from 'react'

// ---------------------------------------------------------------------------
// URL del backend: se toma de la variable de entorno VITE_API_URL
// - En local: http://localhost:8000 (definida en .env o .env.example)
// - En produccion (Railway): https://tu-backend.railway.app
// Vite reemplaza import.meta.env.VITE_* en tiempo de build.
// ---------------------------------------------------------------------------
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

function App() {
  // --- Estado de la aplicacion ---
  const [ine, setIne] = useState(null)           // Archivo de imagen INE seleccionado
  const [selfie, setSelfie] = useState(null)      // Archivo de imagen selfie seleccionado
  const [resultados, setResultados] = useState(null) // Respuesta del backend (o null si no hay)
  const [cargando, setCargando] = useState(false)    // Indica si estamos esperando respuesta del backend

  // ---------------------------------------------------------------------------
  // procesarImagenes: Envia las imagenes al backend y recibe los resultados
  // ---------------------------------------------------------------------------
  const procesarImagenes = async (e) => {
    // Prevenir que el formulario recargue la pagina
    e.preventDefault()

    // Validar que ambas imagenes esten seleccionadas
    if (!ine || !selfie) return alert("Sube ambas imagenes por favor.")

    // Activar estado de carga y limpiar resultados anteriores
    setCargando(true)
    setResultados(null)

    // FormData permite enviar archivos binarios al servidor
    // Es el formato que FastAPI espera para recibir UploadFile
    const formData = new FormData()
    formData.append("ine", ine)       // Campo "ine" que espera el backend
    formData.append("selfie", selfie) // Campo "selfie" que espera el backend

    try {
      // Enviar las imagenes al endpoint /api/verificar del backend
      const respuesta = await fetch(`${API_URL}/api/verificar`, {
        method: "POST",
        body: formData,
        // No ponemos Content-Type: el navegador lo genera automaticamente
        // con el boundary correcto para multipart/form-data
      })

      // Si el servidor respondio con error HTTP (400, 500, etc.)
      if (!respuesta.ok) {
        const errorData = await respuesta.json()
        setResultados({ error: errorData.detail || "Error del servidor" })
        return
      }

      // Parsear la respuesta JSON del backend
      const datos = await respuesta.json()
      setResultados(datos)
    } catch (error) {
      // Error de red: el backend no esta corriendo o no hay conexion
      setResultados({ error: "Error de conexion con el servidor Python. Verifica que el backend este corriendo." })
    } finally {
      // Desactivar el estado de carga sin importar el resultado
      setCargando(false)
    }
  }

  // ---------------------------------------------------------------------------
  // RENDER: Interfaz de usuario con Tailwind CSS
  // ---------------------------------------------------------------------------
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8 font-sans">
      {/* Contenedor principal con sombra y bordes redondeados */}
      <div className="max-w-3xl mx-auto bg-white rounded-xl shadow-md overflow-hidden">

        {/* --- Encabezado azul --- */}
        <div className="bg-blue-600 py-6 px-8">
          <h1 className="text-2xl font-bold text-white text-center">
            Validador KYC Interno
          </h1>
          <p className="text-blue-100 text-center mt-2">
            Verificacion Facial y Extraccion de Polizas
          </p>
        </div>

        {/* --- Cuerpo del formulario --- */}
        <div className="p-8">
          <form onSubmit={procesarImagenes} className="space-y-6">
            {/* Grid de dos columnas para los inputs de archivo */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

              {/* Input: Imagen de la INE/identificacion */}
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  1. Registro (INE)
                </label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setIne(e.target.files[0])}
                  className="text-sm text-gray-500
                    file:mr-4 file:py-2 file:px-4
                    file:rounded-full file:border-0
                    file:text-sm file:font-semibold
                    file:bg-blue-50 file:text-blue-700
                    hover:file:bg-blue-100 cursor-pointer"
                />
              </div>

              {/* Input: Imagen selfie con poliza */}
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  2. Selfie + Poliza
                </label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setSelfie(e.target.files[0])}
                  className="text-sm text-gray-500
                    file:mr-4 file:py-2 file:px-4
                    file:rounded-full file:border-0
                    file:text-sm file:font-semibold
                    file:bg-blue-50 file:text-blue-700
                    hover:file:bg-blue-100 cursor-pointer"
                />
              </div>
            </div>

            {/* Boton de envio: cambia estilo segun estado de carga */}
            <button
              type="submit"
              disabled={cargando}
              className={`w-full flex justify-center py-3 px-4 border border-transparent
                rounded-md shadow-sm text-sm font-medium text-white transition-colors
                ${cargando
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
                }`}
            >
              {cargando ? 'Procesando imagenes con IA...' : 'Verificar Identidad'}
            </button>
          </form>

          {/* --- Seccion de resultados (solo se muestra si hay datos) --- */}
          {resultados && !resultados.error && (
            <div className="mt-8 bg-gray-50 border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 border-b pb-2 mb-4">
                Resultados de Validacion
              </h3>

              {/* Grid con los dos indicadores principales */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                {/* Indicador: Misma persona (verde = si, rojo = no) */}
                <div className="bg-white p-4 rounded shadow-sm border border-gray-100">
                  <p className="text-sm text-gray-500">Misma Persona?</p>
                  <p className={`text-xl font-bold ${resultados.misma_persona ? 'text-green-600' : 'text-red-600'}`}>
                    {resultados.misma_persona ? "SI" : "NO"}
                  </p>
                </div>

                {/* Indicador: Porcentaje de similitud facial */}
                <div className="bg-white p-4 rounded shadow-sm border border-gray-100">
                  <p className="text-sm text-gray-500">Nivel de Similitud</p>
                  <p className="text-xl font-bold text-gray-800">
                    {resultados.similitud}%
                  </p>
                </div>
              </div>

              {/* Bloque de texto extraido via OCR (estilo terminal) */}
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">
                  Texto Extraido (OCR):
                </p>
                <div className="bg-gray-800 text-green-400 p-4 rounded-md overflow-auto max-h-64 font-mono text-sm whitespace-pre-wrap">
                  {resultados.texto_extraido}
                </div>
              </div>
            </div>
          )}

          {/* --- Mensaje de error (barra roja lateral) --- */}
          {resultados?.error && (
            <div className="mt-6 bg-red-50 border-l-4 border-red-400 p-4">
              <p className="text-sm text-red-700">
                <strong>Error:</strong> {resultados.error}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
