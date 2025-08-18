<template>
  <q-card flat bordered class="full-height">
    <q-card-section class="full-height">
      <canvas ref="chartCanvas"></canvas>
    </q-card-section>
  </q-card>
</template>

<script>
  import { defineComponent, ref, watch, onMounted } from "vue";
  import Chart from "chart.js/auto";
  import axios from "axios";

  export default defineComponent({
    props: {
      symbol: String, // Selected stock ticker
    },
    setup(props) {
      const chartCanvas = ref(null);
      let chartInstance = null;

      const fetchChartData = async (symbol) => {
        if (!symbol) return;

        try {
          const response = await axios.get(`http://localhost:5000/api/price-history/${symbol}`);
          const data = response.data;

          const labels = data.map(entry => entry.date);
          const prices = data.map(entry => entry.close);

          if (chartInstance) {
            chartInstance.destroy();
          }

          chartInstance = new Chart(chartCanvas.value, {
            type: "line",
            data: {
              labels,
              datasets: [
                {
                  label: `${symbol} Closing Prices`,
                  data: prices,
                  borderColor: "blue",
                  backgroundColor: "rgba(0, 0, 255, 0.1)",
                  tension: 0.3,
                  fill: true,
                },
              ],
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              scales: {
                x: {
                  title: { display: true, text: "Date" },
                  ticks: { maxRotation: 45, minRotation: 20 }
                },
                y: {
                  title: { display: true, text: "Close Price" }
                }
              }
            },
          });
        } catch (error) {
          console.error("Error fetching chart data:", error);
        }
      };

      onMounted(() => {
        fetchChartData(props.symbol);
      });

      watch(() => props.symbol, (newSymbol) => {
        fetchChartData(newSymbol);
      });

      return { chartCanvas };
    },
  });
</script>

<style>
  .full-height {
    height: 100%;
  }
</style>
