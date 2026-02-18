#!/usr/bin/env node

const http = require('http');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

const PORT = 3000;

const apps = [
    'blackjack21', 'keno4card', 'keno20card', 'kenocasino',
    'kenosuper4x', 'roulette', 'vintageslots', 'videopokercasino', 'multihandpoker'
];

// Cache to avoid hammering GitHub API
let cache = {};
let lastFetch = {};

async function getBuildStatus(app) {
    // Return cached data if less than 30 seconds old
    if (cache[app] && lastFetch[app] && (Date.now() - lastFetch[app] < 30000)) {
        return cache[app];
    }

    return new Promise((resolve) => {
        const cmd = `gh run list --repo LuckyJackpotCasino/${app} --limit 10 --json status,conclusion,displayTitle,databaseId,workflowName 2>/dev/null`;
        
        exec(cmd, (error, stdout, stderr) => {
            if (error) {
                console.error(`Error fetching ${app}:`, error.message);
                resolve({ ios: 'pending', aab: 'pending', amazon: 'pending', windows: 'pending' });
                return;
            }

            try {
                const runs = JSON.parse(stdout);
                const result = {
                    ios: 'pending',
                    aab: 'pending',
                    amazon: 'pending',
                    windows: 'pending',
                    iosRun: null,
                    aabRun: null,
                    amazonRun: null,
                    windowsRun: null
                };

                // Find most recent run for each platform
                runs.forEach(run => {
                    const title = run.displayTitle.toLowerCase();
                    const status = run.status === 'completed' ? run.conclusion : run.status;
                    
                    // Determine platform based on title or workflow
                    if (!result.iosRun && (title.includes('ios') || run.workflowName.includes('iOS'))) {
                        result.ios = status;
                        result.iosRun = run.databaseId;
                    }
                    if (!result.aabRun && (title.includes('aab') || title.includes('google'))) {
                        result.aab = status;
                        result.aabRun = run.databaseId;
                    }
                    if (!result.amazonRun && title.includes('amazon')) {
                        result.amazon = status;
                        result.amazonRun = run.databaseId;
                    }
                    if (!result.windowsRun && (title.includes('windows') || run.workflowName.includes('Windows'))) {
                        result.windows = status;
                        result.windowsRun = run.databaseId;
                    }
                });

                cache[app] = result;
                lastFetch[app] = Date.now();
                resolve(result);
            } catch (parseError) {
                console.error(`Error parsing ${app} data:`, parseError.message);
                resolve({ ios: 'pending', aab: 'pending', amazon: 'pending', windows: 'pending' });
            }
        });
    });
}

const server = http.createServer(async (req, res) => {
    // Enable CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }

    // Serve dashboard HTML
    if (req.url === '/' || req.url === '/dashboard') {
        fs.readFile(path.join(__dirname, 'dashboard.html'), (err, data) => {
            if (err) {
                res.writeHead(500);
                res.end('Error loading dashboard');
                return;
            }
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(data);
        });
        return;
    }

    // API endpoint for individual app status
    const statusMatch = req.url.match(/^\/status\/(.+)$/);
    if (statusMatch) {
        const app = statusMatch[1];
        if (apps.includes(app)) {
            const status = await getBuildStatus(app);
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify(status));
        } else {
            res.writeHead(404, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'App not found' }));
        }
        return;
    }

    // API endpoint for all apps status
    if (req.url === '/status' || req.url === '/api/status') {
        const results = {};
        for (const app of apps) {
            results[app] = await getBuildStatus(app);
        }
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(results));
        return;
    }

    // 404
    res.writeHead(404);
    res.end('Not found');
});

server.listen(PORT, () => {
    console.log(`
╔═══════════════════════════════════════════════════════════╗
║   🎰 Lucky Jackpot Casino - Build Dashboard Server       ║
╠═══════════════════════════════════════════════════════════╣
║                                                            ║
║   Dashboard: http://localhost:${PORT}                     ║
║   API:       http://localhost:${PORT}/api/status          ║
║                                                            ║
║   Press Ctrl+C to stop                                    ║
║                                                            ║
╚═══════════════════════════════════════════════════════════╝
    `);
});
