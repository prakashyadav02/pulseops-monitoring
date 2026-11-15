import { createContext, useContext, useState, type PropsWithChildren } from 'react'
import type { AuthResult, User } from './types'

interface Context {
  user: User | null
  signIn: (auth: AuthResult) => void
  signOut: () => void
  setUser: (user: User) => void
}
const AuthContext = createContext<Context | null>(null)

function savedUser(): User | null {
  try {
    if (!localStorage.getItem('pulseops_token')) return null
    return JSON.parse(localStorage.getItem('pulseops_user') ?? 'null') as User | null
  } catch { return null }
}
export function AuthProvider({ children }: PropsWithChildren) {
  const [user, updateUser] = useState<User | null>(savedUser)
  function setUser(next: User) { localStorage.setItem('pulseops_user', JSON.stringify(next)); updateUser(next) }
  function signIn(auth: AuthResult) { localStorage.setItem('pulseops_token', auth.access_token); setUser(auth.user) }
  function signOut() { localStorage.removeItem('pulseops_token'); localStorage.removeItem('pulseops_user'); updateUser(null) }
  return <AuthContext.Provider value={{ user, signIn, signOut, setUser }}>{children}</AuthContext.Provider>
}
export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('AuthProvider missing')
  return value
}
