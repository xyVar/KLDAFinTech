<template>
    <div>
        <h2>Real-Time Stock Prices</h2>
        <div v-if="priceData">
            <p><strong>{{ priceData.symbol }}</strong>: ${{ priceData.price }}</p>
            <p>Updated at: {{ priceData.timestamp }}</p>
        </div>
        <p v-else>Waiting for data...</p>
    </div>
</template>

<script>
    export default {
        data() {
            return {
                priceData: null,
            };
        },
        mounted() {
            console.log("Connecting to WebSocket...");
            this.socket = new WebSocket("ws://localhost:8080");

            this.socket.onopen = () => console.log("WebSocket Connected!");

            this.socket.onmessage = (event) => {
                console.log("WebSocket Message:", event.data);
                this.priceData = JSON.parse(event.data);
            };

            this.socket.onerror = (error) => console.error("WebSocket Error:", error);

            this.socket.onclose = () => console.log("WebSocket Disconnected");
        },
        beforeUnmount() {
            if (this.socket) {
                this.socket.close();
            }
        },
    };
</script>
