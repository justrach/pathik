const { ChartJSNodeCanvas } = require('chartjs-node-canvas');
const fs = require('fs');
const path = require('path');

async function createMemoryComparisonChart() {
    // Configuration for the chart
    const width = 800;
    const height = 400;
    const chartCallback = (ChartJS) => {
        // Optional callback to customize Chart.js instance
        ChartJS.defaults.font.family = 'Arial';
        ChartJS.defaults.font.size = 16;
    };

    // Create canvas
    const chartJSNodeCanvas = new ChartJSNodeCanvas({ width, height, chartCallback });

    // Actual memory usage for example.com from the benchmark data
    const pathikMemory = 0.45; // MB for example.com
    const playwrightMemory = 4.64; // MB for example.com
    
    // Calculate the ratio
    const ratio = Math.round(playwrightMemory / pathikMemory);
    
    // Chart configuration
    const configuration = {
        type: 'bar',
        data: {
            labels: ['Memory Usage for example.com'],
            datasets: [
                {
                    label: 'Pathik',
                    data: [pathikMemory.toFixed(2)],
                    backgroundColor: 'rgba(54, 162, 235, 0.8)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Playwright',
                    data: [playwrightMemory.toFixed(2)],
                    backgroundColor: 'rgba(255, 99, 132, 0.8)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            plugins: {
                title: {
                    display: true,
                    text: `Memory usage - ${ratio}x less`,
                    font: {
                        size: 24
                    },
                    padding: 20
                },
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Memory Usage (MB)'
                    }
                }
            }
        }
    };

    // Render the chart
    const imageBuffer = await chartJSNodeCanvas.renderToBuffer(configuration);
    
    // Save the image
    const outputDir = path.join(__dirname, 'results');
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }
    
    const outputPath = path.join(outputDir, 'memory-comparison.png');
    fs.writeFileSync(outputPath, imageBuffer);
    
    console.log(`Chart saved to: ${outputPath}`);
    console.log(`Memory usage for example.com: Pathik ${pathikMemory.toFixed(2)}MB vs Playwright ${playwrightMemory.toFixed(2)}MB`);
    console.log(`For example.com, Playwright uses ${ratio}x more memory than Pathik`);
}

createMemoryComparisonChart().catch(console.error); 