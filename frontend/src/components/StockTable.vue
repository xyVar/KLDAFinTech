<template>
    <div>
        <h2>Stock Data for {{ symbol }}</h2>
        <input v-model="symbol" placeholder="Enter stock symbol" @keyup.enter="fetchData" />
        <button @click="fetchData">Fetch Data</button>

        <table v-if="stockData.length">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Open</th>
                    <th>High</th>
                    <th>Low</th>
                    <th>Close</th>
                    <th>Volume</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="stock in stockData" :key="stock.date">
                    <td>{{ new Date(stock.date).toLocaleDateString() }}</td>
                    <td>{{ stock.open }}</td>
                    <td>{{ stock.high }}</td>
                    <td>{{ stock.low }}</td>
                    <td>{{ stock.close }}</td>
                    <td>{{ stock.volume }}</td>
                </tr>
            </tbody>
        </table>
    </div>
</template>

<script>
import { fetchStockData } from "../StockService.js";

export default {
  data() {
    return {
      symbol: "NVDA",
      stockData: [],
    };
  },
  methods: {
    async fetchData() {
      this.stockData = await fetchStockData(this.symbol);
    },
  },
  mounted() {
    this.fetchData();
  },
};
</script>

<style>
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
    }

    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: center;
    }

    th {
        background-color: #f4f4f4;
    }
</style>
