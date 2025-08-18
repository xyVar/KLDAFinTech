<template>
  <q-page padding>
    <q-header elevated>
      <q-toolbar>
        <q-toolbar-title>Menu</q-toolbar-title>
        <q-btn flat label="SIGN UP" />
        <q-btn flat label="SIGN IN" />
      </q-toolbar>
    </q-header>

    <div class="q-pa-md full-height">
      <q-splitter v-model="splitterModel" style="height: calc(100vh - 60px);">

        <!-- LEFT SIDE: Tables & Tabs -->
        <template v-slot:before>
          <q-tabs v-model="tab" dense class="text-grey">
            <q-tab name="general" label="GENERAL SYMBOLS" />
            <q-tab name="watchlist" label="MY WATCHLIST" />
          </q-tabs>

          <q-tab-panels v-model="tab" animated class="full-height">
            <q-tab-panel name="general">
              <q-table dense
                       flat
                       :columns="generalColumns"
                       :rows="generalRows"
                       row-key="ticker"
                       @row-click="selectSymbol">
                <template v-slot:body-cell-watch="props">
                  <q-td class="text-center">
                    <q-checkbox v-model="props.row.watch"
                                @update:model-value="toggleWatch(props.row)" />
                  </q-td>
                </template>
              </q-table>
            </q-tab-panel>

            <q-tab-panel name="watchlist">
              <q-table dense
                       flat
                       :columns="watchlistColumns"
                       :rows="watchlistRows"
                       row-key="ticker"
                       @row-click="selectSymbol" />
            </q-tab-panel>
          </q-tab-panels>
        </template>

        <!-- RIGHT SIDE: Chart & Cards -->
        <template v-slot:after>
          <div class="column full-height">
            <!-- TOP 33%: Stock Chart -->
            <div class="col q-pa-xs" style="height:33%">
              <StockChart :symbol="selectedSymbol" />
            </div>

            <!-- MIDDLE 33%: Company Headlines + Earnings Releases -->
            <div class="col q-pa-xs" style="height:33%">
              <div class="row full-height">
                <div class="col-6 q-pa-xs">
                  <CompanyHeadlinesCard />
                </div>
                <div class="col-6 q-pa-xs">
                  <EarningsReleasesCard />
                </div>
              </div>
            </div>

            <!-- BOTTOM 34%: Market Expectation + Economic Calendar -->
            <div class="col q-pa-xs" style="height:34%">
              <div class="row full-height">
                <div class="col-6 q-pa-xs">
                  <MarketExpectationCard />
                </div>
                <div class="col-6 q-pa-xs">
                  <EconomicCalendarCard />
                </div>
              </div>
            </div>
          </div>
        </template>

      </q-splitter>
    </div>
  </q-page>
</template>

<script>
  import { defineComponent } from 'vue'
  import axios from 'axios'
  import StockChart from 'src/components/StockChart.vue'

  // 1) Import the 4 new card components
  import CompanyHeadlinesCard from 'components/cards/CompanyHeadlinesCard.vue'
  import EarningsReleasesCard from 'components/cards/EarningsReleasesCard.vue'
  import MarketExpectationCard from 'components/cards/MarketExpectationCard.vue'
  import EconomicCalendarCard from 'components/cards/EconomicCalendarCard.vue'

  export default defineComponent({
    name: 'IndexPage',
    components: {
      StockChart,
      CompanyHeadlinesCard,
      EarningsReleasesCard,
      MarketExpectationCard,
      EconomicCalendarCard
    },
    data() {
      return {
        splitterModel: 30,
        tab: 'general',
        selectedSymbol: '',
        generalColumns: [
          { name: 'ticker', label: 'Ticker', field: 'ticker' },
          { name: 'open', label: 'Open', field: 'open' },
          { name: 'high', label: 'High', field: 'high' },
          { name: 'low', label: 'Low', field: 'low' },
          { name: 'close', label: 'Close', field: 'close' },
          { name: 'volume', label: 'Volume', field: 'volume' },
          { name: 'trades', label: 'Trades', field: 'trades' },
          { name: 'watch', label: 'Watch', field: 'watch' }
        ],
        generalRows: [],
        watchlistColumns: [
          { name: 'ticker', label: 'Ticker', field: 'ticker' },
          { name: 'open', label: 'Open', field: 'open' },
          { name: 'high', label: 'High', field: 'high' },
          { name: 'low', label: 'Low', field: 'low' },
          { name: 'close', label: 'Close', field: 'close' },
          { name: 'volume', label: 'Volume', field: 'volume' },
          { name: 'trades', label: 'Trades', field: 'trades' }
        ],
        watchlistRows: []
      }
    },
    created() {
      this.loadAssets()
    },
    methods: {
      async loadAssets() {
        const { data } = await axios.get('http://localhost:5000/api/assets')
        this.generalRows = data
      },
      toggleWatch(row) {
        if (row.watch) {
          this.watchlistRows.push(row)
        } else {
          const idx = this.watchlistRows.indexOf(row)
          if (idx !== -1) {
            this.watchlistRows.splice(idx, 1)
          }
        }
      },
      selectSymbol(_, row) {
        this.selectedSymbol = row.ticker
      }
    }
  })
</script>

<style>
  .full-height {
    height: 100%;
  }
</style>
