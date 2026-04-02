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
      className="w-full max-w-lg cursor-pointer select-none"
      role="button"
      aria-label={isFlipped ? 'Card showing translation, click to flip back' : 'Card showing word, click to reveal translation'}
    >
      <div
        style={{
          transformStyle: 'preserve-3d',
          transition: 'transform 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
          transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
          position: 'relative',
          width: '100%',
          minHeight: '15rem',
        }}
      >
        {/* Front face — shows the Russian word */}
        <div
          style={{ backfaceVisibility: 'hidden' }}
          className="absolute inset-0 bg-white rounded-2xl shadow-lg border border-gray-200
                     flex flex-col items-center justify-center p-8"
        >
          <p className="text-xs uppercase tracking-widest text-gray-400 mb-3">Word</p>
          <p style={{ fontSize: 'clamp(0.875rem, 2.5vw, 2.25rem)' }} className="font-bold text-gray-900 text-center leading-snug">{front}</p>
          <p className="text-xs text-gray-400 mt-6">Tap to reveal translation</p>
        </div>

        {/* Back face — invisible spacer so the container grows to fit back content */}
        <div
          style={{ visibility: 'hidden', pointerEvents: 'none' }}
          className="flex flex-col items-center justify-center p-8"
          aria-hidden="true"
        >
          <p className="text-xs mb-3">&nbsp;</p>
          <p style={{ fontSize: 'clamp(0.875rem, 2.5vw, 2.25rem)' }} className="font-bold text-center leading-snug">{isFlipped ? back : front}</p>
        </div>

        {/* Back face — shows the translation */}
        <div
          style={{
            backfaceVisibility: 'hidden',
            transform: 'rotateY(180deg)',
          }}
          className="absolute inset-0 bg-primary-600 rounded-2xl shadow-lg
                     flex flex-col items-center justify-center p-8"
        >
          <p className="text-xs uppercase tracking-widest text-primary-200 mb-3">Translation</p>
          <p style={{ fontSize: 'clamp(0.875rem, 2.5vw, 2.25rem)' }} className="font-bold text-white text-center leading-snug">{back}</p>
        </div>
      </div>
    </div>
  )
}
