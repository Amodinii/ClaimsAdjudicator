import { useState } from "react"
import { ArrowRight, ShieldCheck, User, AlertCircle } from "lucide-react"

interface LoginProps {
  onLogin: (user: any) => void
}

export default function LoginScreen({ onLogin }: LoginProps) {
  const [name, setName] = useState("")
  const [role, setRole] = useState("employee") // Default role
  const [error, setError] = useState("") // New Error State

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    setError("") // Clear previous errors

    if (!name.trim()) return

    // --- SECURITY CHECK ---
    if (role === "admin" && name.trim().toLowerCase() !== "amodini") {
        setError("Access Denied: You are not authorized for the Claims Officer role.")
        return
    }

    const userData = {
      name: name,
      role: role,
      memberId: role === 'admin' ? "ADM-001" : "EMP-" + Math.floor(Math.random() * 10000),
      isLoggedIn: true
    }

    // Save to LocalStorage
    localStorage.setItem("plum_user", JSON.stringify(userData))
    
    // Update App State
    onLogin(userData)
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-md rounded-2xl shadow-xl overflow-hidden border border-gray-100">
        {/* Header */}
        <div className="bg-gradient-to-r from-fuchsia-600 to-purple-600 p-8 text-center text-white">
          <div className="mx-auto bg-white/20 w-16 h-16 rounded-full flex items-center justify-center mb-4 backdrop-blur-sm">
            <ShieldCheck className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold mb-2">Plum Claims Portal</h1>
          <p className="text-fuchsia-100 text-sm">Secure AI Adjudication System</p>
        </div>

        {/* Form */}
        <div className="p-8">
          <form onSubmit={handleLogin} className="space-y-6">
            
            {/* Error Message Banner */}
            {error && (
                <div className="p-3 bg-red-50 border border-red-100 rounded-lg flex items-start gap-2 text-red-700 text-sm animate-in fade-in slide-in-from-top-1">
                    <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                    <p>{error}</p>
                </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
              <div className="relative">
                <User className="absolute left-3 top-3.5 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => {
                      setName(e.target.value)
                      setError("") // Clear error when typing
                  }}
                  className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent transition-all"
                    placeholder="Enter your full name"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Select Role (Persona)</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => {
                      setRole("employee")
                      setError("")
                  }}
                  className={`py-2 px-4 rounded-lg text-sm font-medium border transition-all ${
                    role === "employee"
                      ? "bg-fuchsia-50 border-fuchsia-500 text-fuchsia-700"
                      : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  Employee
                </button>
                <button
                  type="button"
                  onClick={() => setRole("admin")}
                  className={`py-2 px-4 rounded-lg text-sm font-medium border transition-all ${
                    role === "admin"
                      ? "bg-fuchsia-50 border-fuchsia-500 text-fuchsia-700"
                      : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  Claims Officer
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="w-full bg-fuchsia-600 hover:bg-fuchsia-700 text-white py-3.5 rounded-xl font-bold shadow-lg hover:shadow-fuchsia-200 transition-all flex items-center justify-center gap-2"
            >
              Access Dashboard
              <ArrowRight className="w-5 h-5" />
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-xs text-gray-400">
              Protected by Enterprise Grade Security
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}