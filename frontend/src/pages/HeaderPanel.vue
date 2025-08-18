<template>
  <q-page padding>
    <q-header elevated>
      <q-toolbar>
        <q-toolbar-title>Menu</q-toolbar-title>
        <q-btn flat label="SIGN UP" @click="showSignUp = true" />
        <q-btn flat label="SIGN IN" @click="showSignIn = true" />
      </q-toolbar>
    </q-header>

    <div class="q-pa-md full-height">
      <q-splitter v-model="splitterModel" style="height: calc(100vh - 60px);">
        <template v-slot:before>
          <q-tabs v-model="tab" dense class="text-grey">
            <q-tab name="general" label="GENERAL SYMBOLS" />
            <q-tab name="watchlist" label="MY WATCHLIST" />
          </q-tabs>

          <q-tab-panels v-model="tab" animated class="full-height">
            <q-tab-panel name="general">
              <q-table dense flat :columns="generalColumns" :rows="generalRows" row-key="ticker">
                <template v-slot:body-cell-watch="props">
                  <q-td class="text-center">
                    <q-checkbox v-model="props.row.watch" @update:model-value="toggleWatch(props.row)" />
                  </q-td>
                </template>
              </q-table>
            </q-tab-panel>

            <q-tab-panel name="watchlist">
              <q-table dense flat :columns="watchlistColumns" :rows="watchlistRows" row-key="ticker" />
            </q-tab-panel>
          </q-tab-panels>
        </template>

        <template v-slot:after>
          <div class="column full-height">
            <div class="col q-pa-xs" style="height:33%">
              <q-card flat bordered class="full-height">
                <q-card-section class="text-h6">📊 Chart Placeholder</q-card-section>
              </q-card>
            </div>
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

    <q-dialog v-model="showSignUp">
      <q-card style="min-width: 400px">
        <q-card-section><div class="text-h6">Create an Account</div></q-card-section>
        <q-card-section>
          <q-input filled v-model="signUpForm.email" label="Email" />
          <q-input filled v-model="signUpForm.password" label="Password" type="password" />
          <q-input filled v-model="signUpForm.confirm" label="Confirm Password" type="password" />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn label="Sign Up" color="primary" @click="submitSignUp" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <q-dialog v-model="showSignIn">
      <q-card style="min-width: 400px">
        <q-card-section><div class="text-h6">Sign In</div></q-card-section>
        <q-card-section>
          <q-input filled v-model="signInForm.email" label="Email" />
          <q-input filled v-model="signInForm.password" label="Password" type="password" />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn label="Sign In" color="primary" @click="submitSignIn" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script>
import CompanyHeadlinesCard from 'components/cards/CompanyHeadlinesCard.vue';
import EarningsReleasesCard from 'components/cards/EarningsReleasesCard.vue';
import MarketExpectationCard from 'components/cards/MarketExpectationCard.vue';
import EconomicCalendarCard from 'components/cards/EconomicCalendarCard.vue';

export default {
  name: 'HeaderPanel',
  components: {
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
      showSignUp: false,
      showSignIn: false,
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
      watchlistRows: [],
      signUpForm: {
        email: '',
        password: '',
        confirm: ''
      },
      signInForm: {
        email: '',
        password: ''
      }
    }
  },
  methods: {
    toggleWatch(row) {
      row.watch
        ? this.watchlistRows.push(row)
        : this.watchlistRows.splice(this.watchlistRows.indexOf(row), 1);
    },
    submitSignUp() {
      if (this.signUpForm.password !== this.signUpForm.confirm) {
        this.$q.notify({ type: 'negative', message: 'Passwords do not match' });
        return;
      }
      this.$q.notify({ type: 'positive', message: 'Signed up successfully!' });
      this.showSignUp = false;
    },
    submitSignIn() {
      this.$q.notify({ type: 'positive', message: 'Signed in successfully!' });
      this.showSignIn = false;
    }
  }
}
</script>

<style>
.full-height {
  height: 100%;
}
</style>
