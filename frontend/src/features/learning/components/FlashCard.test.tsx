import { render, screen, fireEvent } from '@testing-library/react'
import { FlashCard } from './FlashCard'

describe('FlashCard', () => {
  const defaultProps = {
    front: 'Привет',
    back: 'Hello',
    isFlipped: false,
    onFlip: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders front text', () => {
    render(<FlashCard {...defaultProps} />)
    expect(screen.getByText('Привет')).toBeInTheDocument()
  })

  it('renders back text', () => {
    render(<FlashCard {...defaultProps} />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('calls onFlip when clicked', () => {
    render(<FlashCard {...defaultProps} />)
    fireEvent.click(screen.getByRole('button'))
    expect(defaultProps.onFlip).toHaveBeenCalledTimes(1)
  })

  it('has aria-label indicating front state when not flipped', () => {
    render(<FlashCard {...defaultProps} isFlipped={false} />)
    expect(screen.getByRole('button')).toHaveAttribute(
      'aria-label',
      'Card showing word, click to reveal translation',
    )
  })

  it('has aria-label indicating back state when flipped', () => {
    render(<FlashCard {...defaultProps} isFlipped={true} />)
    expect(screen.getByRole('button')).toHaveAttribute(
      'aria-label',
      'Card showing translation, click to flip back',
    )
  })

  it('applies rotateY(180deg) transform when flipped', () => {
    render(<FlashCard {...defaultProps} isFlipped={true} />)
    // The inner flip div is the direct child of the [role=button] wrapper
    const inner = screen.getByRole('button').firstElementChild as HTMLElement
    expect(inner.style.transform).toBe('rotateY(180deg)')
  })

  it('applies rotateY(0deg) transform when not flipped', () => {
    render(<FlashCard {...defaultProps} isFlipped={false} />)
    const inner = screen.getByRole('button').firstElementChild as HTMLElement
    expect(inner.style.transform).toBe('rotateY(0deg)')
  })
})
