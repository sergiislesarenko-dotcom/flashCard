import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { cardsApi } from '../../api/cards.api'
import { Input } from '../../components/Input'
import { Button } from '../../components/Button'
import type { Flashcard } from '../../api/types'

const schema = z.object({
  front: z.string().min(1, 'Front side is required').max(500),
  back: z.string().min(1, 'Back side is required').max(500),
})
type FormValues = z.infer<typeof schema>

interface Props {
  setId: number
  card?: Flashcard
  onClose: () => void
}

export function CardEditorModal({ setId, card, onClose }: Props) {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      card
        ? cardsApi.update(card.id, values)
        : cardsApi.create({ setId, ...values }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cards', setId] })
      queryClient.invalidateQueries({ queryKey: ['sets'] })
      onClose()
    },
  })

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: card ? { front: card.front, back: card.back } : undefined,
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-2xl w-full max-w-md p-6 shadow-xl">
        <h2 className="text-lg font-bold mb-4">{card ? 'Edit Card' : 'New Card'}</h2>

        <form onSubmit={handleSubmit((v) => mutation.mutate(v))} className="flex flex-col gap-4">
          <Input
            label="Front (Russian word/phrase)"
            placeholder="e.g. Привет"
            error={errors.front?.message}
            {...register('front')}
          />
          <Input
            label="Back (translation)"
            placeholder="e.g. Hello"
            error={errors.back?.message}
            {...register('back')}
          />

          <div className="flex gap-3 mt-2">
            <Button type="button" variant="secondary" className="flex-1" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" loading={mutation.isPending} className="flex-1">
              {card ? 'Save' : 'Add card'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
