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
      className="w-full max-w-lg h-60 cursor-pointer select-none"
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
          height: '100%',
        }}
      >
        {/* Front face — shows the Russian word */}
        <div
          style={{ backfaceVisibility: 'hidden' }}
          className="absolute inset-0 bg-white rounded-2xl shadow-lg border border-gray-200
                     flex flex-col items-center justify-center p-8"
        >
          <p className="text-xs uppercase tracking-widest text-gray-400 mb-3">Word</p>
          <p className="text-4xl font-bold text-gray-900 text-center">{front}</p>
          <p className="text-xs text-gray-400 mt-6">Tap to reveal translation</p>
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
          <p className="text-4xl font-bold text-white text-center">{back}</p>
        </div>
      </div>
    </div>
  )
}
