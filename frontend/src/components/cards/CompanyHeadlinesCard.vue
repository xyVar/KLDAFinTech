<template>
  <q-card flat bordered class="full-height">
    <q-card-section class="text-h6">📢 Company Headlines</q-card-section>
    <q-separator />

    <q-scroll-area class="q-pa-sm" style="height: calc(100% - 50px);">
      <q-list>
        <q-item v-for="(item, index) in headlines" :key="index" clickable>
          <q-item-section>
            <q-item-label>{{ item.title }}</q-item-label>
            <q-item-label caption>{{ item.source }} — {{ item.time }}</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </q-scroll-area>
  </q-card>
</template>

<script>
export default {
  name: 'CompanyHeadlinesCard',
  data() {
    return {
      headlines: [
        {
          title: 'NVIDIA unveils new AI chip at developer event',
          source: 'Bloomberg',
          time: 'Mar 21, 2025 14:45'
        },
        {
          title: 'Intel delays earnings report amid audit',
          source: 'CNBC',
          time: 'Mar 21, 2025 11:20'
        },
        {
          title: 'AMD gains on positive semiconductor forecast',
          source: 'TipRanks',
          time: 'Mar 20, 2025 09:00'
        }
      ]
    }
  }
}
</script>
