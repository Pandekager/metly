<template>
  <div class="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6">
    <h3 class="text-xl font-semibold mb-4 text-slate-900 dark:text-slate-100">
        Kunde fordeling på kort
    </h3>
    <div class="h-96">
      <l-map
        ref="mapRef"
        :zoom="6"
        :center="[56.2639, 9.5018]"
        style="height: 100%; width: 100%; z-index: 1;"
        @ready="onMapReady"
      >
        <l-tile-layer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="&copy; OpenStreetMap contributors"
        />
        <l-circle-marker
          v-for="city in analyticsData"
          :key="city.city"
          :lat-lng="[city.latitude, city.longitude]"
          :radius="getMarkerRadius(city.customer_count)"
          :color="getRevenueColor(city.revenue)"
          :fill-color="getRevenueColor(city.revenue)"
          :fill-opacity="0.6"
        >
          <l-popup>
            <div class="text-slate-900">
              <strong>{{ city.city }}</strong><br>
              Kunder: {{ city.customer_count }}<br>
              Omsætning: {{ formatCurrency(city.revenue) }}
            </div>
          </l-popup>
        </l-circle-marker>
      </l-map>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { LMap, LTileLayer, LCircleMarker, LPopup } from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'

// Fix for Leaflet import issue
import * as L from 'leaflet'

// Workaround for Leaflet's automatic CSS import issue
if (typeof window !== 'undefined') {
  const leafletModule = L as typeof L & {
    Default?: {
      prototype?: {
        _initHooks?: unknown
      }
    }
  }

  if (leafletModule.Default?.prototype?._initHooks) {
    delete leafletModule.Default.prototype._initHooks
  }
}

interface CityData {
  city: string
  customer_count: number
  revenue: number
  latitude: number
  longitude: number
}

const props = defineProps<{
  data: CityData[]
}>()

const mapRef = ref<any>(null)

const analyticsData = computed(() => {
  return props.data.filter(city => city.latitude !== 0 && city.longitude !== 0)
})

const getMarkerRadius = (customerCount: number) => {
  // Scale radius between 5 and 25 based on customer count
  const max = Math.max(customerCount, 1)
  return 5 + (customerCount / max) * 20
}

const getRevenueColor = (revenue: number) => {
  // Color gradient from light green to dark green based on revenue
  const max = Math.max(...analyticsData.value.map(c => c.revenue), 1)
  const normalized = revenue / max
  // Use green shades: light (low revenue) to dark (high revenue)
  const intensity = Math.floor(normalized * 155 + 100)
  return `rgb(0, ${intensity}, 0)`
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('da-DK', {
    style: 'currency',
    currency: 'DKK',
    maximumFractionDigits: 0
  }).format(value)
}

const onMapReady = () => {
  console.log('Map ready')
}

onMounted(() => {
  // Force Leaflet to update if container becomes visible
  if (mapRef.value) {
    setTimeout(() => {
      mapRef.value?.leafletObject?.invalidateSize()
    }, 100)
  }
})

</script>

<style>
.leaflet-popup-content-wrapper {
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.leaflet-popup-content {
  margin: 12px;
  font-size: 14px;
}
</style>
