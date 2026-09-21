import { GripVertical } from 'lucide-react'
import {
  DndContext,
  closestCenter,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import type { DragEndEvent } from '@dnd-kit/core'
import {
  SortableContext,
  verticalListSortingStrategy,
  arrayMove,
  useSortable,
  sortableKeyboardCoordinates,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Button } from '@/components/ui/button'

export interface RecipeStep {
  id: string
  description: string
}

export function createStepId() {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `step-${Date.now()}-${Math.random().toString(36).slice(2)}`
}

interface SortableStepRowProps {
  step: RecipeStep
  index: number
  placeholder?: string
  onChange: (index: number, value: string) => void
  onRemove: (index: number) => void
}

function SortableStepRow({ step, index, placeholder, onChange, onRemove }: SortableStepRowProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: step.id,
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <div ref={setNodeRef} style={style} className="mb-2 flex items-start gap-2 bg-background">
      <button
        type="button"
        {...attributes}
        {...listeners}
        className="mt-1.5 cursor-grab touch-none text-muted-foreground hover:text-foreground active:cursor-grabbing"
        aria-label="ドラッグして並び替え"
      >
        <GripVertical className="h-4 w-4" />
      </button>
      <span className="min-w-6 pt-1.5 text-sm">{index + 1}.</span>
      <textarea
        value={step.description}
        onChange={e => onChange(index, e.target.value)}
        rows={2}
        placeholder={placeholder}
        className="flex w-full flex-1 rounded-md border border-input bg-transparent px-3 py-1.5 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
      />
      <Button type="button" variant="ghost" size="sm" onClick={() => onRemove(index)}>削除</Button>
    </div>
  )
}

interface RecipeStepsEditorProps {
  steps: RecipeStep[]
  onStepsChange: (steps: RecipeStep[]) => void
  stepPlaceholder?: (index: number) => string
}

export default function RecipeStepsEditor({ steps, onStepsChange, stepPlaceholder }: RecipeStepsEditorProps) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  )

  function updateStep(index: number, value: string) {
    const next = [...steps]
    next[index] = { ...next[index], description: value }
    onStepsChange(next)
  }

  function addStep() {
    onStepsChange([...steps, { id: createStepId(), description: '' }])
  }

  function removeStep(index: number) {
    onStepsChange(steps.filter((_, i) => i !== index))
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (!over || active.id === over.id) return
    const oldIndex = steps.findIndex(s => s.id === active.id)
    const newIndex = steps.findIndex(s => s.id === over.id)
    if (oldIndex === -1 || newIndex === -1) return
    onStepsChange(arrayMove(steps, oldIndex, newIndex))
  }

  return (
    <section>
      <h2 className="mb-3 text-lg font-semibold">作り方</h2>
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={steps.map(s => s.id)} strategy={verticalListSortingStrategy}>
          {steps.map((step, i) => (
            <SortableStepRow
              key={step.id}
              step={step}
              index={i}
              placeholder={stepPlaceholder?.(i)}
              onChange={updateStep}
              onRemove={removeStep}
            />
          ))}
        </SortableContext>
      </DndContext>
      <Button type="button" variant="outline" size="sm" onClick={addStep}>+ 手順を追加</Button>
    </section>
  )
}
