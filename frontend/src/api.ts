export interface Recipe {
  id: number
  name: string
  source_url: string
  servings: string | null
  scraped_at: string | null
}

export interface Ingredient {
  id: number
  recipe_id: number
  group_name: string | null
  sort_order: number | null
  name: string
  quantity: string | null
  unit: string | null
  note: string | null
}

export interface Step {
  id: number
  recipe_id: number
  step_number: number
  description: string
}

export interface RecipeDetail extends Recipe {
  ingredients: Ingredient[]
  steps: Step[]
}

const BASE = '/api'

const CREDENTIALS_KEY = 'auth'

export function getCredentials(): string | null {
  return sessionStorage.getItem(CREDENTIALS_KEY)
}

export function saveCredentials(user: string, pass: string): void {
  sessionStorage.setItem(CREDENTIALS_KEY, btoa(`${user}:${pass}`))
}

export function clearCredentials(): void {
  sessionStorage.removeItem(CREDENTIALS_KEY)
}

export class UnauthorizedError extends Error {
  constructor() {
    super('Unauthorized')
    this.name = 'UnauthorizedError'
  }
}

export async function authFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const credentials = getCredentials()
  const headers = new Headers(init.headers)
  if (credentials) {
    headers.set('Authorization', `Basic ${credentials}`)
  }
  const res = await fetch(input, { ...init, headers })
  if (res.status === 401) {
    clearCredentials()
    window.dispatchEvent(new Event('unauthorized'))
    throw new UnauthorizedError()
  }
  return res
}

export async function searchRecipes(q: string): Promise<Recipe[]> {
  const res = await authFetch(`${BASE}/recipes?q=${encodeURIComponent(q)}`)
  return res.json()
}

export async function getRecipe(id: number): Promise<RecipeDetail> {
  const res = await authFetch(`${BASE}/recipes/${id}`)
  if (!res.ok) throw new Error('Not found')
  return res.json()
}

export interface RecipeUpdatePayload {
  name: string
  source_url: string
  servings: number | null
  ingredients: {
    group_name: string | null
    name: string
    quantity: string | null
    unit: string | null
    note: string | null
    sort_order?: number | null
  }[]
  steps: {
    step_number: number
    description: string
  }[]
}

export async function updateRecipe(id: number, data: RecipeUpdatePayload): Promise<RecipeDetail> {
  const res = await authFetch(`${BASE}/recipes/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('更新に失敗しました')
  return res.json()
}

export async function recordRecipeViewed(id: number): Promise<void> {
  await authFetch(`${BASE}/recipes/${id}/viewed`, { method: 'POST' })
}

export async function getRecipesByIds(ids: number[]): Promise<Recipe[]> {
  const results = await Promise.all(ids.map(id => getRecipe(id).catch(() => null)))
  return results.filter((r): r is RecipeDetail => r !== null)
}

export async function getIngredientSuggestions(): Promise<string[]> {
  const res = await authFetch(`${BASE}/ingredients/suggestions`)
  if (!res.ok) return []
  return res.json()
}

export class DuplicateUrlError extends Error {
  constructor() {
    super('このURLのレシピはすでに登録されています')
    this.name = 'DuplicateUrlError'
  }
}

export async function importRecipeFromUrl(url: string): Promise<RecipeDetail> {
  const res = await authFetch(`${BASE}/recipes/from-url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  })
  if (res.status === 409) throw new DuplicateUrlError()
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'レシピの生成に失敗しました' }))
    throw new Error(err.detail ?? 'レシピの生成に失敗しました')
  }
  return res.json()
}
