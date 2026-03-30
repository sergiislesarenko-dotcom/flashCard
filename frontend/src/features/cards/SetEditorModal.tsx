import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { setsApi } from '../../api/sets.api'
import { languagesApi } from '../../api/languages.api'
import { Input } from '../../components/Input'
import { Button } from '../../components/Button'
import type { FlashcardSet } from '../../api/types'

const schema = z.object({
  name: z.string().min(1, 'Name is required').max(255),
  languageId: z.coerce.number().positive('Language is required'),
  description: z.string().max(2000).optional(),
})
type FormValues = z.infer<typeof schema>

interface Props {
  set?: FlashcardSet
  onClose: () => void
}

export function SetEditorModal({ set, onClose }: Props) {
  const queryClient = useQueryClient()

  const { data: languages = [] } = useQuery({
    queryKey: ['languages'],
    queryFn: languagesApi.getAll,
    staleTime: Infinity,
  })

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      set
        ? setsApi.update(set.id, values)
        : setsApi.create(values as Parameters<typeof setsApi.create>[0]),
    onSuccess: () => {
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
    defaultValues: set
      ? { name: set.name, languageId: set.language.id, description: set.description ?? '' }
      : undefined,
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-2xl w-full max-w-md p-6 shadow-xl">
        <h2 className="text-lg font-bold mb-4">{set ? 'Edit Deck' : 'New Deck'}</h2>

        <form onSubmit={handleSubmit((v) => mutation.mutate(v))} className="flex flex-col gap-4">
          <Input label="Deck name" error={errors.name?.message} {...register('name')} />

          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-700">Target language</label>
            <select
              className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              {...register('languageId')}
            >
              <option value="">Select a language...</option>
              {languages.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.flag} {l.name}
                </option>
              ))}
            </select>
            {errors.languageId && (
              <p className="text-xs text-red-600">{errors.languageId.message}</p>
            )}
          </div>

          <Input
            label="Description (optional)"
            error={errors.description?.message}
            {...register('description')}
          />

          <div className="flex gap-3 mt-2">
            <Button type="button" variant="secondary" className="flex-1" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" loading={mutation.isPending} className="flex-1">
              {set ? 'Save' : 'Create'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
