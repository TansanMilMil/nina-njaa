export interface Recipe {
  id: number
  name: string
  source_url: string
  servings: string | null
  scraped_at: string | null
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

export async function login(username: string, password: string): Promise<void> {
  const res = await fetch(`${BASE}/auth/login`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (res.status === 401) throw new UnauthorizedError()
  if (!res.ok) throw new Error('ログインに失敗しました')
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

export async function deleteRecipe(id: number): Promise<void> {
  const res = await authFetch(`${BASE}/recipes/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('削除に失敗しました')
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

export async function getRecipeBookmarks(): Promise<number[]> {
  const res = await authFetch(`${BASE}/bookmarks/recipes`)
  if (!res.ok) return []
  return res.json()
}

export async function addRecipeBookmark(id: number): Promise<void> {
  await authFetch(`${BASE}/bookmarks/recipes/${id}`, { method: 'POST' })
}

export async function removeRecipeBookmark(id: number): Promise<void> {
  await authFetch(`${BASE}/bookmarks/recipes/${id}`, { method: 'DELETE' })
}

export async function getIngredientBookmarks(): Promise<string[]> {
  const res = await authFetch(`${BASE}/bookmarks/ingredients`)
  if (!res.ok) return []
  return res.json()
}

export async function addIngredientBookmark(name: string): Promise<void> {
  await authFetch(`${BASE}/bookmarks/ingredients`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
}

export async function removeIngredientBookmark(name: string): Promise<void> {
  await authFetch(`${BASE}/bookmarks/ingredients`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
}
