<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="acs-overlay" @click.self="$emit('close')">
        <div class="acs-modal">
          <div class="acs-header">
            <div class="acs-header-left">
              <CalendarClock :size="16" class="acs-header-icon" />
              <span class="acs-title">Climate Schedule</span>
            </div>
            <button class="acs-close" @click="$emit('close')">&times;</button>
          </div>

          <div class="acs-body">
              <!-- Enable toggle -->
              <div class="acs-row">
                <span class="acs-label">Enabled</span>
                <button class="acs-toggle" :class="{ on: enabled }" @click="enabled = !enabled">
                  <span class="acs-toggle-dot" />
                </button>
              </div>

              <!-- Start time -->
              <div class="acs-row">
                <span class="acs-label">Start Time</span>
                <input type="time" v-model="startTime" class="acs-input" />
              </div>

              <!-- Temperature -->
              <div class="acs-row">
                <span class="acs-label">Temperature</span>
                <div class="acs-temp-control">
                  <button class="acs-step-btn" @click="temp = Math.max(16, temp - 1)">−</button>
                  <span class="acs-temp-value">{{ temp }}°C</span>
                  <button class="acs-step-btn" @click="temp = Math.min(32, temp + 1)">+</button>
                </div>
              </div>

              <!-- Fan Level -->
              <div class="acs-field">
                <span class="acs-label">Fan Level</span>
                <div class="acs-fan-control">
                  <button
                    v-for="lv in 7"
                    :key="lv"
                    class="acs-fan-btn"
                    :class="{ active: fan === lv }"
                    @click="fan = lv"
                  >{{ lv }}</button>
                </div>
              </div>

              <!-- Mode -->
              <div class="acs-field">
                <span class="acs-label">Mode</span>
                <div class="acs-mode-control">
                  <button v-for="m in modes" :key="m.value" class="acs-mode-btn" :class="{ active: mode === m.value }" @click="mode = m.value">
                    <component :is="m.icon" :size="14" />
                    <span>{{ m.label }}</span>
                  </button>
                </div>
              </div>

              <!-- Operate -->
              <div class="acs-field">
                <span class="acs-label">Operate</span>
                <div class="acs-mode-control">
                  <button class="acs-mode-btn" :class="{ active: operate === 'auto' }" @click="operate = 'auto'">Auto</button>
                  <button class="acs-mode-btn" :class="{ active: operate === 'manual' }" @click="operate = 'manual'">Manual</button>
                </div>
              </div>

              <!-- Circulation -->
              <div class="acs-field">
                <span class="acs-label">Circulation</span>
                <div class="acs-mode-control">
                  <button class="acs-mode-btn" :class="{ active: circle === 'in' }" @click="circle = 'in'">
                    <RotateCcw :size="14" />
                    <span>Recirculate</span>
                  </button>
                  <button class="acs-mode-btn" :class="{ active: circle === 'out' }" @click="circle = 'out'">
                    <Wind :size="14" />
                    <span>Fresh</span>
                  </button>
                </div>
              </div>

              <!-- Days of week -->
              <div class="acs-field">
                <span class="acs-label">Days</span>
                <div class="acs-days">
                  <button
                    v-for="d in dayOptions"
                    :key="d.value"
                    class="acs-day-btn"
                    :class="{ active: selectedDays.has(d.value) }"
                    @click="toggleDay(d.value)"
                  >{{ d.short }}</button>
                </div>
                <span class="acs-hint">Leave empty for one-time only</span>
              </div>

              <!-- Windshield -->
              <div class="acs-field">
                <span class="acs-label">Windshield</span>
                <div class="acs-mode-control">
                  <button class="acs-mode-btn" :class="{ active: wshld === '0' }" @click="wshld = '0'">Normal</button>
                  <button class="acs-mode-btn" :class="{ active: wshld === '1' }" @click="wshld = '1'">
                    <ThermometerSnowflake :size="14" />
                    <span>Defrost</span>
                  </button>
                </div>
              </div>

              <!-- Save -->
              <button
                class="acs-apply"
                :disabled="!!saving || !startTime"
                @click="save"
              >
                <Loader v-if="saving" :size="16" class="spinning" />
                <span v-else>Set Schedule</span>
              </button>

              <!-- Cancel all -->
              <button
                class="acs-delete"
                :disabled="!!saving"
                @click="cancelAll"
              >
                <Trash2 :size="14" />
                <span>Cancel All Schedules</span>
              </button>

              <div class="acs-footer-hint">
                Schedules are stored in the Leapmotor cloud and executed by the vehicle.
              </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import {
  CalendarClock, Loader, Snowflake, Flame, Wind, RotateCcw, ThermometerSnowflake, Trash2
} from 'lucide-vue-next'
import { api } from '../composables/useApi'

const props = defineProps({
  visible: Boolean,
  vin: String,
})

const emit = defineEmits(['close', 'saved'])

const enabled = ref(true)
const startTime = ref('07:00')
const temp = ref(24)
const fan = ref(3)
const mode = ref('wind')
const operate = ref('manual')
const circle = ref('out')
const wshld = ref('0')
const saving = ref(false)

const selectedDays = reactive(new Set([1, 2, 3, 4, 5]))

const modes = [
  { value: 'cold', label: 'Cool', icon: Snowflake },
  { value: 'hot', label: 'Heat', icon: Flame },
  { value: 'wind', label: 'Fan', icon: Wind },
]

const dayOptions = [
  { value: 0, short: 'Sun' },
  { value: 1, short: 'Mon' },
  { value: 2, short: 'Tue' },
  { value: 3, short: 'Wed' },
  { value: 4, short: 'Thu' },
  { value: 5, short: 'Fri' },
  { value: 6, short: 'Sat' },
]

function generateSetId() {
  // Format: "air_set" + deviceId + epochMs
  const epochMs = Date.now()
  const devicePart = Math.random().toString(36).substring(2, 10)
  return `air_set${devicePart}${epochMs}`
}

function formatStartTime(timeStr) {
  // Convert "HH:mm" to "yyyy-MM-dd HH:mm:00" using today's date
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d} ${timeStr}:00`
}

function toggleDay(val) {
  if (selectedDays.has(val)) selectedDays.delete(val)
  else selectedDays.add(val)
}

function resetForm() {
  enabled.value = true
  startTime.value = '07:00'
  temp.value = 24
  fan.value = 3
  mode.value = 'wind'
  operate.value = 'manual'
  circle.value = 'out'
  wshld.value = '0'
  selectedDays.clear()
  for (const d of [1, 2, 3, 4, 5]) selectedDays.add(d)
}

watch(() => props.visible, (val) => {
  if (val) resetForm()
})

async function save() {
  if (!props.vin) return
  saving.value = true
  try {
    const now = Date.now()
    const body = {
      controls: [{
        mode: mode.value,
        on: enabled.value ? '1' : '0',
        operate: operate.value,
        set_id: generateSetId(),
        start_time: formatStartTime(startTime.value),
        temperature: String(temp.value),
        update_time: String(now),
        windlevel: String(fan.value),
        days: Array.from(selectedDays).sort(),
        circle: circle.value,
        position: 'all',
        wshld: wshld.value,
      }],
    }
    await api('POST', `/api/vehicles/${props.vin}/ac-schedule`, body)
    emit('saved')
    emit('close')
  } catch (err) {
    alert('Failed to save schedule: ' + (err.message || err))
  } finally {
    saving.value = false
  }
}

async function cancelAll() {
  if (!props.vin) return
  if (!confirm('Cancel all climate schedules?')) return
  saving.value = true
  try {
    await api('DELETE', `/api/vehicles/${props.vin}/ac-schedule`)
    emit('saved')
    emit('close')
  } catch (err) {
    alert('Failed to cancel schedules: ' + (err.message || err))
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.acs-overlay {
  position: fixed; inset: 0; z-index: 9000;
  background: rgba(0,0,0,.55); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
}
.acs-modal {
  background: var(--card); border-radius: 16px; padding: 0;
  width: 92vw; max-width: 440px;
  box-shadow: 0 12px 40px rgba(0,0,0,.4); overflow: hidden;
  max-height: 90vh; overflow-y: auto;
}
.acs-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 1px solid rgba(255,255,255,.06);
  position: sticky; top: 0; background: var(--card); z-index: 1;
}
.acs-header-left { display: flex; align-items: center; gap: 8px; }
.acs-header-icon { color: #00d4ff; }
.acs-title { font-size: 15px; font-weight: 600; color: var(--text); }
.acs-close {
  background: none; border: none; color: var(--muted); font-size: 22px;
  cursor: pointer; padding: 0 4px; line-height: 1;
}
.acs-body { padding: 20px; display: flex; flex-direction: column; gap: 16px; }

/* Rows & Fields */
.acs-label { font-size: 13px; font-weight: 500; color: var(--text); }
.acs-row {
  display: flex; align-items: center; justify-content: space-between;
}
.acs-field { display: flex; flex-direction: column; gap: 8px; }
.acs-hint { font-size: 11px; color: var(--muted2); }

.acs-input {
  padding: 8px 12px; border: 1px solid rgba(255,255,255,.1); border-radius: 10px;
  background: var(--bg); color: var(--text); font-size: 14px;
  outline: none; transition: border-color .2s;
}
.acs-input:focus { border-color: #00d4ff; }

/* Temperature */
.acs-temp-control { display: flex; align-items: center; gap: 10px; }
.acs-step-btn {
  width: 32px; height: 32px; border: 1px solid rgba(255,255,255,.08); border-radius: 10px;
  background: var(--bg); color: var(--text); cursor: pointer;
  font-size: 18px; display: flex; align-items: center; justify-content: center;
  transition: border-color .2s;
}
.acs-step-btn:hover { border-color: #00d4ff; }
.acs-temp-value { font-size: 18px; font-weight: 700; color: var(--text); min-width: 56px; text-align: center; }

/* Fan */
.acs-fan-control { display: flex; gap: 6px; }
.acs-fan-btn {
  flex: 1; padding: 8px 0; border: 1px solid rgba(255,255,255,.08); border-radius: 8px;
  background: var(--bg); color: var(--muted); cursor: pointer;
  font-size: 13px; font-weight: 600; transition: all .2s; text-align: center;
}
.acs-fan-btn.active {
  border-color: #00d4ff; color: #00d4ff;
  background: rgba(0,212,255,.1);
}

/* Mode / Operate buttons */
.acs-mode-control { display: flex; gap: 6px; }
.acs-mode-btn {
  flex: 1; padding: 8px; border: 1px solid rgba(255,255,255,.08); border-radius: 10px;
  background: var(--bg); color: var(--muted); cursor: pointer;
  font-size: 12px; font-weight: 600; transition: all .2s;
  display: flex; align-items: center; justify-content: center; gap: 4px;
}
.acs-mode-btn.active {
  border-color: #00d4ff; color: #00d4ff;
  background: rgba(0,212,255,.1);
}

/* Days */
.acs-days { display: flex; gap: 6px; }
.acs-day-btn {
  flex: 1; padding: 8px 0; border: 1px solid rgba(255,255,255,.08); border-radius: 8px;
  background: var(--bg); color: var(--muted); cursor: pointer;
  font-size: 11px; font-weight: 600; transition: all .2s; text-align: center;
}
.acs-day-btn.active {
  border-color: #00d4ff; color: #00d4ff;
  background: rgba(0,212,255,.08);
}

/* Toggle */
.acs-toggle {
  width: 44px; height: 24px; border-radius: 12px; border: none;
  background: rgba(255,255,255,.1); cursor: pointer;
  position: relative; transition: background .2s; padding: 0;
}
.acs-toggle.on { background: #00e676; }
.acs-toggle-dot {
  position: absolute; top: 3px; left: 3px;
  width: 18px; height: 18px; border-radius: 50%;
  background: #fff; transition: transform .2s;
  box-shadow: 0 1px 3px rgba(0,0,0,.3);
}
.acs-toggle.on .acs-toggle-dot { transform: translateX(20px); }

/* Apply */
.acs-apply {
  width: 100%; padding: 12px; border: none; border-radius: 10px;
  background: linear-gradient(135deg, #00d4ff, #7c6aff);
  color: #fff; font-weight: 600; font-size: 14px;
  cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px;
  transition: opacity .2s;
}
.acs-apply:hover { opacity: 0.9; }
.acs-apply:disabled { opacity: 0.5; cursor: not-allowed; }

.acs-delete {
  width: 100%; padding: 10px; border: 1px solid rgba(255,80,80,.3); border-radius: 10px;
  background: transparent; color: #ff5050; font-weight: 600; font-size: 13px;
  cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px;
  transition: all .2s;
}
.acs-delete:hover { background: rgba(255,80,80,.1); }
.acs-delete:disabled { opacity: 0.5; cursor: not-allowed; }

.acs-footer-hint {
  font-size: 11px; color: var(--muted2); text-align: center;
  line-height: 1.5; padding-top: 4px;
}

.acs-loading {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 32px 0; color: var(--muted);
}

.modal-enter-active, .modal-leave-active { transition: opacity .2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }

@keyframes lm-spin { to { transform: rotate(360deg); } }
.spinning { animation: lm-spin .7s linear infinite; }
</style>
