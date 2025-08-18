<template>
    <div class="table-container">
        <table class="styled-table">
            <thead>
                <tr>
                    <th>Asset</th>
                    <th>Current Price</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="stock in stocks" :key="stock.asset_symbol">
                    <td>{{ stock.asset_symbol }}</td>
                    <td>{{ stock.current_price }}</td>
                </tr>
            </tbody>
        </table>
    </div>
</template>

<script>
    export default {
        data() {
            return {
                stocks: [
                    { asset_symbol: "Asset 1", current_price: "427.27" },
                    { asset_symbol: "Asset 2", current_price: "239.92" },
                    { asset_symbol: "Asset 3", current_price: "639.92" },
                    { asset_symbol: "Asset 4", current_price: "640.54" },
                    { asset_symbol: "Asset 5", current_price: "566.46" },
                    { asset_symbol: "Asset 6", current_price: "511.85" },
                    { asset_symbol: "Asset 7", current_price: "187.46" },
                    { asset_symbol: "Asset 8", current_price: "645.17" },
                    { asset_symbol: "Asset 9", current_price: "945.16" },
                    { asset_symbol: "Asset 10", current_price: "869.00" },
                    { asset_symbol: "Asset 11", current_price: "402.29" },
                    { asset_symbol: "Asset 12", current_price: "504.02" },
                    { asset_symbol: "Asset 13", current_price: "191.76" },
                    { asset_symbol: "Asset 14", current_price: "228.16" },
                    { asset_symbol: "Asset 15", current_price: "561.74" },
                    { asset_symbol: "Asset 16", current_price: "729.61" }
                ]
            };
        }
    };
</script>

<style scoped>
    /* Table2 Full Width */
    .table-container {
        width: 100%;
        max-height: 600px;
        overflow-y: auto;
    }

    /* Table Styling */
    .styled-table {
        width: 100%;
        border-collapse: collapse;
    }

        .styled-table th, .styled-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }

        .styled-table thead {
            background-color: #f4f4f4;
            position: sticky;
            top: 0;
        }
</style>
