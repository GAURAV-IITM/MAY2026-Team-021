<template>
  <section class="seat-filters card" aria-label="Seat filters">
    <div class="seat-filters__search">
      <SearchBar
        v-model="searchModel"
        placeholder="Search seats, students, shifts, or notes"
        @clear="clearSearch"
      />
    </div>

    <div class="seat-filters__field">
      <label class="form-label" for="seat-filter-shift">Shift</label>
      <select
        id="seat-filter-shift"
        class="form-select"
        :value="seatFilters.shift"
        @change="updateFilter('shift', $event.target.value)"
      >
        <option value="">All shifts</option>
        <option value="morning">Morning</option>
        <option value="afternoon">Afternoon</option>
        <option value="evening">Evening</option>
      </select>
    </div>

    <div class="seat-filters__field">
      <label class="form-label" for="seat-filter-status">Status</label>
      <select
        id="seat-filter-status"
        class="form-select"
        :value="seatFilters.status"
        @change="updateFilter('status', $event.target.value)"
      >
        <option value="">All statuses</option>
        <option value="available">Available</option>
        <option value="occupied">Occupied</option>
        <option value="reserved">Reserved</option>
        <option value="maintenance">Maintenance</option>
      </select>
    </div>

    <div class="seat-filters__field">
      <label class="form-label" for="seat-filter-floor">Floor</label>
      <select
        id="seat-filter-floor"
        class="form-select"
        :value="seatFilters.floor"
        @change="updateFilter('floor', $event.target.value)"
      >
        <option value="">All floors</option>
        <option
          v-for="floor in availableFloors"
          :key="floor"
          :value="String(floor)"
        >
          Floor {{ floor }}
        </option>
      </select>
    </div>

    <div class="seat-filters__field">
      <label class="form-label" for="seat-filter-seat-number">Seat Number</label>
      <input
        id="seat-filter-seat-number"
        class="form-control"
        type="search"
        :value="seatFilters.seatNumber"
        placeholder="Example: A-01"
        @input="updateFilter('seatNumber', $event.target.value)"
      />
    </div>

    <div class="seat-filters__field">
      <label class="form-label" for="seat-filter-student-name">Student Name</label>
      <input
        id="seat-filter-student-name"
        class="form-control"
        type="search"
        :value="seatFilters.studentName"
        placeholder="Search student"
        @input="updateFilter('studentName', $event.target.value)"
      />
    </div>

    <div class="seat-filters__field">
      <label class="form-label" for="seat-filter-availability">Availability</label>
      <select
        id="seat-filter-availability"
        class="form-select"
        :value="seatFilters.availability"
        @change="updateFilter('availability', $event.target.value)"
      >
        <option value="">All availability</option>
        <option value="available-now">Available now</option>
        <option value="assigned">Assigned</option>
        <option value="unassigned">Unassigned</option>
        <option value="blocked">Blocked</option>
        <option value="has-active-shift">Has active shift</option>
      </select>
    </div>

    <button
      class="btn btn--secondary seat-filters__reset"
      type="button"
      :disabled="!hasActiveSeatFilters"
      @click="seatStore.resetSeatFilters"
    >
      Reset Filters
    </button>
  </section>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { computed } from 'vue'

import SearchBar from '../common/SearchBar.vue'
import { useSeatStore } from '../../stores/seatStore'

const seatStore = useSeatStore()
const { seatFilters, availableFloors, hasActiveSeatFilters } =
  storeToRefs(seatStore)

const searchModel = computed({
  get() {
    return seatFilters.value.search
  },
  set(value) {
    updateFilter('search', value)
  },
})

function updateFilter(filterName, value) {
  seatStore.updateSeatFilter(filterName, value)
}

function clearSearch() {
  updateFilter('search', '')
}
</script>

<style scoped>
.seat-filters {
  display: grid;
  grid-template-columns:
    minmax(260px, 1.4fr)
    repeat(3, minmax(140px, 0.8fr))
    auto;
  gap: var(--space-4);
  align-items: end;
  padding: var(--space-4);
}

.seat-filters__search {
  align-self: end;
}

.seat-filters__search :deep(.search-bar) {
  max-width: none;
}

.seat-filters__field {
  display: grid;
  gap: var(--space-2);
}

.seat-filters__reset {
  white-space: nowrap;
}

@media (max-width: 1200px) {
  .seat-filters {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .seat-filters__search {
    grid-column: 1 / -1;
  }
}

@media (max-width: 760px) {
  .seat-filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 560px) {
  .seat-filters {
    grid-template-columns: 1fr;
  }

  .seat-filters__reset {
    justify-content: center;
    width: 100%;
  }
}
</style>

<!--
src/components/seat: Store-backed reusable filters for seat availability views.
TODO:
- Map these frontend filters to FastAPI query parameters when backend filtering is introduced.
-->
