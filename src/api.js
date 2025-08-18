export async function fetchAssets() {
    try {
        const response = await fetch("http://localhost:5000/api/assets");
        if (!response.ok) {
            throw new Error("Failed to fetch assets");
        }
        return await response.json();
    } catch (error) {
        console.error("Error fetching assets:", error);
        return [];
    }
}
