<template>
  <aside
    id="app-sidebar"
    class="sidebar"
    :class="{ collapsed: isCollapsed, mobile: isMobile, open: drawerOpen }"
  >
    <div class="sidebar-brand">
      <div class="brand-mark" aria-hidden="true">{{ brandInitial }}</div>
      <div class="brand-text" :class="{ 'visually-hidden': isCollapsed }">
        <h1>{{ t('nav.companyName') }}</h1>
        <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
      </div>
    </div>

    <!-- Only the link list scrolls, so footer dropdowns are not clipped. -->
    <nav class="sidebar-nav" :aria-label="t('nav.primaryNavigation')">
      <ul>
        <li v-for="item in navItems" :key="item.to">
          <!-- router-link adds aria-current="page" on the exact match. We style
               the exact class because "/" would otherwise match every route. -->
          <router-link
            :to="item.to"
            class="nav-link"
            :title="isCollapsed ? t(item.labelKey) : null"
          >
            <svg
              class="nav-icon"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.75"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
              focusable="false"
            >
              <path :d="item.icon" />
            </svg>
            <span class="nav-label" :class="{ 'visually-hidden': isCollapsed }">
              {{ t(item.labelKey) }}
            </span>
          </router-link>
        </li>
      </ul>
    </nav>

    <div class="sidebar-footer">
      <div class="footer-slot">
        <slot name="footer" />
      </div>
      <button
        v-if="!isMobile"
        type="button"
        class="toggle-button"
        :aria-pressed="isCollapsed ? 'true' : 'false'"
        aria-controls="app-sidebar"
        :title="isCollapsed ? toggleLabel : null"
        @click="$emit('toggle')"
      >
        <svg
          class="nav-icon toggle-icon"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.75"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
          focusable="false"
        >
          <path d="M15 6l-6 6 6 6" />
        </svg>
        <span class="nav-label" :class="{ 'visually-hidden': isCollapsed }">{{ toggleLabel }}</span>
      </button>
    </div>
  </aside>
</template>

<script>
import { computed } from 'vue'
import { useI18n } from '../composables/useI18n'

// Each icon is a single stroke path on a 24x24 grid.
const navItems = [
  { to: '/', labelKey: 'nav.overview', icon: 'M3 3h7v7H3z M14 3h7v7h-7z M14 14h7v7h-7z M3 14h7v7H3z' },
  { to: '/inventory', labelKey: 'nav.inventory', icon: 'M21 8l-9-5-9 5v8l9 5 9-5z M3 8l9 5 9-5 M12 13v8' },
  { to: '/orders', labelKey: 'nav.orders', icon: 'M9 4h6v3H9z M7 5H5v16h14V5h-2 M9 12h6 M9 16h6' },
  { to: '/spending', labelKey: 'nav.finance', icon: 'M3 20h18 M6 16v-5 M11 16V7 M16 16v-8' },
  { to: '/demand', labelKey: 'nav.demandForecast', icon: 'M3 17l6-6 4 4 8-8 M15 7h6v6' },
  { to: '/restocking', labelKey: 'nav.restocking', icon: 'M20 11a8 8 0 0 0-14-4L4 9 M4 4v5h5 M4 13a8 8 0 0 0 14 4l2-2 M20 20v-5h-5' },
  { to: '/reports', labelKey: 'nav.reports', icon: 'M14 3H6v18h12V7z M14 3v4h4 M9 12h6 M9 16h6' }
]

export default {
  name: 'AppSidebar',
  props: {
    collapsed: { type: Boolean, default: false },
    isMobile: { type: Boolean, default: false },
    drawerOpen: { type: Boolean, default: false }
  },
  emits: ['toggle'],
  setup(props) {
    const { t } = useI18n()

    // The drawer is always shown expanded; the rail only applies to the in-flow sidebar.
    const isCollapsed = computed(() => props.collapsed && !props.isMobile)
    const toggleLabel = computed(() => (props.collapsed ? t('nav.expand') : t('nav.collapse')))
    const brandInitial = computed(() => t('nav.companyName').charAt(0))

    return { t, navItems, isCollapsed, toggleLabel, brandInitial }
  }
}
</script>

<style scoped>
.sidebar {
  position: sticky;
  top: 0;
  align-self: start;
  height: 100vh;
  width: 240px;
  display: flex;
  flex-direction: column;
  padding: 0.75rem;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  z-index: 100;
  transition: width 150ms ease;
}

.sidebar.collapsed {
  width: 64px;
}

/* Off-canvas drawer below 640px */
.sidebar.mobile {
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  height: auto;
  z-index: 200;
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.2);
  transform: translateX(-100%);
  visibility: hidden;
  /* Delay hiding until the slide-out finishes so closed links are not tabbable. */
  transition: transform 150ms ease, visibility 0s linear 150ms;
}

.sidebar.mobile.open {
  transform: translateX(0);
  visibility: visible;
  transition: transform 150ms ease, visibility 0s;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding-bottom: 0.75rem;
  margin-bottom: 0.5rem;
  border-bottom: 1px solid #e2e8f0;
  min-height: 52px;
}

.brand-mark {
  flex: none;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: #0f172a;
  color: #ffffff;
  font-weight: 700;
  font-size: 1.125rem;
}

.brand-text {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.brand-text h1 {
  font-size: 1rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-subtitle {
  font-size: 0.75rem;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-nav {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-nav ul {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.nav-link,
.toggle-button {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  height: 40px;
  /* 10px + 20px icon + 10px = 40px, so icons stay put when the rail collapses. */
  padding: 0 10px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #64748b;
  font-family: inherit;
  font-size: 0.938rem;
  font-weight: 500;
  text-decoration: none;
  white-space: nowrap;
  cursor: pointer;
}

.nav-link:hover,
.toggle-button:hover {
  color: #0f172a;
  background: #f1f5f9;
}

.nav-link.router-link-exact-active {
  color: #0f172a;
  background: #f1f5f9;
  font-weight: 600;
}

.nav-link.router-link-exact-active::before {
  content: '';
  position: absolute;
  /* Inside the link: the nav list clips horizontal overflow. */
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: #0f172a;
}

.nav-link:focus-visible,
.toggle-button:focus-visible {
  outline: 2px solid #0f172a;
  outline-offset: 2px;
}

.nav-icon {
  flex: none;
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding-top: 0.75rem;
  margin-top: 0.5rem;
  border-top: 1px solid #e2e8f0;
}

.footer-slot {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.toggle-icon {
  transition: transform 150ms ease;
}

.sidebar.collapsed .toggle-icon {
  transform: rotate(180deg);
}

/* Reused header components: open their menus upward from the footer. */
.sidebar-footer :deep(.dropdown-menu) {
  top: auto;
  bottom: calc(100% + 0.5rem);
  left: 0;
  right: auto;
}

.sidebar-footer :deep(.profile-button),
.sidebar-footer :deep(.language-button) {
  width: 100%;
}

.sidebar-footer :deep(.chevron) {
  margin-left: auto;
}

.sidebar-footer :deep(.profile-button:focus-visible),
.sidebar-footer :deep(.language-button:focus-visible) {
  outline: 2px solid #0f172a;
  outline-offset: 2px;
}

/* Rail: hide labels visually but keep them in the accessibility tree. */
.sidebar.collapsed .sidebar-footer :deep(.profile-name),
.sidebar.collapsed .sidebar-footer :deep(.language-label),
.sidebar.collapsed .sidebar-footer :deep(.chevron) {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
}

.sidebar.collapsed .sidebar-footer :deep(.profile-button) {
  justify-content: center;
  padding: 3px;
}

.sidebar.collapsed .sidebar-footer :deep(.language-button) {
  justify-content: center;
  padding: 0.5rem 0;
}

@media (prefers-reduced-motion: reduce) {
  .sidebar,
  .sidebar.mobile,
  .sidebar.mobile.open,
  .toggle-icon {
    transition: none;
  }
}
</style>
