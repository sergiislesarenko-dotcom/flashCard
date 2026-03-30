# Skills — FlashLang Implementation Patterns

Reference this file before writing new code. These patterns are established and must be followed.

---

## NestJS Module File Layout
Every domain follows identical internal structure:
```
src/<domain>/
  <domain>.module.ts
  <domain>.controller.ts
  <domain>.service.ts
  <domain>.repository.ts
  entities/
    <domain>.entity.ts
  dto/
    create-<domain>.dto.ts
    update-<domain>.dto.ts
    <domain>-response.dto.ts
```

---

## Controller Pattern
Controllers only: validate DTO, call service, return typed response. Zero business logic.

```typescript
@Controller('cards')
@UseGuards(JwtAuthGuard)
export class CardsController {
  constructor(private readonly cardsService: CardsService) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  async create(
    @Body() dto: CreateCardDto,
    @CurrentUser() user: JwtPayload,
  ): Promise<CardResponseDto> {
    return this.cardsService.create(user.userId, dto)
  }

  @Get(':id')
  async findOne(
    @Param('id', ParseIntPipe) id: number,
    @CurrentUser() user: JwtPayload,
  ): Promise<CardResponseDto> {
    return this.cardsService.findOneOrFail(user.userId, id)
  }
}
```

---

## Service Pattern
All business logic here. Throws NestJS HTTP exceptions. Never returns raw entities.

```typescript
@Injectable()
export class CardsService {
  constructor(
    private readonly cardsRepository: CardsRepository,
    private readonly setsRepository: FlashcardSetsRepository,
  ) {}

  async create(userId: number, dto: CreateCardDto): Promise<CardResponseDto> {
    const set = await this.setsRepository.findByIdAndUser(dto.setId, userId)
    if (!set) throw new NotFoundException('Set not found')
    const card = await this.cardsRepository.create({ ...dto, userId })
    return CardResponseDto.fromEntity(card)
  }

  async findOneOrFail(userId: number, cardId: number): Promise<CardResponseDto> {
    const card = await this.cardsRepository.findById(cardId)
    if (!card) throw new NotFoundException('Card not found')
    if (card.set.userId !== userId) throw new ForbiddenException()
    return CardResponseDto.fromEntity(card)
  }
}
```

---

## Repository Pattern
TypeORM custom repository. All queries here. No business logic or HTTP exceptions.

```typescript
@Injectable()
export class CardsRepository {
  constructor(
    @InjectRepository(CardEntity)
    private readonly repo: Repository<CardEntity>,
  ) {}

  findById(id: number): Promise<CardEntity | null> {
    return this.repo.findOne({ where: { id }, relations: ['set'] })
  }

  findDueCards(setId: number, limit: number): Promise<CardEntity[]> {
    return this.repo
      .createQueryBuilder('card')
      .where('card.setId = :setId', { setId })
      .andWhere('card.nextReviewAt <= NOW()')
      .orderBy('card.nextReviewAt', 'ASC')
      .limit(limit)
      .getMany()
  }

  async create(data: Partial<CardEntity>): Promise<CardEntity> {
    const card = this.repo.create(data)
    return this.repo.save(card)
  }
}
```

---

## DTO + class-validator Pattern
Input DTOs validate with decorators. Response DTOs have a static `fromEntity` factory.

```typescript
// create-card.dto.ts
export class CreateCardDto {
  @IsInt() @IsPositive()
  setId: number

  @IsString() @MinLength(1) @MaxLength(500)
  front: string

  @IsString() @MinLength(1) @MaxLength(500)
  back: string
}

// card-response.dto.ts
export class CardResponseDto {
  id: number
  front: string
  back: string
  setId: number
  nextReviewAt: Date | null
  easeFactor: number

  static fromEntity(e: CardEntity): CardResponseDto {
    return {
      id: e.id,
      front: e.front,
      back: e.back,
      setId: e.setId,
      nextReviewAt: e.nextReviewAt,
      easeFactor: Number(e.easeFactor),
    }
  }
}
```

---

## TypeORM Entity Pattern
Use `@Column({ name: 'snake_case' })` to map camelCase properties to snake_case columns.

```typescript
@Entity('flashcards')
export class CardEntity {
  @PrimaryGeneratedColumn('increment')
  id: number

  @Column({ length: 500 })
  front: string

  @Column({ length: 500 })
  back: string

  @ManyToOne(() => FlashcardSetEntity, (set) => set.cards, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'set_id' })
  set: FlashcardSetEntity

  @Column({ name: 'set_id' })
  setId: number

  @Column({ type: 'decimal', precision: 4, scale: 2, default: 2.5, name: 'ease_factor' })
  easeFactor: number

  @Column({ default: 1, name: 'interval_days' })
  intervalDays: number

  @Column({ default: 0 })
  repetitions: number

  @Column({ type: 'timestamp', nullable: true, name: 'next_review_at',
            default: () => 'CURRENT_TIMESTAMP' })
  nextReviewAt: Date | null

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date
}
```

---

## Auth Decorators Pattern

```typescript
// decorators/public.decorator.ts — marks a route as bypassing JwtAuthGuard
export const IS_PUBLIC_KEY = 'isPublic'
export const Public = () => SetMetadata(IS_PUBLIC_KEY, true)

// decorators/current-user.decorator.ts — extracts JWT payload from request
export interface JwtPayload { userId: number; email: string }
export const CurrentUser = createParamDecorator(
  (_: unknown, ctx: ExecutionContext): JwtPayload => {
    return ctx.switchToHttp().getRequest().user
  },
)

// guards/jwt-auth.guard.ts — global guard; bypasses @Public() routes
@Injectable()
export class JwtAuthGuard extends AuthGuard('jwt') {
  constructor(private reflector: Reflector) { super() }
  canActivate(context: ExecutionContext) {
    const isPublic = this.reflector.getAllAndOverride<boolean>(IS_PUBLIC_KEY, [
      context.getHandler(), context.getClass(),
    ])
    if (isPublic) return true
    return super.canActivate(context)
  }
}
```

---

## SM-2 Spaced Repetition Service Pattern

```typescript
// learning/spaced-repetition.service.ts
export interface SRCard {
  easeFactor: number   // starts at 2.5
  intervalDays: number // starts at 1
  repetitions: number  // starts at 0
}
export interface SRResult {
  easeFactor: number
  intervalDays: number
  repetitions: number
  nextReviewAt: Date
}

@Injectable()
export class SpacedRepetitionService {
  calculateNext(card: SRCard, result: 'remembered' | 'repeat'): SRResult {
    let { easeFactor, intervalDays, repetitions } = card
    if (result === 'remembered') {
      if (repetitions === 0) intervalDays = 1
      else if (repetitions === 1) intervalDays = 6
      else intervalDays = Math.round(intervalDays * easeFactor)
      easeFactor = Math.min(2.5, easeFactor + 0.1)
      repetitions += 1
    } else {
      intervalDays = 1
      easeFactor = Math.max(1.3, easeFactor - 0.2)
      repetitions = 0
    }
    const nextReviewAt = new Date()
    nextReviewAt.setDate(nextReviewAt.getDate() + intervalDays)
    return { easeFactor, intervalDays, repetitions, nextReviewAt }
  }
}
```

---

## React Query Hook Pattern
One file per API resource. Never call `fetch` directly from components.

```typescript
// features/cards/hooks/useCards.ts
export function useCards(setId: number) {
  return useQuery({
    queryKey: ['cards', setId],
    queryFn: () => cardsApi.getBySet(setId),
    staleTime: 5 * 60 * 1000,
    enabled: !!setId,
  })
}

export function useCreateCard() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: cardsApi.create,
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ['cards', vars.setId] })
      queryClient.invalidateQueries({ queryKey: ['sets'] })
    },
  })
}
```

---

## Zustand Store Pattern
One store per feature for UI-only state. Server state goes to React Query.

```typescript
// store/session.store.ts
interface SessionState {
  sessionId: number | null
  cards: SessionCard[]
  currentIndex: number
  results: Record<number, 'remembered' | 'repeat'>
  actions: {
    setSession: (id: number, cards: SessionCard[]) => void
    recordResult: (cardId: number, result: 'remembered' | 'repeat') => void
    advance: () => void
    reset: () => void
  }
}

export const useSessionStore = create<SessionState>()((set) => ({
  sessionId: null,
  cards: [],
  currentIndex: 0,
  results: {},
  actions: {
    setSession: (id, cards) => set({ sessionId: id, cards, currentIndex: 0, results: {} }),
    recordResult: (cardId, result) =>
      set((s) => ({ results: { ...s.results, [cardId]: result } })),
    advance: () => set((s) => ({ currentIndex: s.currentIndex + 1 })),
    reset: () => set({ sessionId: null, cards: [], currentIndex: 0, results: {} }),
  },
}))
```

---

## React Hook Form + Zod Pattern

```typescript
// features/auth/LoginPage.tsx (form section)
const schema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(1, 'Required'),
})
type FormValues = z.infer<typeof schema>

export function LoginPage() {
  const { register, handleSubmit, formState: { errors, isSubmitting }, setError } = useForm<FormValues>({
    resolver: zodResolver(schema),
  })
  const onSubmit = async (data: FormValues) => {
    try {
      const res = await authApi.login(data)
      authStore.setAuth(res.user, res.accessToken)
      navigate('/sets')
    } catch (e) {
      if (isApiError(e, 401)) setError('root', { message: 'Invalid email or password' })
    }
  }
  // ...
}
```

---

## FlashCard CSS 3D Flip Pattern
Pure CSS — no animation library required.

```tsx
// features/learning/components/FlashCard.tsx
interface FlashCardProps {
  front: string
  back: string
  isFlipped: boolean
  onFlip: () => void
}

export function FlashCard({ front, back, isFlipped, onFlip }: FlashCardProps) {
  return (
    <div
      onClick={onFlip}
      style={{ perspective: '1000px' }}
      className="w-80 h-52 cursor-pointer select-none"
    >
      <div
        style={{
          transformStyle: 'preserve-3d',
          transition: 'transform 0.5s',
          transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
          position: 'relative',
          width: '100%',
          height: '100%',
        }}
      >
        {/* Front face */}
        <div
          style={{ backfaceVisibility: 'hidden' }}
          className="absolute inset-0 bg-white rounded-2xl shadow-lg flex items-center justify-center p-6"
        >
          <p className="text-3xl font-bold text-gray-800 text-center">{front}</p>
        </div>
        {/* Back face */}
        <div
          style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}
          className="absolute inset-0 bg-indigo-600 rounded-2xl shadow-lg flex items-center justify-center p-6"
        >
          <p className="text-2xl font-semibold text-white text-center">{back}</p>
        </div>
      </div>
    </div>
  )
}
```

---

## API Client Pattern (Frontend)
Typed fetch wrapper with silent token refresh on 401.

```typescript
// api/client.ts — see full implementation in that file
// Usage pattern:
const sets = await apiClient<FlashcardSet[]>('GET', '/sets')
const newSet = await apiClient<FlashcardSet>('POST', '/sets', { name: 'Greetings', languageId: 1 })
const updated = await apiClient<FlashcardSet>('PATCH', `/sets/${id}`, { name: 'Updated' })
await apiClient('DELETE', `/sets/${id}`)
```

---

## Protected Route Pattern (Frontend)

```typescript
// features/auth/ProtectedLayout.tsx
export function ProtectedLayout() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <Outlet />
}
```
