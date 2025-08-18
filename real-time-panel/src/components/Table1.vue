<template>
    <div class="table1-container">
        <!-- Menu button on the left -->
        <button class="menu-button">Menu</button>

        <!-- Sign In / Sign Up buttons on the right -->
        <div class="auth-buttons">
            <button @click="signIn">Sign In</button>
            <button @click="signUp">Sign Up</button>
        </div>
    </div>
</template>

<script>
    export default {
        name: "Table1",
        methods: {
            signIn() {
                alert("Sign In clicked");
            },
            signUp() {
                alert("Sign Up clicked");
            }
        }
    };
</script>

<style scoped>
    .table1-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px;
    }

    .menu-button {
        background-color: #007bff;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
    }

    .auth-buttons button {
        background-color: #28a745;
        color: white;
        padding: 10px 20px;
        margin-left: 10px;
        border: none;
        border-radius: 5px;
    }
</style>
