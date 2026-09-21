import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { deleteRecipe } from '../api'
import type { RecipeDetail } from '../api'
import BookmarkButton from '../components/BookmarkButton'
import CookLogModal from '../components/CookLogModal'
import ImageLightbox from '../components/ImageLightbox'
import RecipeEditForm from '../components/RecipeEditForm'
import RecipeIngredientsSection from '../components/RecipeIngredientsSection'
import { RecipePageSkeleton } from '../components/Skeleton'
import { useBookmarks } from '../hooks/useBookmarks'
import { useCookLog } from '../hooks/useCookLog'
import { useIngredientBookmarks } from '../hooks/useIngredientBookmarks'
import { useRecipeDetail } from '../hooks/useRecipeDetail'
import { useRecipeImage } from '../hooks/useRecipeImage'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'
import { useCurrentUser } from '../contexts/UserContext'

export default function RecipePage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const currentUsername = useCurrentUser()
  const { recipe, setRecipe, error, cookedLog, refreshCookedLog } = useRecipeDetail(id)
  const { imageUploading, handleImageUpload, handleDeleteImage } = useRecipeImage(id, setRecipe)
  const cookLog = useCookLog(id, refreshCookedLog)
  const [isEditing, setIsEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [isImageLightboxOpen, setIsImageLightboxOpen] = useState(false)
  const [multiplier, setMultiplier] = useState(1)
  const [multiplierInput, setMultiplierInput] = useState('1')
  const { isBookmarked, toggle } = useBookmarks()
  const { isIngredientBookmarked, toggleIngredient } = useIngredientBookmarks()

  useEffect(() => {
    if (!id) return
    setIsEditing(false)
    setMultiplier(1)
    setMultiplierInput('1')
  }, [id, currentUsername])

  async function handleDelete() {
    if (!id || !window.confirm(`「${recipe?.name}」を削除しますか？`)) return
    setDeleting(true)
    try {
      const name = recipe?.name
      await deleteRecipe(Number(id))
      toast.success(`「${name}」を削除しました`)
      navigate('/')
    } catch {
      toast.error('削除に失敗しました')
      setDeleting(false)
    }
  }

  function handleSaved(updated: RecipeDetail) {
    setRecipe({ ...updated, image_path: recipe?.image_path ?? null })
    setIsEditing(false)
  }

  function handleMultiplierInputChange(value: string) {
    setMultiplierInput(value)
    const parsed = Number(value)
    if (value.trim() !== '' && Number.isFinite(parsed) && parsed > 0) {
      setMultiplier(parsed)
    }
  }

  function applyMultiplierPreset(value: number) {
    setMultiplier(value)
    setMultiplierInput(String(value))
  }

  if (error) return <p className="text-muted-foreground">レシピが見つかりませんでした</p>
  if (!recipe) return <RecipePageSkeleton />

  const canEdit = currentUsername !== null && (recipe.username == null || recipe.username === currentUsername)

  if (isEditing && id) {
    return (
      <RecipeEditForm
        recipe={recipe}
        recipeId={id}
        imageUploading={imageUploading}
        deleting={deleting}
        onImageUpload={handleImageUpload}
        onDeleteImage={handleDeleteImage}
        onSaved={handleSaved}
        onCancel={() => setIsEditing(false)}
        onDelete={handleDelete}
      />
    )
  }

  return (
    <article className="flex flex-col gap-5">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start">
        {recipe.image_path && (
          <button
            type="button"
            onClick={() => setIsImageLightboxOpen(true)}
            className="block w-full cursor-zoom-in lg:w-72 lg:flex-shrink-0"
            aria-label="画像を拡大表示"
          >
            <img
              src={`/uploads/${recipe.image_path}`}
              alt={recipe.name ?? ''}
              className="w-full rounded-lg object-cover max-h-64 lg:h-72 lg:max-h-none"
            />
          </button>
        )}

        <div className="flex flex-col gap-5 lg:flex-1">
          <div className="flex items-center gap-4">
            <h1 className="flex-1 text-2xl font-bold">{recipe.name}</h1>
            {canEdit && <Button variant="outline" size="sm" onClick={() => setIsEditing(true)}>編集</Button>}
          </div>

          {currentUsername && (
            <div className="flex flex-col gap-3">
              <div className="flex flex-wrap items-center gap-3">
                <BookmarkButton
                  isBookmarked={isBookmarked(recipe.id)}
                  onToggle={() => toggle(recipe.id)}
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={cookLog.openModal}
                  disabled={cookLog.cookLogging}
                >
                  {cookLog.cookLogging ? '記録中...' : '作った！'}
                </Button>
                {cookedLog && (
                  <Link
                    to={`/cooked-logs/${recipe.id}`}
                    className="text-sm text-muted-foreground hover:text-foreground hover:underline underline-offset-4"
                  >
                    {cookedLog.count}回作った・最終:{' '}
                    {new Date(cookedLog.last_cooked_at).toLocaleDateString('ja-JP')}
                  </Link>
                )}
              </div>
              {cookedLog?.latest_memo && (
                <div className="rounded-md border bg-muted/50 px-3 py-2 text-sm text-muted-foreground whitespace-pre-wrap">
                  <span className="mb-1 block text-xs font-semibold">直近のメモ:</span>
                  {cookedLog.latest_memo}
                </div>
              )}
            </div>
          )}

          {cookLog.isModalOpen && (
            <CookLogModal
              memo={cookLog.memo}
              submitting={cookLog.cookLogging}
              onMemoChange={cookLog.setMemo}
              onSubmit={cookLog.submit}
              onClose={cookLog.closeModal}
            />
          )}

          <p>
            <a
              href={recipe.source_url}
              className="text-primary underline-offset-4 hover:underline"
            >
              元レシピを見る
            </a>
          </p>
        </div>
      </div>

      {recipe.servings && <p className="text-sm">人数：{recipe.servings}</p>}

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <RecipeIngredientsSection
          ingredients={recipe.ingredients}
          multiplier={multiplier}
          multiplierInput={multiplierInput}
          isIngredientBookmarked={isIngredientBookmarked}
          onToggleIngredient={toggleIngredient}
          onMultiplierInputChange={handleMultiplierInputChange}
          onMultiplierPreset={applyMultiplierPreset}
        />

        <section>
          <h2 className="mb-3 text-lg font-semibold">作り方</h2>
          <ol className="flex list-decimal flex-col gap-2 pl-5 text-sm">
            {recipe.steps.map(step => (
              <li key={step.id}>{step.description}</li>
            ))}
          </ol>
        </section>
      </div>

      {isImageLightboxOpen && recipe.image_path && (
        <ImageLightbox
          src={`/uploads/${recipe.image_path}`}
          alt={recipe.name ?? ''}
          onClose={() => setIsImageLightboxOpen(false)}
        />
      )}
    </article>
  )
}
