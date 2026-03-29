import { useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

const IconUser = () => (
  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
  </svg>
)
const IconUsers = () => (
  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
  </svg>
)
const IconPhoto = () => (
  <svg className="h-10 w-10 text-zinc-300" fill="none" viewBox="0 0 24 24" strokeWidth="1" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0022.5 18.75V5.25A2.25 2.25 0 0020.25 3H3.75A2.25 2.25 0 001.5 5.25v13.5A2.25 2.25 0 003.75 21z" />
  </svg>
)
const IconCamera = () => (
  <svg className="h-10 w-10 text-zinc-300" fill="none" viewBox="0 0 24 24" strokeWidth="1" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M6.827 6.175A2.31 2.31 0 015.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 00-1.134-.175 2.31 2.31 0 01-1.64-1.055l-.822-1.316a2.192 2.192 0 00-1.736-1.039 48.774 48.774 0 00-5.232 0 2.192 2.192 0 00-1.736 1.039l-.821 1.316z" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 12.75a4.5 4.5 0 11-9 0 4.5 4.5 0 019 0z" />
  </svg>
)
const IconShield = () => (
  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
  </svg>
)

function App() {
  const [vista, setVista] = useState('individual')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [ine, setIne] = useState(null)
  const [selfie, setSelfie] = useState(null)
  const [inePreview, setInePreview] = useState(null)
  const [selfiePreview, setSelfiePreview] = useState(null)
  const [resultados, setResultados] = useState(null)
  const [cargando, setCargando] = useState(false)

  const handleFile = (file, setFile, setPreview) => {
    if (!file) return
    setFile(file)
    const reader = new FileReader()
    reader.onloadend = () => setPreview(reader.result)
    reader.readAsDataURL(file)
  }

  const limpiar = () => {
    setIne(null)
    setSelfie(null)
    setInePreview(null)
    setSelfiePreview(null)
    setResultados(null)
  }

  const procesarImagenes = async (e) => {
    e.preventDefault()
    if (!ine || !selfie) return alert("Sube ambas imagenes por favor.")

    setCargando(true)
    setResultados(null)

    const formData = new FormData()
    formData.append("ine", ine)
    formData.append("selfie", selfie)

    try {
      const respuesta = await fetch(`${API_URL}/api/verificar`, {
        method: "POST",
        body: formData,
      })
      if (!respuesta.ok) {
        const errorData = await respuesta.json()
        setResultados({ error: errorData.detail || "Error del servidor" })
        return
      }
      const datos = await respuesta.json()
      setResultados(datos)
    } catch (error) {
      setResultados({ error: "Error de conexion con el servidor. Verifica que el backend este corriendo." })
    } finally {
      setCargando(false)
    }
  }

  const similitudColor = (sim) => {
    if (sim >= 80) return "text-emerald-600"
    if (sim >= 50) return "text-amber-600"
    return "text-red-600"
  }

  const similitudBarColor = (sim) => {
    if (sim >= 80) return "bg-emerald-500"
    if (sim >= 50) return "bg-amber-500"
    return "bg-red-500"
  }

  const menuItems = [
    { id: 'individual', label: 'Verificacion individual', icon: <IconUser /> },
    { id: 'multiple', label: 'Validacion multiple', icon: <IconUsers /> },
  ]

  return (
    <div className="min-h-screen bg-zinc-50 font-sans antialiased flex">

      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/30 z-20 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-30 w-64 bg-white border-r border-zinc-200 transform transition-transform lg:translate-x-0 lg:static lg:z-auto ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="h-full flex flex-col">
          <div className="px-6 py-6 border-b border-zinc-200">
            <h1 className="text-lg font-extrabold text-zinc-900 tracking-tight">Validador KYC</h1>
            <p className="text-xs text-zinc-400 mt-1">Verificacion de identidad</p>
          </div>

          <nav className="flex-1 px-3 py-4 space-y-1">
            {menuItems.map((item) => (
              <button
                key={item.id}
                onClick={() => { setVista(item.id); setSidebarOpen(false); limpiar() }}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  vista === item.id
                    ? 'bg-zinc-900 text-white'
                    : 'text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900'
                }`}
              >
                {item.icon}
                {item.label}
              </button>
            ))}
          </nav>

          {/* Privacy badge */}
          <div className="px-4 py-3">
            <div className="flex items-center gap-2 px-3 py-2 bg-emerald-50 rounded-lg border border-emerald-100">
              <IconShield />
              <div>
                <p className="text-xs font-semibold text-emerald-700">Modo privacidad</p>
                <p className="text-xs text-emerald-600">OCR y deteccion local</p>
              </div>
            </div>
          </div>

          <div className="px-6 py-4 border-t border-zinc-200">
            <p className="text-xs text-zinc-400">Datos personales procesados localmente</p>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 min-h-screen">
        <div className="lg:hidden flex items-center gap-3 px-4 py-3 border-b border-zinc-200 bg-white">
          <button onClick={() => setSidebarOpen(true)} className="p-1.5 rounded-lg hover:bg-zinc-100">
            <svg className="h-5 w-5 text-zinc-600" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          </button>
          <h2 className="text-sm font-semibold text-zinc-900">
            {menuItems.find(m => m.id === vista)?.label}
          </h2>
        </div>

        <div className="max-w-3xl mx-auto px-6 py-10">
          <div className="mb-8">
            <h2 className="text-2xl font-extrabold text-zinc-900 tracking-tight">
              {vista === 'individual' ? 'Verificacion individual' : 'Validacion multiple'}
            </h2>
            <p className="mt-1 text-sm text-zinc-500">
              {vista === 'individual'
                ? 'Compara una identificacion oficial contra una selfie'
                : 'Proximamente: procesa multiples verificaciones en lote'
              }
            </p>
          </div>

          {vista === 'individual' ? (
            <>
              {/* Card: Upload */}
              <div className="bg-white border border-zinc-200 rounded-2xl overflow-hidden">
                <div className="px-6 py-4 border-b border-zinc-200">
                  <h3 className="text-sm font-semibold text-zinc-900">Imagenes a comparar</h3>
                  <p className="text-xs text-zinc-400 mt-0.5">Sube la identificacion oficial y una selfie reciente</p>
                </div>

                <form onSubmit={procesarImagenes}>
                  <div className="p-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">Identificacion (INE)</p>
                        <label className="group relative flex flex-col items-center justify-center h-56 bg-zinc-50 border-2 border-dashed border-zinc-200 rounded-xl cursor-pointer hover:border-zinc-400 hover:bg-zinc-100/50 transition-all overflow-hidden">
                          {inePreview ? (
                            <img src={inePreview} alt="INE" className="absolute inset-0 w-full h-full object-cover rounded-xl" />
                          ) : (
                            <div className="flex flex-col items-center gap-2">
                              <IconPhoto />
                              <p className="text-sm font-medium text-zinc-400">Arrastra o haz clic</p>
                              <p className="text-xs text-zinc-300">JPG, PNG hasta 10MB</p>
                            </div>
                          )}
                          <input type="file" accept="image/*" onChange={(e) => handleFile(e.target.files[0], setIne, setInePreview)} className="sr-only" />
                        </label>
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">Selfie de la persona</p>
                        <label className="group relative flex flex-col items-center justify-center h-56 bg-zinc-50 border-2 border-dashed border-zinc-200 rounded-xl cursor-pointer hover:border-zinc-400 hover:bg-zinc-100/50 transition-all overflow-hidden">
                          {selfiePreview ? (
                            <img src={selfiePreview} alt="Selfie" className="absolute inset-0 w-full h-full object-cover rounded-xl" />
                          ) : (
                            <div className="flex flex-col items-center gap-2">
                              <IconCamera />
                              <p className="text-sm font-medium text-zinc-400">Arrastra o haz clic</p>
                              <p className="text-xs text-zinc-300">JPG, PNG hasta 10MB</p>
                            </div>
                          )}
                          <input type="file" accept="image/*" onChange={(e) => handleFile(e.target.files[0], setSelfie, setSelfiePreview)} className="sr-only" />
                        </label>
                      </div>
                    </div>
                  </div>

                  <div className="px-6 py-4 bg-zinc-50 border-t border-zinc-200 flex gap-3">
                    <button
                      type="submit"
                      disabled={cargando || !ine || !selfie}
                      className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-semibold transition-colors ${
                        cargando || !ine || !selfie
                          ? 'bg-zinc-200 text-zinc-400 cursor-not-allowed'
                          : 'bg-zinc-900 text-white hover:bg-zinc-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-zinc-900'
                      }`}
                    >
                      {cargando ? (
                        <span className="flex items-center justify-center gap-2">
                          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                          </svg>
                          Procesando...
                        </span>
                      ) : 'Verificar identidad'}
                    </button>
                    {(ine || selfie || resultados) && !cargando && (
                      <button type="button" onClick={limpiar} className="py-2.5 px-5 rounded-lg text-sm font-semibold bg-white border border-zinc-200 text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 transition-colors">
                        Limpiar
                      </button>
                    )}
                  </div>
                </form>
              </div>

              {/* Card: Resultados */}
              {resultados && !resultados.error && (
                <div className="mt-6 bg-white border border-zinc-200 rounded-2xl overflow-hidden">
                  <div className="px-6 py-4 border-b border-zinc-200">
                    <h3 className="text-sm font-semibold text-zinc-900">Resultados de verificacion</h3>
                  </div>

                  <div className="grid grid-cols-2 divide-x divide-zinc-200">
                    <div className="px-6 py-5">
                      <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider">Coincidencia</p>
                      <div className="mt-2 flex items-center gap-2">
                        <span className={`inline-flex h-8 w-8 items-center justify-center rounded-full text-sm ${
                          resultados.misma_persona ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                        }`}>
                          {resultados.misma_persona ? (
                            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                            </svg>
                          ) : (
                            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          )}
                        </span>
                        <p className={`text-xl font-extrabold ${resultados.misma_persona ? 'text-emerald-600' : 'text-red-600'}`}>
                          {resultados.misma_persona ? "Positiva" : "Negativa"}
                        </p>
                      </div>
                    </div>
                    <div className="px-6 py-5">
                      <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider">Similitud</p>
                      <p className={`mt-2 text-3xl font-extrabold ${similitudColor(resultados.similitud)}`}>
                        {resultados.similitud}%
                      </p>
                      <div className="mt-2 w-full bg-zinc-100 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all duration-500 ${similitudBarColor(resultados.similitud)}`}
                          style={{ width: `${resultados.similitud}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Explicacion */}
                  {resultados.explicacion && (
                    <div className={`px-6 py-4 border-t ${
                      resultados.misma_persona ? 'bg-emerald-50 border-emerald-100' : 'bg-amber-50 border-amber-100'
                    }`}>
                      <div className="flex items-start gap-2.5">
                        <svg className={`h-4 w-4 mt-0.5 flex-shrink-0 ${
                          resultados.misma_persona ? 'text-emerald-500' : 'text-amber-500'
                        }`} fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
                        </svg>
                        <p className={`text-sm ${
                          resultados.misma_persona ? 'text-emerald-700' : 'text-amber-700'
                        }`}>
                          {resultados.explicacion}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* OCR */}
                  <div className="border-t border-zinc-200">
                    <div className="px-6 py-3 bg-zinc-50 border-b border-zinc-200">
                      <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Texto extraido (OCR) — procesado localmente</p>
                    </div>
                    <div className="px-6 py-4 bg-zinc-900 overflow-auto max-h-72">
                      <pre className="font-mono text-sm text-zinc-300 whitespace-pre-wrap leading-relaxed">{resultados.texto_extraido}</pre>
                    </div>
                  </div>
                </div>
              )}

              {/* Error */}
              {resultados?.error && (
                <div className="mt-6 bg-white border border-red-200 rounded-2xl p-5">
                  <div className="flex items-start gap-3">
                    <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-red-100 text-red-600 flex-shrink-0">
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                      </svg>
                    </span>
                    <div>
                      <p className="text-sm font-semibold text-red-700">Error en la verificacion</p>
                      <p className="mt-1 text-sm text-red-600">{resultados.error}</p>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="bg-white border border-zinc-200 rounded-2xl p-12 text-center">
              <IconUsers />
              <h3 className="mt-4 text-lg font-semibold text-zinc-900">Validacion multiple</h3>
              <p className="mt-2 text-sm text-zinc-500 max-w-sm mx-auto">
                Proximamente podras subir un lote de imagenes para procesar multiples verificaciones de identidad de forma masiva.
              </p>
              <span className="inline-block mt-4 px-3 py-1 rounded-full bg-zinc-100 text-xs font-medium text-zinc-500">
                En desarrollo
              </span>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default App
