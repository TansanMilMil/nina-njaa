import type { Ingredient } from '../api'

const NUMBER_TOKEN_PATTERN = /(\d+\s+\d+\/\d+|\d+\/\d+|\d+(?:\.\d+)?)/g

function parseNumberToken(token: string): number | null {
  const mixed = token.match(/^(\d+)\s+(\d+)\/(\d+)$/)
  if (mixed) {
    const [, whole, num, den] = mixed
    return Number(den) === 0 ? null : Number(whole) + Number(num) / Number(den)
  }
  const fraction = token.match(/^(\d+)\/(\d+)$/)
  if (fraction) {
    const [, num, den] = fraction
    return Number(den) === 0 ? null : Number(num) / Number(den)
  }
  if (/^\d+(?:\.\d+)?$/.test(token)) return Number(token)
  return null
}

function formatScaledNumber(value: number): string {
  return String(Math.round(value * 100) / 100)
}

export function scaleQuantity(quantity: string | null, multiplier: number): string {
  if (!quantity || multiplier === 1) return quantity ?? ''
  return quantity.replace(NUMBER_TOKEN_PATTERN, match => {
    const value = parseNumberToken(match)
    return value === null ? match : formatScaledNumber(value * multiplier)
  })
}

export function groupIngredients(ingredients: Ingredient[]): [string | null, Ingredient[]][] {
  const groups: [string | null, Ingredient[]][] = []
  for (const ing of ingredients) {
    const key = ing.group_name ?? null
    const last = groups[groups.length - 1]
    if (last && last[0] === key) {
      last[1].push(ing)
    } else {
      groups.push([key, [ing]])
    }
  }
  return groups
}
