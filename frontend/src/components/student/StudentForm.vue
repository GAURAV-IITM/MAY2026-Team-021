<template>
  <form class="student-form" novalidate @submit.prevent="handleSubmit">
    <section class="form-card student-form__section">
      <header class="card__header">
        <div>
          <h2 class="text-h5 m-0">Student Profile</h2>
          <p class="text-small text-muted m-0">Identity and enrollment details.</p>
        </div>
      </header>

      <div class="card__body student-form__grid">
        <div class="form-field">
          <label class="form-label" for="student-enrollment">Enrollment Number</label>
          <input
            id="student-enrollment"
            v-model.trim="form.enrollmentNumber"
            class="form-control"
            placeholder="Generated automatically when left empty"
          />
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.status }">
          <label class="form-label" for="student-status">Status</label>
          <select id="student-status" v-model="form.status" class="form-select">
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="suspended">Suspended</option>
            <option value="left">Left</option>
          </select>
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.firstName }">
          <label class="form-label" for="student-first-name">First Name</label>
          <input
            id="student-first-name"
            v-model.trim="form.firstName"
            class="form-control"
            autocomplete="given-name"
            :aria-invalid="Boolean(errors.firstName)"
          />
          <p v-if="errors.firstName" class="form-help">{{ errors.firstName }}</p>
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.lastName }">
          <label class="form-label" for="student-last-name">Last Name</label>
          <input
            id="student-last-name"
            v-model.trim="form.lastName"
            class="form-control"
            autocomplete="family-name"
            :aria-invalid="Boolean(errors.lastName)"
          />
          <p v-if="errors.lastName" class="form-help">{{ errors.lastName }}</p>
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.joiningDate }">
          <label class="form-label" for="student-joining-date">Joining Date</label>
          <input
            id="student-joining-date"
            v-model="form.joiningDate"
            class="form-control"
            type="date"
            :aria-invalid="Boolean(errors.joiningDate)"
          />
          <p v-if="errors.joiningDate" class="form-help">{{ errors.joiningDate }}</p>
        </div>

        <div class="form-field">
          <label class="form-label" for="student-date-of-birth">Date of Birth</label>
          <input
            id="student-date-of-birth"
            v-model="form.dateOfBirth"
            class="form-control"
            type="date"
          />
        </div>

        <div class="form-field student-form__full-row">
          <label class="form-label" for="student-address">Address</label>
          <textarea
            id="student-address"
            v-model.trim="form.address"
            class="form-textarea"
            autocomplete="street-address"
          ></textarea>
        </div>
      </div>
    </section>

    <section
      v-if="showSeatAssignment"
      class="form-card student-form__section"
    >
      <header class="card__header">
        <div>
          <h2 class="text-h5 m-0">Seat Assignment</h2>
          <p class="text-small text-muted m-0">
            {{ seatAssignmentDescription }}
          </p>
        </div>
      </header>

      <div class="card__body student-form__allocation">
        <template v-if="isEditMode">
          <div
            v-if="currentSeatAssignments.length"
            class="student-form__current-assignments"
          >
            <span class="form-label">Current Assignment</span>
            <article
              v-for="assignment in currentSeatAssignments"
              :key="currentAssignmentKey(assignment)"
              class="student-form__current-assignment"
            >
              <div>
                <strong>
                  Seat {{ assignment.seatNumber }}
                  <span class="text-muted">· {{ assignment.floorName }}</span>
                </strong>
                <span>{{ assignment.shiftNames.join(', ') }}</span>
              </div>
              <span class="text-small text-muted">
                {{ assignment.startDate }} to {{ assignment.endDate }}
              </span>
            </article>
          </div>

          <div v-else class="student-form__empty-assignment">
            <strong>No active seat assignment</strong>
            <span class="text-small text-muted">
              This student does not currently hold a seat.
            </span>
          </div>

          <div
            class="form-field"
            :class="{ 'form-field--error': errors.allocationAction }"
          >
            <label class="form-label" for="allocation-action">
              Allocation Action
            </label>
            <select
              id="allocation-action"
              v-model="form.allocationAction"
              class="form-select"
            >
              <option value="keep">
                {{ hasCurrentSeatAssignment ? 'Keep current assignment' : 'No change' }}
              </option>
              <option value="replace" :disabled="!canAssignSeat">
                {{ hasCurrentSeatAssignment ? 'Change seat or shifts' : 'Assign a seat' }}
              </option>
              <option v-if="hasCurrentSeatAssignment" value="remove">
                Remove current assignment
              </option>
            </select>
            <p v-if="errors.allocationAction" class="form-help">
              {{ errors.allocationAction }}
            </p>
            <p
              v-else-if="!canAssignSeat"
              class="text-small text-muted m-0"
            >
              Non-active students cannot receive a new allocation. Saving this
              status will close any current assignment.
            </p>
          </div>

          <div
            v-if="hasAllocationChange"
            class="form-field"
            :class="{ 'form-field--error': errors.allocationChangeReason }"
          >
            <label class="form-label" for="allocation-change-reason">
              Reason for Change
            </label>
            <textarea
              id="allocation-change-reason"
              v-model.trim="form.allocationChangeReason"
              class="form-textarea"
              placeholder="Example: Student requested a different floor"
              :aria-invalid="Boolean(errors.allocationChangeReason)"
            ></textarea>
            <p v-if="errors.allocationChangeReason" class="form-help">
              {{ errors.allocationChangeReason }}
            </p>
          </div>

          <div
            v-if="form.allocationAction === 'remove'"
            class="alert alert--warning student-form__allocation-warning"
            role="status"
          >
            The current assignment will be closed and retained in seat history.
          </div>
        </template>

        <label
          v-else
          class="checkbox student-form__assignment-toggle"
          :class="{ 'student-form__assignment-toggle--disabled': !canAssignSeat }"
        >
          <input
            v-model="form.assignSeat"
            type="checkbox"
            :disabled="!canAssignSeat"
          />
          <span>
            <strong>Assign a seat during registration</strong>
            <small v-if="canAssignSeat">
              The student and seat assignment will be created together.
            </small>
            <small v-else>
              Change the student status to Active before assigning a seat.
            </small>
          </span>
        </label>

        <div v-if="wantsSeatReplacement" class="student-form__allocation-fields">
          <div class="student-form__grid">
            <div
              class="form-field"
              :class="{ 'form-field--error': errors.allocationStartDate }"
            >
              <label class="form-label" for="allocation-start-date">
                Allocation Start Date
              </label>
              <input
                id="allocation-start-date"
                v-model="form.allocationStartDate"
                class="form-control"
                type="date"
                :min="form.joiningDate"
                :aria-invalid="Boolean(errors.allocationStartDate)"
              />
              <p v-if="errors.allocationStartDate" class="form-help">
                {{ errors.allocationStartDate }}
              </p>
            </div>

            <div
              class="form-field"
              :class="{ 'form-field--error': errors.allocationEndDate }"
            >
              <label class="form-label" for="allocation-end-date">
                Allocation End Date
              </label>
              <input
                id="allocation-end-date"
                v-model="form.allocationEndDate"
                class="form-control"
                type="date"
                :min="allocationEndDateMinimum"
                :aria-invalid="Boolean(errors.allocationEndDate)"
              />
              <p v-if="errors.allocationEndDate" class="form-help">
                {{ errors.allocationEndDate }}
              </p>
            </div>

            <div
              class="form-field student-form__full-row"
              :class="{ 'form-field--error': errors.activeShifts }"
            >
              <div class="student-form__field-header">
                <span class="form-label">Shifts</span>
                <button
                  class="btn btn--ghost btn--sm"
                  type="button"
                  :disabled="form.activeShifts.length === 0"
                  @click="clearSelectedShifts"
                >
                  <X :size="15" aria-hidden="true" />
                  Clear
                </button>
              </div>

              <div
                class="student-form__shift-options"
                role="group"
                aria-label="Select one or more non-overlapping shifts"
              >
                <label
                  v-for="shift in shiftOptions"
                  :key="shift.value"
                  class="checkbox student-form__shift-option"
                >
                  <input
                    v-model="form.activeShifts"
                    type="checkbox"
                    :value="shift.value"
                  />
                  <span>
                    <strong>{{ shift.label }}</strong>
                    <small>{{ shift.timing }}</small>
                  </span>
                </label>

                <p
                  v-if="shiftOptions.length === 0"
                  class="text-small text-muted m-0"
                >
                  No active shifts are available.
                </p>
              </div>

              <p v-if="errors.activeShifts" class="form-help">
                {{ errors.activeShifts }}
              </p>
            </div>

            <div
              class="form-field student-form__full-row"
              :class="{ 'form-field--error': errors.seatId }"
            >
              <label class="form-label" for="student-seat">Available Seat</label>
              <select
                id="student-seat"
                v-model="form.seatId"
                class="form-select"
                :disabled="!canChooseSeat"
                :aria-invalid="Boolean(errors.seatId)"
              >
                <option value="">{{ seatPlaceholder }}</option>
                <option
                  v-for="seat in availableSeatOptions"
                  :key="seat.seatId"
                  :value="seat.seatId"
                >
                  {{ seat.seatNumber }} · {{ seat.floorName }}
                </option>
              </select>
              <p v-if="errors.seatId" class="form-help">{{ errors.seatId }}</p>
              <p
                v-else-if="availabilityError"
                class="form-help student-form__availability-error"
                role="alert"
              >
                {{ availabilityError }}
              </p>
              <p v-else class="text-small text-muted m-0">
                {{ availabilityMessage }}
              </p>
            </div>

            <div class="form-field student-form__full-row">
              <label class="form-label" for="allocation-notes">
                Allocation Notes
              </label>
              <textarea
                id="allocation-notes"
                v-model.trim="form.allocationNotes"
                class="form-textarea"
                placeholder="Optional seat assignment note"
              ></textarea>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="form-card student-form__section">
      <header class="card__header">
        <div>
          <h2 class="text-h5 m-0">Contact Information</h2>
          <p class="text-small text-muted m-0">Used for account access and notices.</p>
        </div>
      </header>

      <div class="card__body student-form__grid">
        <div class="form-field" :class="{ 'form-field--error': errors.email }">
          <label class="form-label" for="student-email">Email</label>
          <input
            id="student-email"
            v-model.trim="form.email"
            class="form-control"
            type="email"
            autocomplete="email"
            :aria-invalid="Boolean(errors.email)"
          />
          <p v-if="errors.email" class="form-help">{{ errors.email }}</p>
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.phone }">
          <label class="form-label" for="student-phone">Phone</label>
          <input
            id="student-phone"
            v-model.trim="form.phone"
            class="form-control"
            type="tel"
            autocomplete="tel"
            :aria-invalid="Boolean(errors.phone)"
          />
          <p v-if="errors.phone" class="form-help">{{ errors.phone }}</p>
        </div>

        <div class="form-field">
          <label class="form-label" for="student-guardian-name">Guardian Name</label>
          <input
            id="student-guardian-name"
            v-model.trim="form.guardianName"
            class="form-control"
          />
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.guardianPhone }">
          <label class="form-label" for="student-guardian-phone">Guardian Phone</label>
          <input
            id="student-guardian-phone"
            v-model.trim="form.guardianPhone"
            class="form-control"
            type="tel"
            :aria-invalid="Boolean(errors.guardianPhone)"
          />
          <p v-if="errors.guardianPhone" class="form-help">
            {{ errors.guardianPhone }}
          </p>
        </div>
      </div>
    </section>

    <section class="form-card student-form__section">
      <header class="card__header">
        <div>
          <h2 class="text-h5 m-0">Library Preferences</h2>
          <p class="text-small text-muted m-0">Fee default and administrative notes.</p>
        </div>
      </header>

      <div class="card__body student-form__grid">
        <div class="form-field" :class="{ 'form-field--error': errors.feeAmount }">
          <label class="form-label" for="student-fee-amount">Monthly Fee</label>
          <input
            id="student-fee-amount"
            v-model.number="form.feeAmount"
            class="form-control"
            type="number"
            min="0"
            step="1"
            :aria-invalid="Boolean(errors.feeAmount)"
          />
          <p v-if="errors.feeAmount" class="form-help">{{ errors.feeAmount }}</p>
        </div>

        <div class="form-field">
          <label class="form-label" for="student-language">Preferred Language</label>
          <select id="student-language" v-model="form.preferredLanguage" class="form-select">
            <option value="en">English</option>
            <option value="hi">Hindi</option>
          </select>
        </div>

        <div class="form-field student-form__full-row">
          <label class="form-label" for="student-notes">Notes</label>
          <textarea
            id="student-notes"
            v-model.trim="form.notes"
            class="form-textarea"
            placeholder="Optional internal notes"
          ></textarea>
        </div>

        <label v-if="!isEditMode" class="checkbox student-form__invitation">
          <input v-model="form.sendInvitation" type="checkbox" />
          <span>
            <strong>Create student portal invitation</strong>
            <small>A password setup link will be created after registration.</small>
          </span>
        </label>
      </div>
    </section>

    <div class="student-form__actions">
      <button class="btn btn--secondary" type="button" :disabled="isSubmitting" @click="$emit('cancel')">
        Cancel
      </button>
      <button
        class="btn btn--primary"
        type="submit"
        :disabled="isSubmitting || (wantsSeatReplacement && isAvailabilityLoading)"
      >
        <span v-if="isSubmitting" class="btn__loader" aria-hidden="true"></span>
        {{ isSubmitting ? submittingLabel : submitLabel }}
      </button>
    </div>
  </form>
</template>

<script setup>
import { X } from '@lucide/vue'
import { computed, reactive, watch } from 'vue'

import { doShiftTimingsOverlap } from '../../utils/timeIntervals'
import {
  isNonNegativeNumber,
  isRequired,
  isValidEmail,
  isValidIndianPhone,
} from '../../utils/validators'

const props = defineProps({
  initialValues: { type: Object, default: () => ({}) },
  isSubmitting: { type: Boolean, default: false },
  submitLabel: { type: String, default: 'Save Student' },
  submittingLabel: { type: String, default: 'Saving Student' },
  enableSeatAssignment: { type: Boolean, default: false },
  shifts: { type: Array, default: () => [] },
  allocationAvailability: { type: Object, default: null },
  isAvailabilityLoading: { type: Boolean, default: false },
  availabilityError: { type: String, default: '' },
})

const emit = defineEmits([
  'submit',
  'cancel',
  'availability-request',
  'availability-clear',
])
const isEditMode = computed(() => Boolean(props.initialValues?.id))
const showSeatAssignment = computed(() => props.enableSeatAssignment)
const currentSeatAssignments = computed(() => {
  return Array.isArray(props.initialValues?.seatAssignments)
    ? props.initialValues.seatAssignments
    : []
})
const hasCurrentSeatAssignment = computed(
  () => currentSeatAssignments.value.length > 0,
)
const canAssignSeat = computed(() => form.status === 'active')
const today = new Date().toISOString().slice(0, 10)
const initialSeatAssignment = currentSeatAssignments.value[0] || null
const initialJoiningDate = props.initialValues.joiningDate || today
const initialAllocationStartDate = [today, initialJoiningDate].sort().at(-1)
const initialAllocationEndDate =
  initialSeatAssignment?.endDate >= initialAllocationStartDate
    ? initialSeatAssignment.endDate
    : ''
const form = reactive({
  enrollmentNumber: props.initialValues.enrollmentNumber || '',
  firstName: props.initialValues.firstName || '',
  lastName: props.initialValues.lastName || '',
  email: props.initialValues.email || '',
  phone: props.initialValues.phone || '',
  address: props.initialValues.address || '',
  guardianName: props.initialValues.guardianName || '',
  guardianPhone: props.initialValues.guardianPhone || '',
  dateOfBirth: props.initialValues.dateOfBirth || '',
  preferredLanguage: props.initialValues.preferredLanguage || 'en',
  joiningDate: initialJoiningDate,
  feeAmount: Number(props.initialValues.feeAmount ?? 0),
  status: props.initialValues.status || 'active',
  notes: props.initialValues.notes || '',
  sendInvitation: true,
  assignSeat: false,
  allocationAction: 'keep',
  allocationStartDate: initialAllocationStartDate,
  allocationEndDate: initialAllocationEndDate,
  activeShifts: [...(initialSeatAssignment?.shiftIds || [])],
  seatId: initialSeatAssignment?.seatId || '',
  allocationNotes: '',
  allocationChangeReason: '',
})
const errors = reactive({})

const hasAllocationChange = computed(() => {
  return isEditMode.value && form.allocationAction !== 'keep'
})
const wantsSeatReplacement = computed(() => {
  return isEditMode.value
    ? form.allocationAction === 'replace'
    : form.assignSeat
})
const seatAssignmentDescription = computed(() => {
  return isEditMode.value
    ? 'Keep, replace, or remove the current allocation without losing history.'
    : 'Optionally assign one available seat for non-overlapping shifts.'
})

const allocationEndDateMinimum = computed(() => {
  return [today, form.allocationStartDate, form.joiningDate]
    .filter(Boolean)
    .sort()
    .at(-1)
})

const shiftOptions = computed(() => {
  return props.shifts
    .filter((shift) => shift.isEnabled !== false)
    .map((shift) => ({
      value: shift.id,
      label: shift.name,
      timing: `${shift.startTime}-${shift.endTime}`,
    }))
})

const availableSeatOptions = computed(() => {
  const seats = props.allocationAvailability?.seats
  if (!Array.isArray(seats)) return []
  return seats.filter((seat) => seat.isAvailable)
})

const hasValidAvailabilityCriteria = computed(() => {
  return (
    wantsSeatReplacement.value &&
    Boolean(form.allocationStartDate) &&
    Boolean(form.allocationEndDate) &&
    form.allocationEndDate >= form.allocationStartDate &&
    form.allocationEndDate >= today &&
    form.activeShifts.length > 0 &&
    getOverlappingSelectedShifts(form.activeShifts).length === 0
  )
})

const canChooseSeat = computed(() => {
  return (
    hasValidAvailabilityCriteria.value &&
    !props.isAvailabilityLoading &&
    !props.availabilityError &&
    availableSeatOptions.value.length > 0
  )
})

const seatPlaceholder = computed(() => {
  if (!form.allocationStartDate || !form.allocationEndDate) {
    return 'Select allocation dates first'
  }
  if (form.activeShifts.length === 0) return 'Select shifts first'
  if (getOverlappingSelectedShifts(form.activeShifts).length > 0) {
    return 'Selected shifts overlap'
  }
  if (props.isAvailabilityLoading) return 'Checking seat availability...'
  if (props.availabilityError) return 'Unable to load available seats'
  if (availableSeatOptions.value.length === 0) {
    return 'No seats available for this period'
  }
  return 'Select an available seat'
})

const availabilityMessage = computed(() => {
  if (!hasValidAvailabilityCriteria.value) {
    return 'Choose dates and non-overlapping shifts to load available seats.'
  }
  if (props.isAvailabilityLoading) return 'Checking current availability...'
  if (!props.allocationAvailability) return 'Availability has not been loaded.'
  const count = availableSeatOptions.value.length
  return `${count} seat${count === 1 ? '' : 's'} available for the selected period.`
})

watch(
  () => form.status,
  (status) => {
    if (status !== 'active') {
      if (isEditMode.value && form.allocationAction === 'replace') {
        form.allocationAction = 'keep'
      } else {
        form.assignSeat = false
      }
    }
  },
)

watch(
  () => form.joiningDate,
  (joiningDate, previousJoiningDate) => {
    if (
      !form.allocationStartDate ||
      form.allocationStartDate === previousJoiningDate
    ) {
      form.allocationStartDate = joiningDate
    }
  },
)

watch(
  [
    () => wantsSeatReplacement.value,
    () => form.allocationStartDate,
    () => form.allocationEndDate,
    () => [...form.activeShifts],
  ],
  () => {
    form.seatId = ''
    if (!hasValidAvailabilityCriteria.value) {
      emit('availability-clear')
      return
    }
    emit('availability-request', {
      shiftIds: [...form.activeShifts],
      startDate: form.allocationStartDate,
      endDate: form.allocationEndDate,
    })
  },
)

watch(
  () => props.allocationAvailability,
  () => {
    if (
      form.seatId &&
      !availableSeatOptions.value.some((seat) => seat.seatId === form.seatId)
    ) {
      form.seatId = ''
    }
  },
)

function clearErrors() {
  Object.keys(errors).forEach((key) => delete errors[key])
}

function validate() {
  clearErrors()
  if (!isRequired(form.firstName)) errors.firstName = 'First name is required.'
  if (!isRequired(form.lastName)) errors.lastName = 'Last name is required.'
  if (!isValidEmail(form.email)) errors.email = 'Enter a valid email address.'
  if (!isValidIndianPhone(form.phone)) errors.phone = 'Enter a valid 10-digit phone number.'
  if (form.guardianPhone && !isValidIndianPhone(form.guardianPhone)) {
    errors.guardianPhone = 'Enter a valid 10-digit phone number.'
  }
  if (!form.joiningDate) errors.joiningDate = 'Joining date is required.'
  if (!isNonNegativeNumber(form.feeAmount)) {
    errors.feeAmount = 'Monthly fee cannot be negative.'
  }
  if (
    isEditMode.value &&
    form.allocationAction === 'replace' &&
    !canAssignSeat.value
  ) {
    errors.allocationAction = 'Only active students can receive a seat allocation.'
  }
  if (hasAllocationChange.value && !isRequired(form.allocationChangeReason)) {
    errors.allocationChangeReason = 'Enter a reason for this allocation change.'
  }
  if (wantsSeatReplacement.value) {
    if (!form.allocationStartDate) {
      errors.allocationStartDate = 'Allocation start date is required.'
    } else if (
      form.joiningDate &&
      form.allocationStartDate < form.joiningDate
    ) {
      errors.allocationStartDate =
        'Allocation cannot start before the joining date.'
    }
    if (!form.allocationEndDate) {
      errors.allocationEndDate = 'Allocation end date is required.'
    } else if (
      form.allocationStartDate &&
      form.allocationEndDate < form.allocationStartDate
    ) {
      errors.allocationEndDate =
        'Allocation end date cannot be earlier than start date.'
    } else if (form.allocationEndDate < today) {
      errors.allocationEndDate =
        'A new seat allocation cannot end in the past.'
    }
    if (form.activeShifts.length === 0) {
      errors.activeShifts = 'Select at least one shift.'
    } else {
      const overlappingShifts = getOverlappingSelectedShifts(
        form.activeShifts,
      )
      if (overlappingShifts.length > 0) {
        errors.activeShifts =
          `${overlappingShifts[0].name} overlaps with ` +
          `${overlappingShifts[1].name}. Select non-overlapping shifts.`
      }
    }
    if (!form.seatId) {
      errors.seatId = 'Select an available seat.'
    } else if (
      !availableSeatOptions.value.some((seat) => seat.seatId === form.seatId)
    ) {
      errors.seatId = 'The selected seat is no longer available.'
    }
  }
  return Object.keys(errors).length === 0
}

function handleSubmit() {
  if (!validate()) {
    requestAnimationFrame(() => {
      document.querySelector('.form-field--error input')?.focus()
    })
    return
  }
  const payload = {
    enrollmentNumber: form.enrollmentNumber || undefined,
    firstName: form.firstName,
    lastName: form.lastName,
    email: form.email.toLowerCase(),
    phone: form.phone,
    address: form.address || null,
    guardianName: form.guardianName || null,
    guardianPhone: form.guardianPhone || null,
    dateOfBirth: form.dateOfBirth || null,
    preferredLanguage: form.preferredLanguage,
    joiningDate: form.joiningDate,
    feeAmount: Number(form.feeAmount),
    status: form.status,
    notes: form.notes || null,
  }
  if (!isEditMode.value) payload.sendInvitation = form.sendInvitation
  const allocation = {
    seatId: form.seatId,
    shiftIds: [...form.activeShifts],
    startDate: form.allocationStartDate,
    endDate: form.allocationEndDate,
    notes: form.allocationNotes || null,
  }
  if (!isEditMode.value && form.assignSeat) {
    payload.seatAllocation = allocation
  }
  if (isEditMode.value && form.allocationAction === 'replace') {
    payload.seatAllocationChange = {
      action: 'replace',
      allocation,
      reason: form.allocationChangeReason,
    }
  } else if (isEditMode.value && form.allocationAction === 'remove') {
    payload.seatAllocationChange = {
      action: 'remove',
      allocation: null,
      reason: form.allocationChangeReason,
    }
  }
  emit('submit', payload)
}

function currentAssignmentKey(assignment) {
  return [
    assignment.seatId,
    assignment.startDate,
    assignment.endDate,
    ...(assignment.shiftIds || []),
  ].join(':')
}

function clearSelectedShifts() {
  form.activeShifts = []
}

function getOverlappingSelectedShifts(shiftIds = []) {
  const selectedShifts = shiftIds
    .map((shiftId) => props.shifts.find((shift) => shift.id === shiftId))
    .filter(Boolean)

  for (let index = 0; index < selectedShifts.length; index += 1) {
    for (
      let compareIndex = index + 1;
      compareIndex < selectedShifts.length;
      compareIndex += 1
    ) {
      if (
        doShiftTimingsOverlap(
          selectedShifts[index],
          selectedShifts[compareIndex],
        )
      ) {
        return [selectedShifts[index], selectedShifts[compareIndex]]
      }
    }
  }
  return []
}
</script>

<style scoped>
.student-form { display: grid; gap: var(--space-5); }
.student-form__section { overflow: hidden; }
.student-form__section .card__header > div { display: grid; gap: var(--space-1); }
.student-form__grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-4); }
.student-form__full-row { grid-column: 1 / -1; }
.student-form__actions { display: flex; justify-content: flex-end; gap: var(--space-3); }
.student-form__invitation { grid-column: 1 / -1; align-items: flex-start; padding: var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-muted); }
.student-form__invitation span { display: grid; gap: var(--space-1); }
.student-form__invitation small { color: var(--color-text-muted); }
.student-form__allocation { display: grid; gap: var(--space-4); }
.student-form__current-assignments { display: grid; gap: var(--space-2); }
.student-form__current-assignment { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding: var(--space-3); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-muted); }
.student-form__current-assignment > div { display: grid; gap: var(--space-1); }
.student-form__empty-assignment { display: grid; gap: var(--space-1); padding: var(--space-4); border: 1px dashed var(--color-border); border-radius: var(--radius-md); }
.student-form__allocation-warning { margin: 0; }
.student-form__assignment-toggle { align-items: flex-start; padding: var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-muted); }
.student-form__assignment-toggle span, .student-form__shift-option span { display: grid; gap: var(--space-1); }
.student-form__assignment-toggle small, .student-form__shift-option small { color: var(--color-text-muted); }
.student-form__assignment-toggle--disabled { opacity: 0.72; }
.student-form__allocation-fields { padding-top: var(--space-2); border-top: 1px solid var(--color-divider); }
.student-form__field-header { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); }
.student-form__shift-options { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: var(--space-2); }
.student-form__shift-option { min-height: 54px; align-items: flex-start; padding: var(--space-3); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-elevated); }
.student-form__availability-error { color: var(--color-danger); }
.form-field--error .form-help { color: var(--color-danger); }
@media (max-width: 680px) {
  .student-form__grid { grid-template-columns: 1fr; }
  .student-form__full-row, .student-form__invitation { grid-column: auto; }
  .student-form__actions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .student-form__field-header { align-items: flex-start; flex-direction: column; }
  .student-form__current-assignment { align-items: flex-start; flex-direction: column; }
}
</style>
