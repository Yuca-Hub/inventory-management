<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="confirmation" class="confirmation" role="status">
        {{ t('restocking.success', {
          orderNumber: confirmation.order_number,
          leadTime: t('restocking.leadTimeDays', { days: confirmation.lead_time_days })
        }) }}
        <router-link to="/orders" class="confirmation-link">{{ t('restocking.viewOrders') }}</router-link>
      </div>

      <div v-if="candidates.length === 0" class="card">
        <div class="loading">{{ t('restocking.empty') }}</div>
      </div>

      <template v-else>
        <div class="card budget-card">
          <label class="budget-label" for="budget-slider">
            {{ t('restocking.budgetSlider') }}: {{ currencySymbol }}{{ budget.toLocaleString() }}
          </label>
          <input
            id="budget-slider"
            v-model.number="budget"
            class="budget-slider"
            type="range"
            min="0"
            :max="maxBudget"
            :step="sliderStep"
          />
          <div class="slider-range">
            <span>{{ currencySymbol }}0</span>
            <span>{{ currencySymbol }}{{ maxBudget.toLocaleString() }}</span>
          </div>
          <p class="budget-note">{{ t('restocking.note') }}</p>
        </div>

        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-label">{{ t('restocking.budget') }}</div>
            <div class="stat-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
          </div>
          <div class="stat-card info">
            <div class="stat-label">{{ t('restocking.selectedTotal') }}</div>
            <div class="stat-value">{{ currencySymbol }}{{ selectedTotal.toLocaleString() }}</div>
          </div>
          <div :class="['stat-card', remainingBudget < 0 ? 'danger' : 'success']">
            <div class="stat-label">{{ t('restocking.remainingBudget') }}</div>
            <div class="stat-value">{{ currencySymbol }}{{ remainingBudget.toLocaleString() }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">{{ t('restocking.itemsSelected') }}</div>
            <div class="stat-value">{{ selectedItems.length }}</div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ candidates.length }})</h3>
            <button
              type="button"
              class="btn-primary"
              :disabled="selectedItems.length === 0 || submitting"
              @click="placeOrder"
            >
              {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
            </button>
          </div>

          <div v-if="submitError" class="error">{{ submitError }}</div>

          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th class="col-check">{{ t('restocking.table.select') }}</th>
                  <th>{{ t('restocking.table.sku') }}</th>
                  <th>{{ t('restocking.table.name') }}</th>
                  <th>{{ t('restocking.table.category') }}</th>
                  <th>{{ t('restocking.table.warehouse') }}</th>
                  <th class="num">{{ t('restocking.table.onHand') }}</th>
                  <th class="num">{{ t('restocking.table.forecast') }}</th>
                  <th class="num">{{ t('restocking.table.quantityToOrder') }}</th>
                  <th class="num">{{ t('restocking.table.unitCost') }}</th>
                  <th class="num">{{ t('restocking.table.lineCost') }}</th>
                  <th class="num">{{ t('restocking.table.leadTime') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in candidates" :key="item.sku" :class="{ 'row-selected': isSelected(item.sku) }">
                  <td class="col-check">
                    <input
                      type="checkbox"
                      :checked="isSelected(item.sku)"
                      :aria-label="item.sku"
                      @change="toggleItem(item.sku)"
                    />
                  </td>
                  <td><strong>{{ item.sku }}</strong></td>
                  <td>{{ translateProductName(item.name) }}</td>
                  <td>{{ item.category }}</td>
                  <td>{{ translateWarehouse(item.warehouse) }}</td>
                  <td class="num">{{ item.quantity_on_hand.toLocaleString() }}</td>
                  <td class="num">{{ item.forecasted_demand.toLocaleString() }}</td>
                  <td class="num">{{ item.shortfall.toLocaleString() }}</td>
                  <td class="num">{{ currencySymbol }}{{ item.unit_cost.toLocaleString() }}</td>
                  <td class="num"><strong>{{ currencySymbol }}{{ item.line_cost.toLocaleString() }}</strong></td>
                  <td class="num">{{ t('restocking.leadTimeDays', { days: item.lead_time_days }) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const candidates = ref([])
    const budget = ref(0)
    // Set of selected SKUs; replaced (not mutated) so reactivity is straightforward
    const selectedSkus = ref(new Set())
    const submitting = ref(false)
    const submitError = ref(null)
    const confirmation = ref(null)

    const maxBudget = computed(() => {
      return candidates.value.reduce((sum, c) => sum + c.line_cost, 0)
    })

    // Roughly 1% of the range, rounded down to a power of ten (min 1)
    const sliderStep = computed(() => {
      if (maxBudget.value < 100) return 1
      return Math.pow(10, Math.floor(Math.log10(maxBudget.value)) - 2)
    })

    // Greedy priority fill: candidates arrive in priority order. Take an item only
    // if its full line cost fits the remaining budget; otherwise skip it and keep
    // going, so cheaper lower-priority items can still use leftover budget.
    const recommendedSkus = computed(() => {
      const result = new Set()
      let remaining = budget.value
      for (const item of candidates.value) {
        if (item.line_cost <= remaining) {
          result.add(item.sku)
          remaining -= item.line_cost
        }
      }
      return result
    })

    // Moving the slider re-derives the recommendation and intentionally discards
    // any manual ticks/unticks the user made.
    watch(recommendedSkus, (skus) => {
      selectedSkus.value = new Set(skus)
    })

    const isSelected = (sku) => selectedSkus.value.has(sku)

    const toggleItem = (sku) => {
      const next = new Set(selectedSkus.value)
      if (next.has(sku)) {
        next.delete(sku)
      } else {
        next.add(sku)
      }
      selectedSkus.value = next
    }

    // Preserve priority order of the candidate list
    const selectedItems = computed(() => {
      return candidates.value.filter(c => selectedSkus.value.has(c.sku))
    })

    const selectedTotal = computed(() => {
      return selectedItems.value.reduce((sum, c) => sum + c.line_cost, 0)
    })

    // Can go negative if the user manually ticks items beyond the budget
    const remainingBudget = computed(() => budget.value - selectedTotal.value)

    const loadCandidates = async () => {
      try {
        loading.value = true
        error.value = null
        candidates.value = await api.getRestockingCandidates()
        // Default to the full budget so every candidate is recommended initially.
        // The recommendedSkus watcher is not guaranteed to fire if the value is
        // unchanged, so seed the selection explicitly.
        budget.value = maxBudget.value
        selectedSkus.value = new Set(recommendedSkus.value)
      } catch (err) {
        console.error('Failed to load restocking candidates:', err)
        error.value = t('restocking.loadError')
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (selectedItems.value.length === 0 || submitting.value) return
      try {
        submitting.value = true
        submitError.value = null
        confirmation.value = null
        const result = await api.createRestockingOrder({
          items: selectedItems.value.map(c => ({ sku: c.sku, quantity: c.shortfall })),
          budget: budget.value
        })
        confirmation.value = result
        await loadCandidates()
      } catch (err) {
        // Server returns a human-readable reason in response.data.detail (400/404)
        const detail = err.response && err.response.data && err.response.data.detail
        submitError.value = typeof detail === 'string' ? detail : t('restocking.submitError')
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadCandidates)

    return {
      t,
      currencySymbol,
      loading,
      error,
      candidates,
      budget,
      maxBudget,
      sliderStep,
      selectedItems,
      selectedTotal,
      remainingBudget,
      submitting,
      submitError,
      confirmation,
      isSelected,
      toggleItem,
      placeOrder,
      translateProductName,
      translateWarehouse
    }
  }
}
</script>

<style scoped>
.budget-label {
  display: block;
  font-size: 0.938rem;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 0.75rem;
}

.budget-slider {
  width: 100%;
  accent-color: #0f172a;
  cursor: pointer;
}

.slider-range {
  display: flex;
  justify-content: space-between;
  font-size: 0.813rem;
  color: #64748b;
  margin-top: 0.25rem;
}

.budget-note {
  margin-top: 0.75rem;
  font-size: 0.813rem;
  color: #64748b;
}

.btn-primary {
  background: #0f172a;
  color: #ffffff;
  border: 1px solid #0f172a;
  border-radius: 6px;
  padding: 0.5rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.btn-primary:hover:not(:disabled) {
  background: #1e293b;
}

.btn-primary:disabled {
  background: #e2e8f0;
  border-color: #e2e8f0;
  color: #64748b;
  cursor: not-allowed;
}

.confirmation {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
}

.confirmation-link {
  margin-left: 0.5rem;
  color: #2563eb;
  font-weight: 600;
}

.col-check {
  width: 60px;
  text-align: center;
}

.num {
  text-align: right;
}

.row-selected {
  background: #f8fafc;
}
</style>
