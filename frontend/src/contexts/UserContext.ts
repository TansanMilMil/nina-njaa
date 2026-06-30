import { createContext, useContext } from 'react'

export const UserContext = createContext<string | null>(null)

export function useCurrentUser(): string | null {
  return useContext(UserContext)
}
