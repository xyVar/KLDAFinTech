<template>
  <q-page padding class="q-pa-xl">
    <div class="q-gutter-md text-center">

      <h1 class="text-primary text-h3">Transparent Company Insights</h1>
      <p class="text-subtitle1">
        We are a research-focused platform offering real-time intelligence, news logs, and event tracking
        on public companies — built for investigative transparency, not financial advice.
      </p>

      <q-separator spaced />

      <h2 class="text-h5 text-weight-bold">Our Mission</h2>
      <p>
        To make publicly available company data more accessible, structured, and traceable.
        We source, log, and deliver credible information — helping professionals, journalists, and curious minds
        better understand market-moving events and disclosures.
      </p>

      <q-separator spaced />

      <h2 class="text-h5 text-weight-bold">Our Data Sources</h2>
      <p>
        We gather and organize information from licensed data providers including:
        <strong>Bloomberg, CNBC, TipRanks, SEC filings, official investor relations pages</strong>,
        and verified financial news outlets. All content is cited properly with original sources.
      </p>

      <q-separator spaced />

      <h2 class="text-h5 text-weight-bold">Who It's For</h2>
      <p>
        This platform is designed for researchers, analysts, journalists, and anyone
        looking to explore companies in depth — based on reliable, timestamped event logs.
      </p>

      <q-separator spaced />

      <q-btn label="Register for Access" to="/register" color="primary" size="lg" class="q-mt-md" />

    </div>
  </q-page>
</template>

<script>
export default {
  name: 'LandingPage'
}
</script>
