import { onBeforeUnmount, ref, watch } from 'vue'

export function useDismissibleMenu() {
  const menuRef = ref(null)
  const isMenuOpen = ref(false)

  function closeMenu() {
    isMenuOpen.value = false
  }

  function toggleMenu() {
    isMenuOpen.value = !isMenuOpen.value
  }

  function handleOutsidePointerDown(event) {
    if (!isMenuOpen.value) return

    const menuElement = menuRef.value

    if (menuElement?.contains(event.target)) return

    closeMenu()
  }

  function handleDocumentKeydown(event) {
    if (event.key === 'Escape') {
      closeMenu()
    }
  }

  function addDismissListeners() {
    document.addEventListener('pointerdown', handleOutsidePointerDown)
    document.addEventListener('keydown', handleDocumentKeydown)
  }

  function removeDismissListeners() {
    document.removeEventListener('pointerdown', handleOutsidePointerDown)
    document.removeEventListener('keydown', handleDocumentKeydown)
  }

  watch(isMenuOpen, (isOpen) => {
    if (isOpen) {
      addDismissListeners()
      return
    }

    removeDismissListeners()
  })

  onBeforeUnmount(removeDismissListeners)

  return {
    menuRef,
    isMenuOpen,
    closeMenu,
    toggleMenu,
  }
}
