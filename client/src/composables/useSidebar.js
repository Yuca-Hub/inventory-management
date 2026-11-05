import { ref, onMounted, onBeforeUnmount } from 'vue'

const STORAGE_KEY = 'sidebar-collapsed'

// Returns true/false for a saved choice, or null when the user never chose.
const readStored = () => {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    return value === null ? null : value === 'true'
  } catch (err) {
    return null
  }
}

const writeStored = (value) => {
  try {
    localStorage.setItem(STORAGE_KEY, String(value))
  } catch (err) {
    // Storage unavailable (private mode, quota): the choice just won't persist.
  }
}

export function useSidebar() {
  // < 1024px: default to the icons-only rail. < 640px: off-canvas drawer.
  const narrowQuery = window.matchMedia('(max-width: 1023px)')
  const mobileQuery = window.matchMedia('(max-width: 639px)')

  // A saved choice wins on load; otherwise follow the viewport.
  const collapsed = ref(readStored() ?? narrowQuery.matches)
  const isMobile = ref(mobileQuery.matches)
  const drawerOpen = ref(false)

  // Crossing the 1024px line re-applies the viewport default: collapse when
  // shrinking, restore the saved choice (or expanded) when growing.
  const onNarrowChange = (event) => {
    collapsed.value = event.matches ? true : (readStored() ?? false)
  }

  const onMobileChange = (event) => {
    isMobile.value = event.matches
    if (!event.matches) drawerOpen.value = false
  }

  const onKeydown = (event) => {
    if (event.key === 'Escape' && drawerOpen.value) drawerOpen.value = false
  }

  const toggleCollapsed = () => {
    collapsed.value = !collapsed.value
    writeStored(collapsed.value)
  }

  const openDrawer = () => { drawerOpen.value = true }
  const closeDrawer = () => { drawerOpen.value = false }

  onMounted(() => {
    narrowQuery.addEventListener('change', onNarrowChange)
    mobileQuery.addEventListener('change', onMobileChange)
    window.addEventListener('keydown', onKeydown)
  })

  onBeforeUnmount(() => {
    narrowQuery.removeEventListener('change', onNarrowChange)
    mobileQuery.removeEventListener('change', onMobileChange)
    window.removeEventListener('keydown', onKeydown)
  })

  return { collapsed, isMobile, drawerOpen, toggleCollapsed, openDrawer, closeDrawer }
}
