<template>
    <div class="dashboard-container">
        <div class="top-bar">
            <button class="menu-button">Menu</button>
            <div class="auth-buttons">
                <button class="sign-in">Sign In</button>
                <button class="sign-up">Sign Up</button>
            </div>
        </div>

        <div class="content-layout">
            <!-- Left Sidebar: Table1 (Menu) + Table2 (Asset List) -->
            <div class="left-sidebar">
                <div class="menu-panel">
                    <Table1 />
                </div>
                <div class="table2-container">
                    <Table2 />
                </div>
            </div>

            <!-- Right Side: Tables 3-7 -->
            <div class="right-panel">
                <div class="grid-container">
                    <div class="chart-box"><Table3 /></div>
                    <div class="table-box"><Table4 /></div>
                    <div class="table-box"><Table5 /></div>
                    <div class="table-box"><Table6 /></div>
                    <div class="table-box"><Table7 /></div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
    import Table1 from "../components/Table1.vue";
    import Table2 from "../components/Table2.vue";
    import Table3 from "../components/Table3.vue";
    import Table4 from "../components/Table4.vue";
    import Table5 from "../components/Table5.vue";
    import Table6 from "../components/Table6.vue";
    import Table7 from "../components/Table7.vue";

    export default {
        components: {
            Table1,
            Table2,
            Table3,
            Table4,
            Table5,
            Table6,
            Table7
        }
    };
</script>

<style scoped>
    /* Full Page Layout */
    .dashboard-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 10px;
        width: 100%;
    }

    /* Top Bar (Menu + Auth Buttons) */
    .top-bar {
        display: flex;
        justify-content: space-between;
        width: 100%;
        padding: 10px;
    }

    .menu-button {
        background-color: blue;
        color: white;
        border: none;
        padding: 8px 12px;
        cursor: pointer;
    }

    .auth-buttons {
        display: flex;
        gap: 10px;
    }

    .sign-in, .sign-up {
        background-color: green;
        color: white;
        border: none;
        padding: 8px 12px;
        cursor: pointer;
    }

    /* Layout Wrapper */
    .content-layout {
        display: flex;
        width: 100%;
        gap: 15px;
    }

    /* Left Sidebar (Menu + Table2) */
    .left-sidebar {
        display: flex;
        flex-direction: column;
        width: 300px;
    }

    .menu-panel {
        height: 60px;
        background-color: white;
        border: 1px solid #ddd;
    }

    /* Table2 Placement */
    .table2-container {
        flex: 1;
        overflow-y: auto;
    }

    /* Right Panel (Tables 3-7) */
    .right-panel {
        flex: 3;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    /* Grid Layout for Tables 3-7 */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        width: 100%;
    }

    /* Individual table boxes */
    .table-box, .chart-box {
        background: white;
        border-radius: 6px;
        padding: 10px;
        box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
</style>
