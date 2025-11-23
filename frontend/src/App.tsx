import { useState, useEffect } from "react"
import ClaimDashboard from "./components/claim-dashboard"
import LoginScreen from "./components/LoginScreen"
import { LogOut, UserCircle } from "lucide-react"

function App() {
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const savedUser = localStorage.getItem("plum_user")
    if (savedUser) {
      setUser(JSON.parse(savedUser))
    }
    setLoading(false)
  }, [])

  const handleLogout = () => {
    localStorage.removeItem("plum_user")
    setUser(null)
  }

  if (loading) return null 

  if (!user) {
    return <LoginScreen onLogin={setUser} />
  }

  return (
    <div className="min-h-screen bg-gray-50 relative font-sans text-gray-900">
      {/* Navbar / Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          
          {/* Logo Area */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-fuchsia-600 to-purple-700 rounded-lg flex items-center justify-center text-white font-bold shadow-md">
              P
            </div>
            <span className="font-bold text-gray-800 text-lg tracking-tight">Plum Claims</span>
          </div>
          
          {}
          <div className="flex items-center gap-4">
            <div className="hidden md:flex flex-col items-end">
              <p className="text-sm font-semibold text-gray-800 leading-none">{user.name}</p>
              <div className="flex items-center gap-1 mt-1">
                <span className={`w-2 h-2 rounded-full ${user.role === 'admin' ? 'bg-red-500' : 'bg-green-500'}`}></span>
                <p className="text-[10px] font-bold uppercase tracking-wider text-gray-500">
                  {user.role === 'admin' ? 'Claims Officer' : 'Employee'}
                </p>
              </div>
            </div>
            
            <div className="h-8 w-[1px] bg-gray-200 hidden md:block"></div>

            <button 
              onClick={handleLogout}
              className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-full transition-all duration-200"
              title="Logout"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex items-center justify-center p-4 md:p-8 animate-in fade-in duration-500">
        {}
        <ClaimDashboard user={user} />
      </main>
    </div>
  )
}

export default App