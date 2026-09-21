import { useState } from 'react'
import { toast } from 'sonner'
import { addCookedLog } from '../api'

export function useCookLog(id: string | undefined, onLogged: () => void) {
  const [cookLogging, setCookLogging] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [memo, setMemo] = useState('')

  function openModal() {
    setIsModalOpen(true)
    setMemo('')
  }

  function closeModal() {
    setIsModalOpen(false)
  }

  async function submit() {
    if (!id) return
    setCookLogging(true)
    try {
      await addCookedLog(Number(id), memo)
      toast.success('料理記録を追加しました！')
      setIsModalOpen(false)
      setMemo('')
      onLogged()
    } catch {
      toast.error('記録に失敗しました')
    } finally {
      setCookLogging(false)
    }
  }

  return { cookLogging, isModalOpen, memo, setMemo, openModal, closeModal, submit }
}
