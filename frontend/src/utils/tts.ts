/**
 * Speak text using the browser's Web Speech API.
 * @param text     - text to speak
 * @param langCode - BCP-47 language tag, e.g. "en", "ru", "de"
 */
export function speak(text: string, langCode: string): void {
  if (!window.speechSynthesis) return
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = langCode
  utterance.rate = 0.9
  window.speechSynthesis.speak(utterance)
}
