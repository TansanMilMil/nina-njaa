export interface Recipe {
  id: number
  name: string
  source_url: string
  servings: string | null
  scraped_at: string | null
  image_path?: string | null
  ingredient_names?: string[]
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

export class UnauthorizedError extends Error {
  constructor() {
    super('Unauthorized')
    this.name = 'UnauthorizedError'
  }
}

export async function authFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const res = await fetch(input, { credentials: 'include', ...init })
  if (res.status === 401) {
    window.dispatchEvent(new Event('unauthorized'))
    throw new UnauthorizedError()
  }
  return res
}

function jsonInit(method: string, data: unknown): RequestInit {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }
}

function assertOk(res: Response, message: string): void {
  if (!res.ok) throw new Error(message)
}

async function fetchJsonOr<T>(path: string, fallback: T): Promise<T> {
  const res = await authFetch(`${BASE}${path}`)
  if (!res.ok) return fallback
  return res.json()
}

export async function login(username: string, password: string): Promise<void> {
  const res = await fetch(`${BASE}/auth/login`, {
    credentials: 'include',
    ...jsonInit('POST', { username, password }),
  })
  if (res.status === 401) throw new UnauthorizedError()
  assertOk(res, 'ログインに失敗しました')
}

export async function logout(): Promise<void> {
  await authFetch(`${BASE}/auth/logout`, { method: 'POST' })
}

export async function checkAuth(): Promise<string | null> {
  try {
    const res = await authFetch(`${BASE}/auth/me`)
    if (!res.ok) return null
    const data = await res.json()
    return data.username as string
  } catch (e) {
    if (e instanceof UnauthorizedError) return null
    throw e
  }
}

export async function searchRecipes(q: string): Promise<Recipe[]> {
  const res = await authFetch(`${BASE}/recipes?q=${encodeURIComponent(q)}`)
  return res.json()
}

export async function getRecipe(id: number): Promise<RecipeDetail> {
  const res = await authFetch(`${BASE}/recipes/${id}`)
  assertOk(res, 'Not found')
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
  const res = await authFetch(`${BASE}/recipes/${id}`, jsonInit('PUT', data))
  assertOk(res, '更新に失敗しました')
  return res.json()
}

export async function recordRecipeViewed(id: number): Promise<void> {
  await authFetch(`${BASE}/recipes/${id}/viewed`, { method: 'POST' })
}

export async function deleteRecipe(id: number): Promise<void> {
  const res = await authFetch(`${BASE}/recipes/${id}`, { method: 'DELETE' })
  assertOk(res, '削除に失敗しました')
}

export async function getRecipesByIds(ids: number[]): Promise<Recipe[]> {
  const results = await Promise.all(ids.map(id => getRecipe(id).catch(() => null)))
  return results.filter((r): r is RecipeDetail => r !== null)
}

export async function getIngredientSuggestions(): Promise<string[]> {
  return fetchJsonOr<string[]>('/ingredients/suggestions', [])
}

export async function getRecentViewedRecipes(): Promise<Recipe[]> {
  return fetchJsonOr<Recipe[]>('/history/recipes', [])
}

export async function getRecentViewedIngredients(): Promise<string[]> {
  return fetchJsonOr<string[]>('/history/ingredients', [])
}

export class DuplicateUrlError extends Error {
  constructor() {
    super('このURLのレシピはすでに登録されています')
    this.name = 'DuplicateUrlError'
  }
}

export async function importRecipeFromUrl(url: string): Promise<RecipeDetail> {
  const res = await authFetch(`${BASE}/recipes/from-url`, jsonInit('POST', { url }))
  if (res.status === 409) throw new DuplicateUrlError()
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'レシピの生成に失敗しました' }))
    throw new Error(err.detail ?? 'レシピの生成に失敗しました')
  }
  return res.json()
}

export async function getRecipeBookmarks(): Promise<number[]> {
  return fetchJsonOr<number[]>('/bookmarks/recipes', [])
}

export async function addRecipeBookmark(id: number): Promise<void> {
  await authFetch(`${BASE}/bookmarks/recipes/${id}`, { method: 'POST' })
}

export async function removeRecipeBookmark(id: number): Promise<void> {
  await authFetch(`${BASE}/bookmarks/recipes/${id}`, { method: 'DELETE' })
}

export async function getIngredientBookmarks(): Promise<string[]> {
  return fetchJsonOr<string[]>('/bookmarks/ingredients', [])
}

async function sendIngredientBookmark(method: 'POST' | 'DELETE', name: string): Promise<void> {
  await authFetch(`${BASE}/bookmarks/ingredients`, jsonInit(method, { name }))
}

export async function addIngredientBookmark(name: string): Promise<void> {
  await sendIngredientBookmark('POST', name)
}

export async function removeIngredientBookmark(name: string): Promise<void> {
  await sendIngredientBookmark('DELETE', name)
}

export interface CookedLogEntry {
  recipe_id: number
  recipe_name: string | null
  image_path?: string | null
  count: number
  last_cooked_at: string
}

export async function addCookedLog(recipe_id: number): Promise<void> {
  const res = await authFetch(`${BASE}/cooked-logs/${recipe_id}`, { method: 'POST' })
  assertOk(res, '記録に失敗しました')
}

export async function getCookedLogs(): Promise<CookedLogEntry[]> {
  return fetchJsonOr<CookedLogEntry[]>('/cooked-logs', [])
}

export async function getCookedLogForRecipe(recipe_id: number): Promise<CookedLogEntry | null> {
  const res = await authFetch(`${BASE}/cooked-logs/${recipe_id}`)
  if (!res.ok) return null
  return res.json()
}

export async function uploadRecipeImage(id: number, file: File): Promise<{ image_path: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`/api/recipes/${id}/image`, { method: 'POST', body: form })
  if (res.status === 401) { window.dispatchEvent(new Event('unauthorized')); throw new Error('unauthorized') }
  if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail ?? 'upload failed') }
  return res.json()
}

export async function deleteRecipeImage(id: number): Promise<void> {
  const res = await fetch(`/api/recipes/${id}/image`, { method: 'DELETE' })
  if (res.status === 401) { window.dispatchEvent(new Event('unauthorized')); throw new Error('unauthorized') }
  if (!res.ok) throw new Error('delete failed')
}
