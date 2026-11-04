import { Share2 } from 'lucide-react'
import { toast } from 'sonner'
import type { Ingredient } from '../api'
import { buildShoppingListText } from '../lib/ingredients'
import { Button } from '@/components/ui/button'

interface ShareIngredientsButtonProps {
  recipeName: string | null
  ingredients: Ingredient[]
  multiplier: number
}

async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    toast.success('材料をコピーしました')
  } catch {
    toast.error('共有に失敗しました')
  }
}

export default function ShareIngredientsButton({
  recipeName,
  ingredients,
  multiplier,
}: ShareIngredientsButtonProps) {
  const handleShare = async () => {
    const text = buildShoppingListText(recipeName, ingredients, multiplier)
    const data: ShareData = { text }
    if (typeof navigator.share !== 'function' || navigator.canShare?.(data) === false) {
      await copyToClipboard(text)
      return
    }
    try {
      await navigator.share(data)
    } catch (e) {
      // ユーザーが共有シートを閉じた場合は何もしない
      if (e instanceof DOMException && e.name === 'AbortError') return
      await copyToClipboard(text)
    }
  }

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      onClick={handleShare}
      disabled={ingredients.length === 0}
      title="買い物リスト用に材料を共有"
    >
      <Share2 className="h-4 w-4" />
      材料を共有
    </Button>
  )
}
