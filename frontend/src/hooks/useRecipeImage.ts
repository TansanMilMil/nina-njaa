import { useState } from 'react'
import type { ChangeEvent, Dispatch, SetStateAction } from 'react'
import { toast } from 'sonner'
import { uploadRecipeImage, deleteRecipeImage } from '../api'
import type { RecipeDetail } from '../api'

export function useRecipeImage(
  id: string | undefined,
  setRecipe: Dispatch<SetStateAction<RecipeDetail | null>>
) {
  const [imageUploading, setImageUploading] = useState(false)

  async function handleImageUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file || !id) return
    setImageUploading(true)
    try {
      const result = await uploadRecipeImage(Number(id), file)
      setRecipe(prev => prev ? { ...prev, image_path: `${result.image_path}?t=${Date.now()}` } : prev)
      toast.success('画像をアップロードしました')
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'アップロードに失敗しました'
      toast.error(msg)
    } finally {
      setImageUploading(false)
      e.target.value = ''
    }
  }

  async function handleDeleteImage() {
    if (!id) return
    try {
      await deleteRecipeImage(Number(id))
      setRecipe(prev => prev ? { ...prev, image_path: null } : prev)
      toast.success('画像を削除しました')
    } catch {
      toast.error('削除に失敗しました')
    }
  }

  return { imageUploading, handleImageUpload, handleDeleteImage }
}
